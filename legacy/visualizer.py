"""Superpose la détection produit et les scores de critères sur l'image."""

from pathlib import Path
from typing import Union

import cv2
import numpy as np

from src.detector import visualize_detection

_GREEN  = (34, 197, 94)
_ORANGE = (251, 146, 60)
_RED    = (239, 68, 68)

_CRITERION_LABELS = {
    "jpeg_artifacts":      "JPEG",
    "lighting_uniformity": "Light",
    "edge_quality":        "Edges",
    "color_consistency":   "Color",
    "effective_resolution": "Res",
    "clip_coherence":      "CLIP",
}


def _score_color(score: float) -> tuple[int, int, int]:
    if score >= 0.70:
        return _GREEN
    if score >= 0.40:
        return _ORANGE
    return _RED


def annotate_image(
    image_path: Union[str, Path],
    output_path: Union[str, Path],
    criteria: dict,
) -> bool:
    """
    Sauvegarde l'image avec détection + scores de critères superposés.

    Parameters
    ----------
    image_path  : chemin de l'image source
    output_path : chemin de l'image annotée (écrasée si existe)
    criteria    : dict retourné par analyze_image() — clé → {score, message}

    Returns True si l'écriture a réussi.
    """
    # 1. Dessin de la détection (mask + bbox)
    ok = visualize_detection(image_path, output_path)
    if not ok:
        # fallback : copier l'image brute
        img_src = cv2.imread(str(image_path))
        if img_src is None:
            return False
        cv2.imwrite(str(output_path), img_src)

    img = cv2.imread(str(output_path))
    if img is None:
        return False

    h, w = img.shape[:2]
    font       = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.4, min(w, h) / 800)
    thickness  = max(1, int(font_scale * 2))
    line_h     = int(font_scale * 28)
    margin     = 8

    # 2. Fond semi-transparent en bas de l'image
    n_lines = len(criteria)
    overlay_h = n_lines * line_h + margin * 2
    overlay = img.copy()
    cv2.rectangle(overlay, (0, h - overlay_h), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, img, 0.45, 0, img)

    # 3. Texte des scores
    for i, (key, val) in enumerate(criteria.items()):
        score = float(val.get("score", 0.0)) if isinstance(val, dict) else float(val)
        label = _CRITERION_LABELS.get(key, key)
        text  = f"{label}: {score:.2f}"
        color = _score_color(score)
        y = h - overlay_h + margin + (i + 1) * line_h
        cv2.putText(img, text, (margin, y), font, font_scale, color, thickness, cv2.LINE_AA)

    return cv2.imwrite(str(output_path), img)
