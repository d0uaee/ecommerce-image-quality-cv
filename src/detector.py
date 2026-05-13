"""
Product detector — segments the main product in an e-commerce image.

Primary method : Grounding DINO (zero-shot, text-prompted) via HuggingFace
                 Transformers.  A text prompt describing the product is used
                 to locate the bounding box; GrabCut then refines the mask
                 inside that box.
Fallback method: grayscale Otsu threshold + largest connected component for
                 images on plain white/light backgrounds when DINO finds
                 nothing useful, or when no text prompt is provided.

Usage
-----
from src.detector import detect_product, visualize_detection

# With a text prompt (recommended)
result = detect_product("data/raw_images/electronics/001.jpg",
                        text_prompt="téléphone portable")

# Without a prompt → goes straight to background subtraction
result = detect_product("data/raw_images/electronics/001.jpg")

# result = {
#   "mask":       np.ndarray (H×W, uint8, 0 or 255),
#   "bbox":       [x1, y1, x2, y2],
#   "confidence": 0.87,
#   "label":      "téléphone portable",
#   "success":    True,
#   "method":     "grounding_dino",   # or "fallback"
# }

visualize_detection("data/raw_images/electronics/001.jpg", "output/vis.jpg")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Grounding DINO constants
# ---------------------------------------------------------------------------

GDINO_MODEL_ID  = "IDEA-Research/grounding-dino-tiny"
BOX_THRESHOLD   = 0.35
TEXT_THRESHOLD  = 0.25

# ---------------------------------------------------------------------------
# Grounding DINO — lazy-loaded so importing this module doesn't force a
# network download or a transformers import at startup.
# ---------------------------------------------------------------------------

_gdino_processor = None
_gdino_model     = None


def _get_gdino_model():
    """
    Load (and cache) the Grounding DINO processor and model.
    Returns (processor, model) or raises RuntimeError if unavailable.
    """
    global _gdino_processor, _gdino_model
    if _gdino_processor is None or _gdino_model is None:
        try:
            from transformers import (  # noqa: PLC0415
                AutoModelForZeroShotObjectDetection,
                AutoProcessor,
            )
            log.info("Loading Grounding DINO (%s) …", GDINO_MODEL_ID)
            _gdino_processor = AutoProcessor.from_pretrained(GDINO_MODEL_ID)
            _gdino_model = AutoModelForZeroShotObjectDetection.from_pretrained(
                GDINO_MODEL_ID
            )
            _gdino_model.eval()
            log.info("Grounding DINO loaded.")
        except ImportError as exc:
            raise RuntimeError(
                "transformers / torch not installed. "
                "Run: pip install transformers torch"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load Grounding DINO model: {exc}"
            ) from exc
    return _gdino_processor, _gdino_model


def _normalise_prompt(text: str) -> str:
    """
    Grounding DINO expects lowercase text ending with a period.
    e.g. "Téléphone Samsung" → "téléphone samsung."
    """
    text = text.strip().lower()
    if not text.endswith("."):
        text += "."
    return text


# ---------------------------------------------------------------------------
# Public result helpers
# ---------------------------------------------------------------------------

def _empty_result(h: int, w: int, method: str = "fallback") -> dict:
    return {
        "mask":       np.zeros((h, w), dtype=np.uint8),
        "bbox":       [0, 0, w, h],
        "confidence": 0.0,
        "label":      "",
        "success":    False,
        "method":     method,
    }


# ---------------------------------------------------------------------------
# Fallback: background subtraction for light/white backgrounds
# (unchanged from previous version)
# ---------------------------------------------------------------------------

def _fallback_bg_subtraction(gray: np.ndarray) -> np.ndarray:
    """
    Return a binary mask (0/255) isolating the foreground on a
    white or light-coloured background.

    Strategy
    --------
    1. Otsu threshold to find the dark foreground.
    2. Morphological close + open to clean up noise.
    3. Keep only the largest connected component.
    """
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN,  kernel, iterations=1)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(opened, connectivity=8)
    if num_labels < 2:
        return opened

    fg_stats    = stats[1:]
    largest_idx = int(np.argmax(fg_stats[:, cv2.CC_STAT_AREA])) + 1
    mask        = np.where(labels == largest_idx, np.uint8(255), np.uint8(0))
    return mask


def _bbox_from_mask(mask: np.ndarray) -> list[int]:
    """Return [x1, y1, x2, y2] tight bounding box of non-zero pixels."""
    coords = cv2.findNonZero(mask)
    if coords is None:
        h, w = mask.shape
        return [0, 0, w, h]
    x, y, bw, bh = cv2.boundingRect(coords)
    return [x, y, x + bw, y + bh]


# ---------------------------------------------------------------------------
# GrabCut mask refinement inside a bounding box
# (unchanged from previous version — now initialised from DINO box)
# ---------------------------------------------------------------------------

def _refine_mask_from_box(image_bgr: np.ndarray, bbox: list[int]) -> np.ndarray:
    """
    Refine a coarse detection box into a tighter foreground mask using GrabCut.

    The DINO bounding box is kept as the initialization signal:
    1. Mark everything outside the box as definite background.
    2. Run GrabCut with a slightly inset rectangle so the box edges do not
       force the entire rectangle to become foreground.
    3. Clean the binary result with morphology and keep the largest component.

    If refinement fails, fall back to the original box mask.
    """
    h, w = image_bgr.shape[:2]
    x1, y1, x2, y2 = bbox

    fallback_mask = np.zeros((h, w), dtype=np.uint8)
    fallback_mask[y1:y2, x1:x2] = 255

    if x2 <= x1 or y2 <= y1:
        return fallback_mask

    box_w = x2 - x1
    box_h = y2 - y1
    if box_w < 8 or box_h < 8:
        return fallback_mask

    # Start from "probable background" everywhere, then use the detection box
    # as the only region allowed to contain foreground.
    grabcut_mask = np.full((h, w), cv2.GC_BGD, dtype=np.uint8)
    grabcut_mask[y1:y2, x1:x2] = cv2.GC_PR_FGD

    # Inset the rectangle slightly so GrabCut can separate object edges from
    # the background instead of treating the whole box as foreground.
    inset_x = max(1, int(box_w * 0.03))
    inset_y = max(1, int(box_h * 0.03))
    rect_x1 = min(max(x1 + inset_x, 0), w - 1)
    rect_y1 = min(max(y1 + inset_y, 0), h - 1)
    rect_x2 = max(rect_x1 + 1, min(x2 - inset_x, w))
    rect_y2 = max(rect_y1 + 1, min(y2 - inset_y, h))
    rect    = (rect_x1, rect_y1, rect_x2 - rect_x1, rect_y2 - rect_y1)

    bg_model = np.zeros((1, 65), np.float64)
    fg_model = np.zeros((1, 65), np.float64)

    try:
        cv2.grabCut(
            image_bgr,
            grabcut_mask,
            rect,
            bg_model,
            fg_model,
            5,
            cv2.GC_INIT_WITH_RECT,
        )
    except cv2.error as exc:
        log.debug("GrabCut refinement failed for bbox=%s: %s", bbox, exc)
        return fallback_mask

    refined = np.where(
        (grabcut_mask == cv2.GC_FGD) | (grabcut_mask == cv2.GC_PR_FGD),
        255,
        0,
    ).astype(np.uint8)

    # Restrict to the DINO region — the detection box is our search area.
    refined[:y1, :] = 0
    refined[y2:, :]  = 0
    refined[:, :x1]  = 0
    refined[:, x2:]  = 0

    kernel  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    refined = cv2.morphologyEx(refined, cv2.MORPH_OPEN,  kernel, iterations=1)
    refined = cv2.morphologyEx(refined, cv2.MORPH_CLOSE, kernel, iterations=2)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(refined, connectivity=8)
    if num_labels > 1:
        fg_stats    = stats[1:]
        largest_idx = int(np.argmax(fg_stats[:, cv2.CC_STAT_AREA])) + 1
        refined     = np.where(labels == largest_idx, 255, 0).astype(np.uint8)

    if cv2.countNonZero(refined) < 100:
        return fallback_mask

    return refined


# ---------------------------------------------------------------------------
# Core detection
# ---------------------------------------------------------------------------

def detect_product(
    image_path: Union[str, Path],
    text_prompt: str | None = None,
) -> dict:
    """
    Detect the main product in *image_path*.

    Parameters
    ----------
    image_path  : str or Path — path to the image file.
    text_prompt : str or None — natural-language description of the product
                  (e.g. "téléphone portable", "chaise en bois").
                  When None or empty the fallback background-subtraction is
                  used directly, without attempting Grounding DINO.

    Returns
    -------
    dict with keys:
        mask        : np.ndarray  H×W uint8 (0 or 255)
        bbox        : list[int]   [x1, y1, x2, y2]
        confidence  : float
        label       : str
        success     : bool
        method      : str         "grounding_dino" | "fallback"
    """
    image_path = Path(image_path)

    # --- 1. Load image ---------------------------------------------------
    try:
        pil_img = Image.open(image_path).convert("RGB")
    except FileNotFoundError:
        log.error("Image not found: %s", image_path)
        return _empty_result(100, 100)
    except UnidentifiedImageError:
        log.error("Cannot identify image (corrupt?): %s", image_path)
        return _empty_result(100, 100)
    except Exception as exc:
        log.error("Unexpected error opening %s: %s", image_path, exc)
        return _empty_result(100, 100)

    img_np = np.array(pil_img)        # H×W×3, uint8, RGB
    h, w   = img_np.shape[:2]
    bgr    = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # --- 2. Grounding DINO (only when a text prompt is provided) ----------
    if text_prompt and text_prompt.strip():
        prompt = _normalise_prompt(text_prompt)
        try:
            import torch  # noqa: PLC0415
            processor, model = _get_gdino_model()

            inputs = processor(
                images=pil_img,
                text=prompt,
                return_tensors="pt",
            )

            with torch.no_grad():
                outputs = model(**inputs)

            # post_process returns a list of dicts (one per image)
            # transformers ≥4.49 renamed box_threshold → threshold
            try:
                results = processor.post_process_grounded_object_detection(
                    outputs,
                    inputs.input_ids,
                    box_threshold=BOX_THRESHOLD,
                    text_threshold=TEXT_THRESHOLD,
                    target_sizes=[(h, w)],
                )[0]
            except TypeError:
                results = processor.post_process_grounded_object_detection(
                    outputs,
                    inputs.input_ids,
                    threshold=BOX_THRESHOLD,
                    text_threshold=TEXT_THRESHOLD,
                    target_sizes=[(h, w)],
                )[0]

            boxes  = results["boxes"].cpu().numpy()    # (N, 4) in xyxy pixels
            scores = results["scores"].cpu().numpy()   # (N,)
            labels = results.get("text_labels", results.get("labels", []))  # transformers ≥4.51 uses text_labels

            if len(scores) > 0:
                # Keep only the detection with the highest confidence score
                best_idx  = int(np.argmax(scores))
                best_conf = float(scores[best_idx])
                best_label = labels[best_idx] if best_idx < len(labels) else prompt.rstrip(".")

                x1, y1, x2, y2 = boxes[best_idx].tolist()
                best_box = [
                    max(0, int(x1)), max(0, int(y1)),
                    min(w, int(x2)), min(h, int(y2)),
                ]

                # --- 3. GrabCut refinement inside the DINO box -----------
                mask        = _refine_mask_from_box(bgr, best_box)
                refined_box = _bbox_from_mask(mask)

                log.debug(
                    "Grounding DINO: '%s' (%.2f) raw_box=%s refined_box=%s",
                    best_label, best_conf, best_box, refined_box,
                )
                return {
                    "mask":       mask,
                    "bbox":       refined_box,
                    "confidence": best_conf,
                    "label":      best_label,
                    "success":    True,
                    "method":     "grounding_dino",
                }

            log.debug(
                "Grounding DINO found no boxes above threshold for prompt '%s'", prompt
            )

        except RuntimeError as exc:
            # Model unavailable (not installed, download failed, etc.)
            log.warning("Grounding DINO unavailable (%s) — using fallback", exc)
        except Exception as exc:
            log.warning("Grounding DINO inference failed (%s) — using fallback", exc)

    elif text_prompt is not None:
        # Empty string provided — skip DINO silently
        log.debug("Empty text_prompt — skipping Grounding DINO, using fallback")
    else:
        # No prompt provided (called from analyzer.py / app.py without prompt)
        log.debug("No text_prompt — using fallback background subtraction")

    # --- 4. Fallback: background subtraction --------------------------------
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    mask = _fallback_bg_subtraction(gray)
    non_zero = cv2.countNonZero(mask)

    if non_zero < 100:
        log.debug("Fallback produced empty mask for %s", image_path)
        return _empty_result(h, w)

    bbox = _bbox_from_mask(mask)
    log.debug("Fallback bg-subtraction succeeded for %s", image_path)
    return {
        "mask":       mask,
        "bbox":       bbox,
        "confidence": 0.0,
        "label":      "unknown (fallback)",
        "success":    True,
        "method":     "fallback",
    }


# ---------------------------------------------------------------------------
# Visualisation (unchanged)
# ---------------------------------------------------------------------------

def visualize_detection(
    image_path: Union[str, Path],
    output_path: Union[str, Path],
    mask_color:     tuple[int, int, int] = (0, 255, 0),
    mask_alpha:     float                = 0.35,
    bbox_color:     tuple[int, int, int] = (0, 200, 0),
    bbox_thickness: int                  = 3,
    text_prompt:    str | None           = None,
) -> bool:
    """
    Save *image_path* annotated with the detection mask overlay and bbox.

    Parameters
    ----------
    image_path      : source image
    output_path     : where to write the annotated image (JPEG or PNG)
    mask_color      : BGR colour of the mask overlay
    mask_alpha      : opacity of the mask overlay (0–1)
    bbox_color      : BGR colour of the bounding-box rectangle
    bbox_thickness  : pixel width of the bbox line

    Returns
    -------
    True on success, False on any error.
    """
    image_path  = Path(image_path)
    output_path = Path(output_path)

    result = detect_product(image_path, text_prompt=text_prompt)

    try:
        pil_img = Image.open(image_path).convert("RGB")
    except Exception as exc:
        log.error("Cannot open image for visualisation (%s): %s", image_path, exc)
        return False

    bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]

    # --- Mask overlay ---
    mask = result["mask"]
    if mask.shape != (h, w):
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)

    overlay     = bgr.copy()
    color_layer = np.full_like(bgr, mask_color[::-1])   # BGR
    fg          = mask > 0
    overlay[fg] = cv2.addWeighted(bgr, 1 - mask_alpha, color_layer, mask_alpha, 0)[fg]

    # --- Bounding box ---
    x1, y1, x2, y2 = result["bbox"]
    cv2.rectangle(overlay, (x1, y1), (x2, y2), bbox_color[::-1], bbox_thickness)

    # --- Label text ---
    label_text = result["label"]
    method     = result.get("method", "")
    if result["success"] and result["confidence"] > 0:
        label_text += f"  {result['confidence']:.0%}"
    if method == "fallback":
        label_text = ""  # ne pas afficher "fallback" sur l'image
    if label_text:
        font        = cv2.FONT_HERSHEY_SIMPLEX
        font_scale  = max(0.5, min(1.2, w / 800))
        thickness   = max(1, bbox_thickness - 1)
        (tw, th), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)
        tx = max(x1, 0)
        ty = max(y1 - 8, th + 4)
        cv2.rectangle(
            overlay,
            (tx, ty - th - baseline - 2), (tx + tw + 4, ty + baseline),
            (0, 0, 0), -1,
        )
        cv2.putText(
            overlay, label_text, (tx + 2, ty),
            font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA,
        )

    # --- Save ---
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), overlay)
        log.info("Visualisation saved -> %s", output_path)
        return True
    except Exception as exc:
        log.error("Failed to save visualisation (%s): %s", output_path, exc)
        return False


# ---------------------------------------------------------------------------
# CLI convenience
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m src.detector <image_path> [text_prompt] [output_path]")
        sys.exit(1)

    src    = Path(sys.argv[1])
    prompt = sys.argv[2] if len(sys.argv) > 2 else None
    dest   = Path(sys.argv[3]) if len(sys.argv) > 3 else src.with_name(src.stem + "_detected.jpg")

    res = detect_product(src, text_prompt=prompt)
    print(f"success    : {res['success']}")
    print(f"method     : {res['method']}")
    print(f"label      : {res['label']}")
    print(f"confidence : {res['confidence']:.3f}")
    print(f"bbox       : {res['bbox']}")
    print(f"mask shape : {res['mask'].shape}  non-zero px: {cv2.countNonZero(res['mask'])}")

    if visualize_detection(src, dest):
        print(f"Visualisation -> {dest}")
