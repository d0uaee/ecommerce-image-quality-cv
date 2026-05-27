from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

import src.text_processor as tp
from config import ANALYZER_WEIGHTS, QUALITY_THRESHOLDS
from src.candidate_region_generator import propose_regions
from src.dictionaries import EMBEDDING_VECTOR_SIZE, FRENCH_COLOR_TO_RGB


ImageInput = str | Path | np.ndarray


ADVICE_TEMPLATES = {
    "sharpness": {
        "fr": "Image trop douce : stabilise le smartphone, refais la mise au point et evite le zoom numerique.",
        "darija": "Tsowira ma hiyach hada: chdd telephonk mzyan, dir focus mzyan, w b3ed mn zoom numerique.",
    },
    "exposure": {
        "fr": "Exposition a corriger : ajoute une lumiere douce ou eloigne le produit d'une source trop forte.",
        "darija": "Lidawa khas-ha tetslah: zid noor hani ola b3ed lproduit 3la noor qwi bzzaf.",
    },
    "contrast": {
        "fr": "Contraste faible : utilise un fond plus propre et separe mieux le produit de l'arriere-plan.",
        "darija": "Lcontrast da3if: sta3mel fond nqiy w khalli lproduit yban mzyan 3la l'arriere-plan.",
    },
    "color_balance": {
        "fr": "Legere dominante couleur : photographie pres d'une lumiere naturelle pour garder des couleurs fideles.",
        "darija": "Kayna dominante khfifa f lwan: swer qrib l'daw tabi3i bach ibqaw lwan s7i7in.",
    },
    "effective_resolution": {
        "fr": "Resolution effective limitee : evite les captures d'ecran et garde l'image originale en grande taille.",
        "darija": "Resolution ma kfayach: ma تستعملch screenshot w khlli tsowira l'asliya b taille kbira.",
    },
    "coherence": {
        "fr": "Coherence produit/texte a renforcer : garde un crop centre sur le bon produit et aligne mieux l'image avec l'annonce.",
        "darija": "Kayn khlat bin tswira w texte: khalli crop mrattez 3la nafs lproduit w waffe9 tswira m3a l'annonce.",
    },
}


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return float(max(low, min(high, value)))


def _linear_score(value: float, low: float, high: float) -> float:
    if high <= low:
        return 100.0
    return _clamp(100.0 * (value - low) / (high - low))


def _load_image(image_input: ImageInput) -> np.ndarray:
    if isinstance(image_input, np.ndarray):
        image = image_input.copy()
    else:
        image = cv2.imread(str(image_input), cv2.IMREAD_COLOR)
        if image is None:
            raise FileNotFoundError(f"Impossible de lire l'image: {image_input}")

    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("L'image doit avoir 3 canaux ou etre en niveaux de gris.")
    return image.astype(np.uint8)


def _criterion(name: str, score: float, raw_value: float | dict[str, float | str | None], message: str) -> dict[str, Any]:
    return {
        "name": name,
        "score": round(_clamp(score), 2),
        "raw_value": raw_value,
        "message_fr": message,
    }


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=np.float32).reshape(-1)
    right = np.asarray(right, dtype=np.float32).reshape(-1)
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    cosine = float(np.dot(left, right) / (left_norm * right_norm))
    return max(0.0, min(1.0, (cosine + 1.0) / 2.0))


def _closest_color_name(image_bgr: np.ndarray) -> str | None:
    if image_bgr.size == 0:
        return None
    rgb_mean = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB).mean(axis=(0, 1))
    best_name = None
    best_distance = float("inf")
    for name, rgb in FRENCH_COLOR_TO_RGB.items():
        distance = float(np.linalg.norm(rgb_mean - np.array(rgb, dtype=np.float32)))
        if distance < best_distance:
            best_name = name
            best_distance = distance
    return best_name


def _encode_image_embedding(image_bgr: np.ndarray) -> np.ndarray:
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    return tp.encode_image_embedding(rgb)


def _sharpness_score(gray: np.ndarray) -> dict[str, Any]:
    thresholds = QUALITY_THRESHOLDS["sharpness"]
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    score = _linear_score(lap_var, thresholds["very_blurry_max"], thresholds["excellent_min"])

    if lap_var < thresholds["very_blurry_max"]:
        message = "Nettete tres faible : la photo est franchement floue."
    elif lap_var < thresholds["soft_max"]:
        message = "Nettete limitee : le produit manque de details fins."
    elif lap_var < thresholds["good_min"]:
        message = "Nettete correcte : les details sont visibles mais encore perfectibles."
    else:
        message = "Bonne nettete : les contours et textures sont bien lisibles."

    return _criterion("sharpness", score, round(lap_var, 2), message)


def _exposure_score(gray: np.ndarray) -> dict[str, Any]:
    thresholds = QUALITY_THRESHOLDS["exposure"]
    mean_brightness = float(gray.mean())
    std_brightness = float(gray.std())
    p10 = float(np.percentile(gray, 10))
    p90 = float(np.percentile(gray, 90))
    shadow_ratio = float(np.mean(gray <= 35))
    highlight_ratio = float(np.mean(gray >= 245))
    target = thresholds["target_mean"]
    deviation = abs(mean_brightness - target)

    if mean_brightness <= thresholds["extreme_dark"] or mean_brightness >= thresholds["extreme_bright"]:
        score = 12.0
    elif deviation <= thresholds["tolerance_good"]:
        score = 100.0 - (deviation / max(thresholds["tolerance_good"], 1.0)) * 12.0
    elif deviation <= thresholds["tolerance_ok"]:
        score = 88.0 - (deviation - thresholds["tolerance_good"]) / (
            thresholds["tolerance_ok"] - thresholds["tolerance_good"]
        ) * 38.0
    else:
        score = max(18.0, 50.0 - (deviation - thresholds["tolerance_ok"]) * 1.1)

    if mean_brightness < target:
        darkness_penalty = max(0.0, (80.0 - p10) * 0.32) + shadow_ratio * 42.0
        score -= darkness_penalty
    else:
        highlight_penalty = max(0.0, (p90 - 235.0) * 0.40) + highlight_ratio * 38.0
        score -= highlight_penalty

    final_score = _clamp(score)

    if mean_brightness < thresholds["extreme_dark"]:
        message = "Sous-exposition forte : l'image est trop sombre."
    elif mean_brightness > thresholds["extreme_bright"]:
        message = "Surexposition forte : les hautes lumieres sont brulees."
    elif final_score < 45.0:
        message = "Exposition a corriger : l'image parait trop sombre ou desequilibree."
    elif deviation > thresholds["tolerance_ok"]:
        message = "Exposition moyenne : la lumiere n'est pas encore bien equilibree."
    else:
        message = "Exposition maitrisee : la luminosite globale est correcte."

    return _criterion(
        "exposure",
        score,
        {
            "mean_brightness": round(mean_brightness, 2),
            "std_brightness": round(std_brightness, 2),
            "p10": round(p10, 2),
            "p90": round(p90, 2),
            "shadow_ratio": round(shadow_ratio, 4),
            "highlight_ratio": round(highlight_ratio, 4),
        },
        message,
    )


def _contrast_score(gray: np.ndarray) -> dict[str, Any]:
    thresholds = QUALITY_THRESHOLDS["contrast"]
    std_value = float(gray.std())
    score = _linear_score(std_value, thresholds["flat_max"], thresholds["strong_min"])

    if std_value < thresholds["flat_max"]:
        message = "Contraste tres faible : l'image parait plate."
    elif std_value < thresholds["acceptable_min"]:
        message = "Contraste faible : le produit se detache mal."
    elif std_value < thresholds["good_min"]:
        message = "Contraste acceptable : la lecture visuelle reste correcte."
    else:
        message = "Bon contraste : le produit ressort bien."

    return _criterion("contrast", score, round(std_value, 2), message)


def _color_balance_score(image_bgr: np.ndarray) -> dict[str, Any]:
    thresholds = QUALITY_THRESHOLDS["color_balance"]
    channel_means = image_bgr.mean(axis=(0, 1)).astype(float)
    cast_delta = float(np.max(channel_means) - np.min(channel_means))

    if cast_delta <= thresholds["good_max_delta"]:
        score = 100.0
    elif cast_delta <= thresholds["acceptable_max_delta"]:
        score = 100.0 - (cast_delta - thresholds["good_max_delta"]) * 1.3
    elif cast_delta <= thresholds["strong_cast_delta"]:
        score = 84.0 - (cast_delta - thresholds["acceptable_max_delta"]) * 1.4
    else:
        score = max(45.0, 62.0 - (cast_delta - thresholds["strong_cast_delta"]) * 0.8)

    if cast_delta <= thresholds["good_max_delta"]:
        message = "Couleurs equilibrees : pas de dominante genante."
    elif cast_delta <= thresholds["acceptable_max_delta"]:
        message = "Legere dominante couleur : peu penalisante."
    else:
        message = "Dominante couleur visible : les teintes s'eloignent du rendu naturel."

    return _criterion(
        "color_balance",
        score,
        {
            "blue_mean": round(float(channel_means[0]), 2),
            "green_mean": round(float(channel_means[1]), 2),
            "red_mean": round(float(channel_means[2]), 2),
            "cast_delta": round(cast_delta, 2),
        },
        message,
    )


def _effective_resolution_score(gray: np.ndarray) -> dict[str, Any]:
    thresholds = QUALITY_THRESHOLDS["effective_resolution"]
    height, width = gray.shape[:2]
    lap = cv2.Laplacian(gray, cv2.CV_32F)
    detail_ratio = float(np.mean(np.abs(lap)) / 255.0)
    edge_density = float(np.mean(cv2.Canny(gray, 80, 160) > 0))
    image_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    candidate_regions = propose_regions(image_bgr)
    if candidate_regions:
        main_region = candidate_regions[0]
        useful_area = float(main_region.get("area", 0.0))
        useful_centrality = float(main_region.get("centrality", 0.0))
    else:
        useful_area = 0.35
        useful_centrality = 0.50

    width_score = _linear_score(width, thresholds["min_width"], thresholds["recommended_width"])
    height_score = _linear_score(height, thresholds["min_height"], thresholds["recommended_height"])
    detail_score = _linear_score(detail_ratio, thresholds["detail_soft_min"], thresholds["detail_good_min"])
    useful_area_score = _linear_score(useful_area, 0.16, 0.42)
    useful_centrality_score = _linear_score(useful_centrality, 0.38, 0.82)
    edge_density_score = _linear_score(edge_density, 0.025, 0.11)
    score = (
        0.24 * width_score
        + 0.24 * height_score
        + 0.24 * detail_score
        + 0.12 * useful_area_score
        + 0.06 * useful_centrality_score
        + 0.10 * edge_density_score
    )
    detail_penalty = max(0.0, thresholds["detail_soft_min"] - detail_ratio) * 900.0
    edge_penalty = max(0.0, 0.03 - edge_density) * 220.0
    area_penalty = max(0.0, 0.14 - useful_area) * 110.0
    score -= detail_penalty + edge_penalty + area_penalty

    if width < thresholds["min_width"] or height < thresholds["min_height"]:
        message = "Resolution faible : l'image manque de pixels utiles."
    elif detail_ratio < thresholds["detail_soft_min"] or useful_area < 0.16:
        message = "Resolution effective limitee : l'image semble lissee ou reechantillonnee."
    else:
        message = "Resolution correcte : le niveau de detail est exploitable."

    return _criterion(
        "effective_resolution",
        score,
        {
            "width": int(width),
            "height": int(height),
            "detail_ratio": round(detail_ratio, 4),
            "edge_density": round(edge_density, 4),
            "useful_area": round(useful_area, 4),
            "useful_centrality": round(useful_centrality, 4),
        },
        message,
    )


def _coherence_score(image_bgr: np.ndarray, text_data: dict[str, Any] | None) -> dict[str, Any]:
    thresholds = QUALITY_THRESHOLDS["coherence"]
    if not text_data:
        return _criterion(
            "coherence",
            thresholds["color_missing_score"],
            {
                "clip_similarity": 0.0,
                "clip_score": 0.0,
                "expected_color": None,
                "dominant_color": _closest_color_name(image_bgr),
                "color_score": thresholds["color_missing_score"],
            },
            "Coherence non evaluable finement : texte annonce absent.",
        )

    text_embedding = np.asarray(
        text_data.get("text_embedding", np.zeros(EMBEDDING_VECTOR_SIZE, dtype=np.float32)),
        dtype=np.float32,
    ).reshape(-1)
    image_embedding = _encode_image_embedding(image_bgr)
    clip_similarity = _cosine_similarity(image_embedding, text_embedding)
    clip_score = clip_similarity * 100.0

    expected_color = text_data.get("color")
    dominant_color = _closest_color_name(image_bgr)
    if not expected_color:
        color_score = thresholds["color_missing_score"]
    elif dominant_color == expected_color:
        color_score = thresholds["color_match_score"]
    else:
        color_score = thresholds["color_soft_match_score"]

    score = thresholds["clip_weight"] * clip_score + thresholds["color_weight"] * color_score

    if clip_similarity >= 0.70:
        message = "Bonne coherence entre le crop selectionne et le texte de l'annonce."
    elif clip_similarity >= 0.45:
        message = "Coherence moyenne : le produit semble proche de la description, mais l'alignement peut etre ameliore."
    else:
        message = "Coherence faible : le crop ou le texte semblent mal alignes."

    return _criterion(
        "coherence",
        score,
        {
            "clip_similarity": round(clip_similarity, 4),
            "clip_score": round(clip_score, 2),
            "expected_color": expected_color,
            "dominant_color": dominant_color,
            "color_score": round(float(color_score), 2),
        },
        message,
    )


def global_score(criteria: dict[str, dict[str, Any]]) -> float:
    total = 0.0
    for name, weight in ANALYZER_WEIGHTS.items():
        total += criteria[name]["score"] * weight
    return round(total, 2)


def _build_advice(criteria: dict[str, dict[str, Any]]) -> tuple[list[str], list[str]]:
    ranked = sorted(criteria.items(), key=lambda item: item[1]["score"])
    weakest = [name for name, payload in ranked if payload["score"] < 70.0][:3]

    advice_fr: list[str] = []
    advice_darija: list[str] = []
    for name in weakest:
        template = ADVICE_TEMPLATES.get(name)
        if template is None:
            continue
        advice_fr.append(template["fr"])
        advice_darija.append(template["darija"])

    if not advice_fr:
        advice_fr.append("Photo globalement propre : garde ce cadrage et cette lumiere.")
        advice_darija.append("Tsowira mzyana bzzaf: kammel b nafs cadrage w nafs d'daw.")

    return advice_fr, advice_darija


def analyze(image_input: ImageInput, text_data: dict[str, Any] | None = None) -> dict[str, Any]:
    image_bgr = _load_image(image_input)
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    criteria = {
        "sharpness": _sharpness_score(gray),
        "exposure": _exposure_score(gray),
        "contrast": _contrast_score(gray),
        "color_balance": _color_balance_score(image_bgr),
        "effective_resolution": _effective_resolution_score(gray),
        "coherence": _coherence_score(image_bgr, text_data),
    }

    score = global_score(criteria)
    advice_fr, advice_darija = _build_advice(criteria)

    if score >= 85.0:
        summary = "Tres bonne photo produit."
    elif score >= 70.0:
        summary = "Photo exploitable avec quelques ameliorations possibles."
    elif score >= 50.0:
        summary = "Qualite moyenne : plusieurs corrections sont recommandees."
    else:
        summary = "Photo insuffisante pour une fiche produit e-commerce convaincante."

    return {
        "criteria": criteria,
        "global_score": score,
        "summary_fr": summary,
        "advice_fr": advice_fr,
        "advice_darija": advice_darija,
        "image_shape": tuple(int(v) for v in image_bgr.shape),
    }


def analyze_image(image_input: ImageInput, *args: Any, **kwargs: Any) -> dict[str, Any]:
    text_data = kwargs.get("text_data")
    return analyze(image_input, text_data=text_data)
