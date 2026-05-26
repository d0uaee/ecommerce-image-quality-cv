"""Facade rapide : score global + grade A-F pour une image produit."""

from pathlib import Path
from typing import Union

from src.analyzer import analyze_image, global_score

_GRADES = [
    (0.85, "A"),
    (0.70, "B"),
    (0.55, "C"),
    (0.40, "D"),
]


def _grade(score: float) -> str:
    for threshold, letter in _GRADES:
        if score >= threshold:
            return letter
    return "F"


def score_image(
    image_path: Union[str, Path],
    text_prompt: str | None = None,
) -> dict:
    """
    Analyse une image et retourne son score global + grade.

    Returns
    -------
    {
        "global":   float,          # score pondéré [0, 1]
        "grade":    "A"|"B"|"C"|"D"|"F",
        "criteria": dict,           # sous-scores détaillés
        "success":  bool,
        "error":    str | None,
    }
    """
    try:
        report = analyze_image(image_path, text_prompt=text_prompt)
        gs = global_score(report["criteria"])
        return {
            "global": round(gs, 4),
            "grade": _grade(gs),
            "criteria": report["criteria"],
            "success": True,
            "error": None,
        }
    except Exception as exc:
        return {
            "global": 0.0,
            "grade": "F",
            "criteria": {},
            "success": False,
            "error": str(exc),
        }
