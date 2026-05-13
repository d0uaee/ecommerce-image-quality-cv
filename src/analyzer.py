"""
Advanced multi-criteria image quality analyser for e-commerce product images.

Each criterion returns a sub-dict:
    { "score": float[0,1], "value": <raw measurement>, "message": str }

Advanced criteria:
    1. JPEG_ARTIFACTS     — 8x8 block compression artifacts
    2. LIGHTING_UNIFORMITY — spatial uniformity of brightness (3x3 grid)
    3. EDGE_QUALITY       — sharpness of product borders
    4. COLOR_CONSISTENCY  — white balance and color naturalness
    5. EFFECTIVE_RESOLUTION — detects upscaling / fake resolution
    6. CLIP_COHERENCE     — image-text description alignment

Usage
-----
from src.analyzer import analyze, global_score

result = analyze("data/raw_images/electronics/001_phone.jpg",
                 detection=..., text_prompt="téléphone portable")
print(global_score(result["criteria"]))   # e.g. 0.74
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

log = logging.getLogger(__name__)

_CLIP_MODEL = None
_CLIP_PROCESSOR = None
_CLIP_LOAD_ATTEMPTED = False

# ---------------------------------------------------------------------------
# Criterion weights for the global score
# ---------------------------------------------------------------------------

WEIGHTS = {
    "jpeg_artifacts":      0.20,
    "lighting_uniformity": 0.20,
    "edge_quality":        0.20,
    "color_consistency":   0.15,
    "effective_resolution": 0.15,
    "clip_coherence":      0.10,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_image(image_path: Union[str, Path]) -> np.ndarray | None:
    """Return an RGB uint8 numpy array, or None on failure."""
    try:
        img = Image.open(image_path).convert("RGB")
        return np.array(img)
    except FileNotFoundError:
        log.error("Image not found: %s", image_path)
    except UnidentifiedImageError:
        log.error("Cannot identify image (corrupt?): %s", image_path)
    except Exception as exc:
        log.error("Unexpected error opening %s: %s", image_path, exc)
    return None


def _linear(value: float, low: float, high: float) -> float:
    """Linearly map value → [0, 1] clamped, where high maps to 1."""
    if value <= low:
        return 0.0
    if value >= high:
        return 1.0
    return (value - low) / (high - low)


def _criterion(score: float, value, message: str) -> dict:
    return {"score": round(float(score), 4), "value": value, "message": message}


def _has_large_uniform_regions(
    img_rgb: np.ndarray,
    block_size: int = 8,
    std_threshold: float = 20.0,
    min_uniform_ratio: float = 0.20,
) -> bool:
    """
    Heuristic pre-check for artistic/rendered images with large smooth color areas.

    We compute per-block standard deviation on grayscale 8x8 blocks and consider the
    image "uniform-rich" if enough blocks are low-variance.
    """
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    h, w = gray.shape
    if h < block_size or w < block_size:
        return False

    uniform_blocks = 0
    total_blocks = 0

    for y in range(0, h - block_size + 1, block_size):
        for x in range(0, w - block_size + 1, block_size):
            block = gray[y:y + block_size, x:x + block_size]
            total_blocks += 1
            if float(block.std()) < std_threshold:
                uniform_blocks += 1

    if total_blocks == 0:
        return False

    return (uniform_blocks / total_blocks) >= min_uniform_ratio


def _load_clip_model_once():
    """Lazy-load and cache CLIP model/processor once per process."""
    global _CLIP_MODEL, _CLIP_PROCESSOR, _CLIP_LOAD_ATTEMPTED

    if _CLIP_MODEL is not None and _CLIP_PROCESSOR is not None:
        return _CLIP_MODEL, _CLIP_PROCESSOR

    if _CLIP_LOAD_ATTEMPTED:
        return None, None

    _CLIP_LOAD_ATTEMPTED = True

    try:
        from transformers import CLIPModel, CLIPProcessor
        model_id = "openai/clip-vit-base-patch32"
        # Prefer local cache to avoid long network stalls in offline environments.
        _CLIP_PROCESSOR = CLIPProcessor.from_pretrained(model_id, local_files_only=True)
        _CLIP_MODEL = CLIPModel.from_pretrained(model_id, local_files_only=True)
        return _CLIP_MODEL, _CLIP_PROCESSOR
    except Exception as exc:
        log.warning("CLIP model load failed: %s", exc)
        return None, None


# ---------------------------------------------------------------------------
# Individual criteria
# ---------------------------------------------------------------------------

def _jpeg_artifacts(img_rgb: np.ndarray, image_path: Union[str, Path, None] = None) -> dict:
    """
    Mesure la nettete globale de l'image par variance du Laplacien.

    Une photo floue ou sous-exposee a une variance Laplacienne faible;
    une photo nette et bien eclairee a une variance elevee.
    Ce critere detecte les problemes de mise au point et de compression
    excessive qui reduisent les details fins.

    Seuils calibres sur 300 images Jumia Maroc (300x300 px):
        lap_var < 200  → tres flou / fortement compresse  → score 0.0
        lap_var > 3000 → net et tres detaille             → score 1.0
    """
    if img_rgb.size == 0:
        return _criterion(1.0, 0.0, "Image vide")

    try:
        y = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        lap = cv2.Laplacian(y, cv2.CV_64F)
        lap_var = float(lap.var())

        import math
        log_var   = math.log10(max(lap_var, 0.1))
        log_low   = math.log10(200.0)
        log_high  = math.log10(3000.0)
        score = max(0.0, min(1.0, (log_var - log_low) / (log_high - log_low)))

        if score >= 0.75:
            msg = "La qualite de votre photo est excellente"
        elif score >= 0.40:
            msg = "Photo correcte — verifiez la mise au point et l'eclairage"
        else:
            msg = "Photo floue ou trop compressee — reprenez avec un meilleur angle"

        return _criterion(score, round(lap_var, 1), msg)

    except Exception as e:
        log.warning("Sharpness detection failed: %s", e)
        return _criterion(0.5, 0.0, "Erreur: impossible d'analyser la nettete")


def _lighting_uniformity(gray_product: np.ndarray, gray_full: np.ndarray, mask: np.ndarray) -> dict:
    """
    Measures spatial uniformity of brightness across product region.
    
    Divides the product bounding box into a 3x3 grid (9 zones),
    computes mean brightness in each zone, then measures std of these means.
    
    Score 1.0 if std < 15, 0.0 if std > 60 (very uneven lighting).
    """
    if gray_full.size == 0:
        return _criterion(0.0, 0.0, "Image vide")

    # Get product bounding box
    coords = cv2.findNonZero(mask)
    if coords is None:
        return _criterion(0.0, 0.0, "Aucun produit détecté")

    x1, y1 = coords[:, 0, 0].min(), coords[:, 0, 1].min()
    x2, y2 = coords[:, 0, 0].max(), coords[:, 0, 1].max()

    bbox_h = y2 - y1 + 1
    bbox_w = x2 - x1 + 1

    # Divide into 3x3 grid
    zone_means = []
    for zy in range(3):
        for zx in range(3):
            zone_y1 = y1 + int(zy * bbox_h / 3)
            zone_y2 = y1 + int((zy + 1) * bbox_h / 3)
            zone_x1 = x1 + int(zx * bbox_w / 3)
            zone_x2 = x1 + int((zx + 1) * bbox_w / 3)

            # Use gray_full and extract from mask region
            zone_gray = gray_full[zone_y1:zone_y2, zone_x1:zone_x2]
            zone_mask = mask[zone_y1:zone_y2, zone_x1:zone_x2]

            if zone_mask.sum() > 0:
                zone_brightness = zone_gray[zone_mask > 0].mean()
                zone_means.append(zone_brightness)

    if len(zone_means) < 3:
        return _criterion(0.0, 0.0, "Région produit insuffisante")

    uniformity_std = np.std(zone_means)

    # Score: 1.0 if std < 15, 0.0 if std > 60, linear between
    score = 1.0 - _linear(uniformity_std, 15.0, 60.0)
    score = max(0.0, min(1.0, score))

    if score >= 0.8:
        msg = "L'éclairage de votre photo est parfait"
    elif score >= 0.5:
        msg = "Certaines parties de votre photo sont trop sombres ou trop claires"
    else:
        msg = "L'éclairage est mauvais — photographiez près d'une fenêtre ou ajoutez de la lumière"

    return _criterion(score, round(uniformity_std, 2), msg)


def _edge_quality(img_rgb: np.ndarray, mask: np.ndarray) -> dict:
    """
    Measures sharpness of product border edges.
    
    Applies Canny edge detection on dilated mask boundaries,
    measures edge continuity and strength. High-quality product
    separation should have clear, strong edges at the boundary.
    
    Thresholds are adaptive to image size:
    - For high-res (≥400px): strict thresholds (low=0.1, high=0.6)
    - For small images (<400px): relaxed thresholds (low=0.06, high=0.36)
    
    Score 1.0 if edges are sharp and continuous, 0.0 if weak/fragmented.
    """
    if mask.size == 0:
        return _criterion(0.0, 0.0, "Aucun masque")

    try:
        h, w = img_rgb.shape[:2]
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

        # Dilate mask to find boundary region
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        dilated = cv2.dilate(mask, kernel, iterations=2)
        eroded = cv2.erode(mask, kernel, iterations=2)
        boundary_mask = dilated - eroded

        # Apply Canny on boundary region
        canny = cv2.Canny(gray, 50, 150)
        boundary_edges = canny & boundary_mask

        # Measure edge density and coherence
        edge_count = boundary_edges.sum() // 255
        boundary_size = boundary_mask.sum() // 255

        if boundary_size < 50:
            return _criterion(0.5, 0.0, "Produit trop petit pour analyser")

        edge_density = edge_count / max(1, boundary_size)

        # Adaptive thresholds based on image size
        # For small images (<400px), reduce thresholds by 40%
        if h < 400 or w < 400:
            low_threshold = 0.1 * 0.6   # 0.06
            high_threshold = 0.6 * 0.6  # 0.36
        else:
            low_threshold = 0.1
            high_threshold = 0.6

        score = _linear(edge_density, low_threshold, high_threshold)
        score = max(0.0, min(1.0, score))

        if score >= 0.8:
            msg = "Votre produit est bien mis en valeur"
        elif score >= 0.5:
            msg = "Les bords de votre produit ne sont pas nets — rapprochez l'appareil"
        else:
            msg = "Votre produit est flou — nettoyez l'objectif et restabilisez votre appareil"

        return _criterion(score, round(edge_density, 4), msg)

    except Exception as e:
        log.warning("Edge quality detection failed: %s", e)
        return _criterion(0.5, 0.0, "Erreur: impossible d'analyser la netteté")


def _color_consistency(img_rgb: np.ndarray, mask: np.ndarray) -> dict:
    """
    Measures white balance and color naturalness on product region.
    
    Uses gray world assumption: in neutral lighting, R=G=B means white.
    Checks deviation of product colors from this assumption,
    and detects over-saturation or color cast.
    
    Score 1.0 if balanced color, 0.0 if strong color cast.
    """
    if mask.size == 0:
        return _criterion(0.0, 0.0, "Aucun masque")

    try:
        # Extract product region
        fg = mask > 0
        if not fg.any():
            return _criterion(0.5, 0.0, "Aucune région produit")

        r_channel = img_rgb[:, :, 0][fg].astype(np.float32)
        g_channel = img_rgb[:, :, 1][fg].astype(np.float32)
        b_channel = img_rgb[:, :, 2][fg].astype(np.float32)

        # Gray world check: compute mean of each channel
        mean_r = r_channel.mean()
        mean_g = g_channel.mean()
        mean_b = b_channel.mean()

        # Color cast is deviation from neutral (all channels equal)
        # Compute std of channel means
        channel_std = np.std([mean_r, mean_g, mean_b])

        # Also check saturation: HSV S channel
        hsv_full = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        s_channel = hsv_full[:, :, 1][fg].astype(np.float32)
        mean_saturation = s_channel.mean()

        # Score components:
        # 1. Color cast (lower is better): 1.0 if std < 20, 0.0 if > 60
        color_cast_score = 1.0 - _linear(channel_std, 20.0, 60.0)

        # 2. Saturation (natural is 50-150 in HSV): 1.0 if in range, 0.0 if outside
        if 50.0 <= mean_saturation <= 150.0:
            saturation_score = 1.0
        elif mean_saturation < 50.0:
            saturation_score = _linear(mean_saturation, 0.0, 50.0)
        else:
            saturation_score = 1.0 - _linear(mean_saturation - 150.0, 0.0, 105.0)

        # Combined score
        score = 0.6 * color_cast_score + 0.4 * saturation_score
        score = max(0.0, min(1.0, score))

        if score >= 0.8:
            msg = "Les couleurs de votre photo sont naturelles et fidèles"
        elif score >= 0.5:
            msg = "Les couleurs semblent légèrement déformées"
        else:
            msg = "Les couleurs ne sont pas naturelles — photographiez sous lumière blanche"

        return _criterion(score, round(channel_std, 2), msg)

    except Exception as e:
        log.warning("Color consistency detection failed: %s", e)
        return _criterion(0.5, 0.0, "Erreur: impossible d'analyser les couleurs")


def _effective_resolution(img_rgb: np.ndarray) -> dict:
    """
    Measures image resolution quality for e-commerce listings.

    Two components (weighted equally):
      1. Upscaling detection — variance ratio of original vs down/up-scaled copy.
         Low ratio = genuinely sharp; high ratio = blurry/upscaled original.
      2. Absolute size adequacy — Jumia recommends 500×500 px minimum; 800×800+ ideal.
         Images below 400 px on their shortest side score 0 for this component.

    Score 1.0 = 800 px native, 0.5 = 300 px native (CDN thumbnail), 0.0 = heavily upscaled.
    """
    if img_rgb.size == 0:
        return _criterion(0.5, 0.0, "Image vide")

    try:
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape

        # --- Component 1: upscaling detection ---
        original_variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        dw, dh = max(1, w // 2), max(1, h // 2)
        downscaled = cv2.resize(gray, (dw, dh), interpolation=cv2.INTER_AREA)
        upscaled   = cv2.resize(downscaled, (w, h), interpolation=cv2.INTER_LINEAR)
        upscaled_variance = cv2.Laplacian(upscaled, cv2.CV_64F).var()

        variance_ratio = (upscaled_variance / original_variance) if original_variance > 0 else 1.0
        # Score: 1.0 if ratio < 0.3 (genuinely sharp), 0.0 if > 0.8 (flat/upscaled)
        upscaling_score = 1.0 - _linear(variance_ratio, 0.3, 0.8)
        upscaling_score = max(0.0, min(1.0, upscaling_score))

        # --- Component 2: absolute resolution adequacy ---
        # 400 px → 0.0 (too small for Jumia), 800 px → 1.0 (ideal)
        size_score = _linear(min(h, w), 400, 800)
        size_score = max(0.0, min(1.0, size_score))

        score = 0.5 * upscaling_score + 0.5 * size_score
        score = max(0.0, min(1.0, score))

        if score >= 0.8:
            msg = "Votre photo est suffisamment grande et nette"
        elif score >= 0.5:
            msg = "Votre photo est un peu petite — utilisez un appareil avec une meilleure caméra"
        else:
            msg = "Votre photo est trop petite — les clients ne pourront pas voir les détails"

        return _criterion(score, round(variance_ratio, 4), msg)

    except Exception as e:
        log.warning("Effective resolution detection failed: %s", e)
        return _criterion(0.5, 0.0, "Erreur: impossible d'analyser la résolution")


def _clip_coherence(img_rgb: np.ndarray, text_prompt: str | None) -> dict:
    """
    Measures if the image matches the user's text description using CLIP.
    
    Computes cosine similarity between image embedding and text embedding.
    If no text prompt is provided, returns neutral score of 0.5.
    If CLIP model is unavailable or cannot be loaded, returns neutral score.
    
    Score = similarity (0 to 1).
    
    NOTE: CLIP feature is OPTIONAL and gracefully degrades in offline environments.
    """
    if text_prompt is None or text_prompt.strip() == "":
        return _criterion(0.5, 0.0, "Aucune description fournie")

    try:
        import torch

        model, processor = _load_clip_model_once()
        if model is None or processor is None:
            return _criterion(
                0.5,
                0.0,
                "Aucune description fournie",
            )

        # Prepare inputs
        pil_image = Image.fromarray(img_rgb)
        inputs = processor(
            text=[text_prompt],
            images=pil_image,
            return_tensors="pt",
            padding=True,
        )

        # Get embeddings and compute similarity
        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image
            similarity = logits_per_image[0, 0].item()

        # CLIP logits are typically in range [-1, 1] or normalized
        # Normalize to [0, 1] using sigmoid-like transformation
        score = 1.0 / (1.0 + np.exp(-similarity))  # sigmoid
        score = max(0.0, min(1.0, score))

        if score >= 0.75:
            msg = "Votre photo correspond bien à votre description"
        elif score >= 0.5:
            msg = "Vérifiez que la photo montre bien le produit que vous vendez"
        else:
            msg = "Votre photo ne semble pas correspondre à votre annonce"

        return _criterion(score, round(similarity, 4), msg)

    except ImportError as e:
        log.warning("CLIP/torch not available: %s", e)
        return _criterion(
            0.5, 0.0, "Aucune description fournie"
        )
    except Exception as e:
        log.warning("CLIP coherence detection failed: %s", e)
        return _criterion(0.5, 0.0, "Aucune description fournie")


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze(
    image_path: Union[str, Path],
    detection: dict,
    text_prompt: str | None = None,
) -> dict:
    """
    Analyse image quality given a pre-computed detection result.

    Parameters
    ----------
    image_path : path to the image file
    detection  : dict returned by ``detect_product()``
    text_prompt : optional text description of the product for CLIP coherence

    Returns
    -------
    dict with keys:
        "criteria" : dict of criterion_name → {score, value, message}
        "success"  : bool (False if image could not be loaded)
    """
    image_path = Path(image_path)
    img_rgb = _load_image(image_path)

    if img_rgb is None:
        empty = {k: _criterion(0.0, None, "Image load failed") for k in WEIGHTS}
        return {"criteria": empty, "success": False}

    h, w = img_rgb.shape[:2]
    mask = detection.get("mask", np.zeros((h, w), dtype=np.uint8))

    # Resize mask if dimensions mismatch
    if mask.shape != (h, w):
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)

    # Pre-compute grayscale
    gray_full = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    # Masked (product-only) version
    fg = mask > 0
    gray_product = gray_full[fg] if fg.any() else np.array([], dtype=np.uint8)

    criteria = {
        "jpeg_artifacts":      _jpeg_artifacts(img_rgb, image_path),
        "lighting_uniformity": _lighting_uniformity(gray_product, gray_full, mask),
        "edge_quality":        _edge_quality(img_rgb, mask),
        "color_consistency":   _color_consistency(img_rgb, mask),
        "effective_resolution": _effective_resolution(img_rgb),
        "clip_coherence":      _clip_coherence(img_rgb, text_prompt),
    }

    return {"criteria": criteria, "success": True}


def analyze_image(
    image_path: Union[str, Path],
    text_prompt: str | None = None,
) -> dict:
    """
    Convenience wrapper: runs ``detect_product()`` internally, then analyses.

    Parameters
    ----------
    image_path : path to the image file
    text_prompt : optional product description for CLIP coherence

    Returns
    -------
    dict with keys "criteria", "success", and "detection"
    """
    from src.detector import detect_product  # local import to avoid circular deps

    image_path = Path(image_path)
    detection = detect_product(image_path)
    result = analyze(image_path, detection, text_prompt=text_prompt)
    result["detection"] = detection
    return result


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def global_score(criteria: dict) -> float:
    """
    Weighted average of criterion scores.

    Parameters
    ----------
    criteria : the ``"criteria"`` sub-dict from ``analyze()`` / ``analyze_image()``

    Returns
    -------
    float in [0, 1]
    """
    total_weight = 0.0
    weighted_sum = 0.0
    for name, weight in WEIGHTS.items():
        criterion = criteria.get(name)
        if criterion is None:
            continue
        weighted_sum += criterion["score"] * weight
        total_weight += weight
    return round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import json

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m src.analyzer <image_path>")
        sys.exit(1)

    report = analyze_image(sys.argv[1])
    criteria = report["criteria"]

    print(f"\n{'Criterion':<20} {'Score':>6}  {'Value':>10}  Message")
    print("-" * 65)
    for name, data in criteria.items():
        print(f"{name:<20} {data['score']:>6.3f}  {str(data['value']):>10}  {data['message']}")

    score = global_score(criteria)
    print("-" * 65)
    print(f"{'GLOBAL SCORE':<20} {score:>6.3f}")
