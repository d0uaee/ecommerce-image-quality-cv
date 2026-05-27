from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image

import src.text_processor as tp
from config import PROXY_WEIGHTS, SELECTOR_WEIGHTS
from src.candidate_region_generator import refine_crop
from src.dictionaries import CATEGORY_KEYWORDS, EMBEDDING_VECTOR_SIZE, FRENCH_COLOR_TO_RGB


MAX_CROPS = 5
CLIP_INPUT_SIZE = (224, 224)


def _load_image(image: str | Path | np.ndarray) -> np.ndarray:
    if isinstance(image, np.ndarray):
        array = image.copy()
    else:
        array = cv2.imread(str(image), cv2.IMREAD_COLOR)
        if array is None:
            raise FileNotFoundError(f"Impossible de lire l'image: {image}")

    if array.ndim == 2:
        array = cv2.cvtColor(array, cv2.COLOR_GRAY2BGR)
    return array.astype(np.uint8)


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=np.float32).reshape(-1)
    right = np.asarray(right, dtype=np.float32).reshape(-1)
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    cosine = float(np.dot(left, right) / (left_norm * right_norm))
    return max(0.0, min(1.0, (cosine + 1.0) / 2.0))


def _resize_for_clip(crop_bgr: np.ndarray) -> Image.Image:
    rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb)
    return pil_image.resize(CLIP_INPUT_SIZE)


def _category_coherence(text_category: str | None, crop_bgr: np.ndarray) -> float:
    """
    Estime si le crop est visuellement cohérent avec la catégorie textuelle.

    Heuristiques visuelles légères (rapport d'aspect + densité de contours) :
    - portable_electronics : objets plutôt carrés/portrait, contours nets
    - shoes               : objets nettement plus larges que hauts
    - clothing            : plage de ratios large — on vérifie seulement l'absence
                            de ratios extrêmes et une densité minimale de contours.

    Choix de conception :
    L'ancienne version testait `any(kw in CATEGORY_KEYWORDS["clothing"] for kw in …)`,
    ce qui est toujours True puisque la liste contient par définition ces mots-clés.
    Le bug masquait l'absence de signal visuel réel. On préfère un score honnête :
    0.5 (neutre) si l'heuristique visuelle ne peut pas trancher, plutôt qu'un faux 1.0.
    """
    if not text_category:
        return 0.5

    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    mean_edge = float(np.mean(np.abs(cv2.Laplacian(gray, cv2.CV_32F))))
    aspect_ratio = crop_bgr.shape[1] / max(crop_bgr.shape[0], 1)

    if text_category == "portable_electronics":
        # Téléphones/tablettes/casques : ratio approximativement carré ou portrait,
        # contours nets (écrans, coques) → seuil d'arête plus élevé.
        return 1.0 if (0.65 <= aspect_ratio <= 1.85 and mean_edge > 8.0) else 0.5

    if text_category == "shoes":
        # Chaussures photographiées de côté ou en 3/4 : nettement plus larges que hautes.
        return 1.0 if (1.1 <= aspect_ratio <= 3.2 and mean_edge > 6.0) else 0.5

    if text_category == "clothing":
        # Les vêtements couvrent une large plage de ratios (t-shirt portrait vs veste
        # 3/4 paysage). Sans détecteur de forme dédié, on ne peut pas distinguer un
        # vêtement d'un fond non-vêtement sur le seul ratio. On accepte tout crop dont
        # le ratio reste dans des bornes non-absurdes et qui présente des contours
        # minimaux (évite les crops de fond uni).
        if 0.35 <= aspect_ratio <= 2.0 and mean_edge > 4.0:
            return 1.0
        # Ratio extrême ou crop quasi-uniforme → signal insuffisant, score neutre.
        return 0.5

    # Catégorie inconnue : score neutre.
    return 0.5


def _mean_color_name(crop_bgr: np.ndarray) -> str | None:
    if crop_bgr.size == 0:
        return None
    rgb_mean = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB).mean(axis=(0, 1))
    best_name = None
    best_distance = float("inf")
    for name, rgb in FRENCH_COLOR_TO_RGB.items():
        distance = float(np.linalg.norm(rgb_mean - np.array(rgb, dtype=np.float32)))
        if distance < best_distance:
            best_name = name
            best_distance = distance
    return best_name


def _proxy_clip_score(crop_bgr: np.ndarray, text_data: dict[str, Any], area: float, centrality: float) -> tuple[float, dict[str, float]]:
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    detail_signal = float(np.mean(np.abs(cv2.Laplacian(gray, cv2.CV_32F))) / 32.0)
    detail_signal = max(0.0, min(1.0, detail_signal))

    text_color = text_data.get("color")
    crop_color = _mean_color_name(crop_bgr)
    color_signal = 1.0 if text_color and crop_color == text_color else 0.5

    size_signal = max(0.0, min(1.0, area))
    clip_proxy = (
        PROXY_WEIGHTS["detail"] * detail_signal
        + PROXY_WEIGHTS["center"] * (0.5 * centrality + 0.5 * size_signal)
        + PROXY_WEIGHTS["color"] * color_signal
    )
    return clip_proxy, {
        "detail_signal": round(detail_signal, 4),
        "proxy_color_signal": round(color_signal, 4),
        "proxy_size_signal": round(size_signal, 4),
    }


@lru_cache(maxsize=1)
def _clip_image_encoder_ready() -> bool:
    model = tp._load_embedding_model()
    return tp._embed_backend == "clip" and model is not None


def _encode_crop_embedding(crop_bgr: np.ndarray) -> np.ndarray:
    if not _clip_image_encoder_ready():
        return np.zeros(EMBEDDING_VECTOR_SIZE, dtype=np.float32)

    model = tp._load_embedding_model()
    if model is None:
        return np.zeros(EMBEDDING_VECTOR_SIZE, dtype=np.float32)

    try:
        pil_image = _resize_for_clip(crop_bgr)
        vector = model.encode([pil_image], convert_to_numpy=True, normalize_embeddings=True)
    except Exception:
        return np.zeros(EMBEDDING_VECTOR_SIZE, dtype=np.float32)

    array = np.asarray(vector, dtype=np.float32).reshape(-1)
    if array.size == EMBEDDING_VECTOR_SIZE:
        return array
    if array.size > EMBEDDING_VECTOR_SIZE:
        return array[:EMBEDDING_VECTOR_SIZE]

    padded = np.zeros(EMBEDDING_VECTOR_SIZE, dtype=np.float32)
    padded[: array.size] = array
    return padded


def _prepare_candidates(candidate_boxes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_boxes = sorted(
        candidate_boxes,
        key=lambda item: (item.get("area", 0.0), item.get("centrality", 0.0)),
        reverse=True,
    )
    return sorted_boxes[:MAX_CROPS]


def select_product(
    image: str | Path | np.ndarray,
    candidate_boxes: list[dict[str, Any]],
    text_data: dict[str, Any],
) -> dict[str, Any]:
    image_bgr = _load_image(image)
    candidates = _prepare_candidates(candidate_boxes)

    text_embedding = np.asarray(
        text_data.get("text_embedding", np.zeros(EMBEDDING_VECTOR_SIZE, dtype=np.float32)),
        dtype=np.float32,
    ).reshape(-1)

    selection_details: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        x1, y1, x2, y2 = candidate["bbox"]
        crop = image_bgr[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        area = float(candidate.get("area", 0.0))
        centrality = float(candidate.get("centrality", 0.0))
        score_visual = max(0.0, min(1.0, area * centrality))
        score_cat = _category_coherence(text_data.get("category"), crop)

        if tp._embed_backend != "clip":
            score_clip, proxy_details = _proxy_clip_score(crop, text_data, area, centrality)
            clip_backend = "proxy"
            image_embedding = np.zeros(EMBEDDING_VECTOR_SIZE, dtype=np.float32)
        else:
            image_embedding = _encode_crop_embedding(crop)
            score_clip = _cosine_similarity(image_embedding, text_embedding)
            proxy_details = {}
            clip_backend = "clip" if np.linalg.norm(image_embedding) > 0 else "proxy"
            if clip_backend == "proxy":
                score_clip, proxy_details = _proxy_clip_score(crop, text_data, area, centrality)

        final_score = (
            SELECTOR_WEIGHTS["clip_text_similarity"] * score_clip
            + SELECTOR_WEIGHTS["size_centrality"] * score_visual
            + SELECTOR_WEIGHTS["category_coherence"] * score_cat
        )

        selection_details.append(
            {
                "candidate_rank": index + 1,
                "bbox": candidate["bbox"],
                "area": round(area, 4),
                "centrality": round(centrality, 4),
                "score_clip": round(score_clip, 4),
                "score_visual": round(score_visual, 4),
                "score_category": round(score_cat, 4),
                "score_total": round(final_score, 4),
                "clip_backend": clip_backend,
                "proxy_details": proxy_details,
            }
        )

    if not selection_details:
        raise ValueError("Aucune région candidate exploitable pour la sélection.")

    selection_details.sort(key=lambda item: item["score_total"], reverse=True)
    winner = selection_details[0]
    refined = refine_crop(image_bgr, tuple(winner["bbox"]))

    return {
        "selected_bbox": winner["bbox"],
        "refined_bbox": refined["bbox"],
        "selected_crop": refined["crop"],
        "selected_mask": refined["mask"],
        "selected_score": winner["score_total"],
        "candidates": selection_details,
        "calibration_note": "Poids du selector issus d'une calibration empirique sur le pipeline zero-shot.",
    }
