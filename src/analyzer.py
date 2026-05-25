from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from config import ANALYZER_WEIGHTS, QUALITY_THRESHOLDS


ImageInput = str | Path | np.ndarray


ADVICE_TEMPLATES = {
    "sharpness": {
        "fr": "Image trop douce : stabilise le smartphone, refais la mise au point et évite le zoom numérique.",
        "darija": "Tsowira ma hiyach hada: chdd telephonk mzyan, dir focus مزيان, w b3ed mn zoom numérique.",
    },
    "exposure": {
        "fr": "Exposition à corriger : ajoute une lumière douce ou éloigne le produit d'une source trop forte.",
        "darija": "Lidawa khas-ha tetslah: zid noor hani ola b3ed lproduit 3la noor qwi بزاف.",
    },
    "contrast": {
        "fr": "Contraste faible : utilise un fond plus propre et sépare mieux le produit de l'arrière-plan.",
        "darija": "Lcontrast da3if: sta3mel fond nqiy w khalli lproduit yban mzyan 3la l'arrière-plan.",
    },
    "color_balance": {
        "fr": "Légère dominante couleur : photographie près d'une lumière naturelle pour garder des couleurs fidèles.",
        "darija": "Kayna dominante khfifa f lwan: swer qrib l'daw tabi3i باش ibqaw lwan s7i7in.",
    },
    "effective_resolution": {
        "fr": "Résolution effective limitée : évite les captures d'écran et garde l'image originale en grande taille.",
        "darija": "Resolution ma kfayach: ma تستعملch screenshot w khlli tsowira l'asliya b taille kbira.",
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
        raise ValueError("L'image doit avoir 3 canaux ou être en niveaux de gris.")
    return image.astype(np.uint8)


def _criterion(name: str, score: float, raw_value: float | dict[str, float], message: str) -> dict[str, Any]:
    return {
        "name": name,
        "score": round(_clamp(score), 2),
        "raw_value": raw_value,
        "message_fr": message,
    }


def _sharpness_score(gray: np.ndarray) -> dict[str, Any]:
    thresholds = QUALITY_THRESHOLDS["sharpness"]
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    score = _linear_score(
        lap_var,
        thresholds["very_blurry_max"],
        thresholds["excellent_min"],
    )

    if lap_var < thresholds["very_blurry_max"]:
        message = "Netteté très faible : la photo est franchement floue."
    elif lap_var < thresholds["soft_max"]:
        message = "Netteté limitée : le produit manque de détails fins."
    elif lap_var < thresholds["good_min"]:
        message = "Netteté correcte : les détails sont visibles mais encore perfectibles."
    else:
        message = "Bonne netteté : les contours et textures sont bien lisibles."

    return _criterion("sharpness", score, round(lap_var, 2), message)


def _exposure_score(gray: np.ndarray) -> dict[str, Any]:
    thresholds = QUALITY_THRESHOLDS["exposure"]
    mean_brightness = float(gray.mean())
    std_brightness = float(gray.std())
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

    if mean_brightness < thresholds["extreme_dark"]:
        message = "Sous-exposition forte : l'image est trop sombre."
    elif mean_brightness > thresholds["extreme_bright"]:
        message = "Surexposition forte : les hautes lumières sont brûlées."
    elif deviation > thresholds["tolerance_ok"]:
        message = "Exposition moyenne : la lumière n'est pas encore bien équilibrée."
    else:
        message = "Exposition maîtrisée : la luminosité globale est correcte."

    return _criterion(
        "exposure",
        score,
        {
            "mean_brightness": round(mean_brightness, 2),
            "std_brightness": round(std_brightness, 2),
        },
        message,
    )


def _contrast_score(gray: np.ndarray) -> dict[str, Any]:
    thresholds = QUALITY_THRESHOLDS["contrast"]
    std_value = float(gray.std())
    score = _linear_score(std_value, thresholds["flat_max"], thresholds["strong_min"])

    if std_value < thresholds["flat_max"]:
        message = "Contraste très faible : l'image paraît plate."
    elif std_value < thresholds["acceptable_min"]:
        message = "Contraste faible : le produit se détache mal."
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
        message = "Couleurs équilibrées : pas de dominante gênante."
    elif cast_delta <= thresholds["acceptable_max_delta"]:
        message = "Légère dominante couleur : peu pénalisante."
    else:
        message = "Dominante couleur visible : les teintes s'éloignent du rendu naturel."

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

    width_score = _linear_score(width, thresholds["min_width"], thresholds["recommended_width"])
    height_score = _linear_score(height, thresholds["min_height"], thresholds["recommended_height"])
    detail_score = _linear_score(
        detail_ratio,
        thresholds["detail_soft_min"],
        thresholds["detail_good_min"],
    )
    score = 0.4 * width_score + 0.4 * height_score + 0.2 * detail_score

    if width < thresholds["min_width"] or height < thresholds["min_height"]:
        message = "Résolution faible : l'image manque de pixels utiles."
    elif detail_ratio < thresholds["detail_soft_min"]:
        message = "Résolution effective limitée : l'image semble lissée ou rééchantillonnée."
    else:
        message = "Résolution correcte : le niveau de détail est exploitable."

    return _criterion(
        "effective_resolution",
        score,
        {
            "width": int(width),
            "height": int(height),
            "detail_ratio": round(detail_ratio, 4),
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
        advice_fr.append("Photo globalement propre : garde ce cadrage et cette lumière.")
        advice_darija.append("Tsowira مزيانة bzzaf: kammel b nafs cadrage w nafs d'daw.")

    return advice_fr, advice_darija


def analyze(image_input: ImageInput) -> dict[str, Any]:
    image_bgr = _load_image(image_input)
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    criteria = {
        "sharpness": _sharpness_score(gray),
        "exposure": _exposure_score(gray),
        "contrast": _contrast_score(gray),
        "color_balance": _color_balance_score(image_bgr),
        "effective_resolution": _effective_resolution_score(gray),
    }

    score = global_score(criteria)
    advice_fr, advice_darija = _build_advice(criteria)

    if score >= 85.0:
        summary = "Très bonne photo produit."
    elif score >= 70.0:
        summary = "Photo exploitable avec quelques améliorations possibles."
    elif score >= 50.0:
        summary = "Qualité moyenne : plusieurs corrections sont recommandées."
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
    return analyze(image_input)
