from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config import DATA_DIR, DEGRADED_DIR, OUTPUT_DIR
from src.analyzer import analyze


DEGRADED_METADATA_CSV = DATA_DIR / "degraded_metadata.csv"
SENSITIVITY_OUTPUT_CSV = OUTPUT_DIR / "reports" / "analyzer_sensitivity.csv"
FULL_MATRIX_OUTPUT_CSV = OUTPUT_DIR / "reports" / "analyzer_sensitivity_full_matrix.csv"

PRIMARY_CRITERION_BY_DEGRADATION = {
    "blur": "sharpness",
    "underexposure": "exposure",
    "overexposure": "exposure",
    "lowres": "effective_resolution",
    "jpeg": "sharpness",
    "bad_crop": "effective_resolution",
}

NEUTRAL_TEXT_DATA = {
    "text_embedding": np.zeros(512, dtype=np.float32),
    "color": None,
    "category": None,
    "brand": None,
    "clean_text": "",
}


def load_degraded_rows() -> list[dict[str, str]]:
    if DEGRADED_METADATA_CSV.exists():
        with open(DEGRADED_METADATA_CSV, newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    rows: list[dict[str, str]] = []
    for path in DEGRADED_DIR.rglob("*.jpg"):
        stem_parts = path.stem.split("_")
        if len(stem_parts) < 3:
            continue
        level = stem_parts[-1]
        degradation = "_".join(stem_parts[1:-1])
        rows.append(
            {
                "image": str(path.relative_to(DATA_DIR)),
                "source": "",
                "type_degradation": degradation,
                "niveau": level,
            }
        )
    return rows


def resolve_source_path(row: dict[str, str]) -> Path | None:
    source_value = row.get("source", "").strip()
    if source_value:
        source_path = DATA_DIR / source_value
        if source_path.exists():
            return source_path

    image_value = row.get("image", "").strip()
    image_path = DATA_DIR / image_value
    image_name = Path(image_value).name
    source_id = image_name.split("_")[0]
    if not source_id:
        return None

    for candidate in (DATA_DIR / "raw_images").rglob(f"{source_id}_*"):
        if candidate.is_file():
            return candidate
    return None


def analyze_scores(image_path: Path) -> dict[str, float]:
    result = analyze(image_path, text_data=NEUTRAL_TEXT_DATA)
    scores = {name: payload["score"] for name, payload in result["criteria"].items()}
    scores["global_score"] = result["global_score"]
    return scores


def build_measurements() -> pd.DataFrame:
    rows = load_degraded_rows()
    if not rows:
        raise FileNotFoundError(
            "Aucune donnée dégradée trouvée. Génère d'abord data/degraded/ et data/degraded_metadata.csv."
        )

    cache: dict[Path, dict[str, float]] = {}
    measurements: list[dict[str, Any]] = []

    for row in rows:
        degraded_path = DATA_DIR / row["image"]
        if not degraded_path.exists():
            continue

        source_path = resolve_source_path(row)
        if source_path is None or not source_path.exists():
            continue

        if source_path not in cache:
            cache[source_path] = analyze_scores(source_path)
        if degraded_path not in cache:
            cache[degraded_path] = analyze_scores(degraded_path)

        clean_scores = cache[source_path]
        degraded_scores = cache[degraded_path]
        degradation = row["type_degradation"]
        primary_criterion = PRIMARY_CRITERION_BY_DEGRADATION.get(degradation, "global_score")

        for criterion_name, clean_score in clean_scores.items():
            degraded_score = degraded_scores[criterion_name]
            measurements.append(
                {
                    "source": str(source_path.relative_to(DATA_DIR)),
                    "degraded_image": str(degraded_path.relative_to(DATA_DIR)),
                    "type_degradation": degradation,
                    "niveau": row.get("niveau", ""),
                    "criterion": criterion_name,
                    "primary_criterion": primary_criterion,
                    "clean_score": clean_score,
                    "degraded_score": degraded_score,
                    "drop": clean_score - degraded_score,
                    "is_target_criterion": criterion_name == primary_criterion,
                    "criterion_dropped": degraded_score < clean_score,
                }
            )

    frame = pd.DataFrame(measurements)
    if frame.empty:
        raise RuntimeError("Impossible de construire les mesures. Vérifie les chemins source/dégradés.")
    return frame


def summarize_target_sensitivity(frame: pd.DataFrame) -> pd.DataFrame:
    target_rows = frame[frame["is_target_criterion"]].copy()
    summary = (
        target_rows.groupby(["type_degradation", "primary_criterion"], as_index=False)
        .agg(
            n=("drop", "size"),
            clean_mean=("clean_score", "mean"),
            degraded_mean=("degraded_score", "mean"),
            avg_drop=("drop", "mean"),
            median_drop=("drop", "median"),
            success_rate=("criterion_dropped", "mean"),
        )
        .sort_values(["type_degradation", "primary_criterion"])
    )
    summary["success_rate"] = (summary["success_rate"] * 100.0).round(2)
    for column in ("clean_mean", "degraded_mean", "avg_drop", "median_drop"):
        summary[column] = summary[column].round(2)
    return summary


def summarize_full_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    matrix = (
        frame.groupby(["type_degradation", "criterion"], as_index=False)
        .agg(
            avg_drop=("drop", "mean"),
            success_rate=("criterion_dropped", "mean"),
        )
        .sort_values(["type_degradation", "criterion"])
    )
    matrix["avg_drop"] = matrix["avg_drop"].round(2)
    matrix["success_rate"] = (matrix["success_rate"] * 100.0).round(2)
    return matrix


def print_summary_table(summary: pd.DataFrame) -> None:
    print("\nTableau sensibilite par critere")
    print(
        summary.to_string(
            index=False,
            columns=[
                "type_degradation",
                "primary_criterion",
                "n",
                "clean_mean",
                "degraded_mean",
                "avg_drop",
                "median_drop",
                "success_rate",
            ],
        )
    )


def main() -> None:
    frame = build_measurements()
    summary = summarize_target_sensitivity(frame)
    matrix = summarize_full_matrix(frame)

    SENSITIVITY_OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SENSITIVITY_OUTPUT_CSV, index=False, encoding="utf-8")
    matrix.to_csv(FULL_MATRIX_OUTPUT_CSV, index=False, encoding="utf-8")

    print_summary_table(summary)
    print(f"\nCSV principal: {SENSITIVITY_OUTPUT_CSV}")
    print(f"CSV matrice complete: {FULL_MATRIX_OUTPUT_CSV}")


if __name__ == "__main__":
    main()
