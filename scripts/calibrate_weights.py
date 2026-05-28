from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ANALYZER_WEIGHTS
from evaluate_full import HUMAN_TEMPLATE_CSV, NEUTRAL_TEXT_DATA
from src.analyzer import analyze


CRITERIA = [
    "sharpness",
    "exposure",
    "contrast",
    "color_balance",
    "effective_resolution",
    "framing",
    "coherence",
]

REPORT_DIR = PROJECT_ROOT / "output" / "reports"
CALIBRATION_CSV = REPORT_DIR / "weight_calibration_results.csv"
CALIBRATION_JSON = REPORT_DIR / "best_weight_calibration.json"


def load_annotations() -> pd.DataFrame:
    frame = pd.read_csv(HUMAN_TEMPLATE_CSV)
    frame["score_humain"] = pd.to_numeric(frame["score_humain"], errors="coerce")
    labeled = frame.dropna(subset=["score_humain"]).copy()
    if len(labeled) < 10:
        raise RuntimeError("Pas assez d'annotations humaines pour calibrer les poids.")
    return labeled


def score_image(path_str: str) -> dict[str, float]:
    image_path = PROJECT_ROOT / path_str
    if not image_path.exists():
        image_path = Path(path_str)
    result = analyze(image_path, text_data=NEUTRAL_TEXT_DATA)
    return {name: float(result["criteria"][name]["score"]) for name in CRITERIA}


def build_feature_frame(labeled: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for _, row in labeled.iterrows():
        features = score_image(str(row["image"]))
        feature_row: dict[str, float | str] = {
            "image": str(row["image"]),
            "score_humain": float(row["score_humain"]),
        }
        feature_row.update(features)
        rows.append(feature_row)
    return pd.DataFrame(rows)


def evaluate_weights(frame: pd.DataFrame, weights: dict[str, float]) -> tuple[float, float]:
    auto = np.zeros(len(frame), dtype=np.float64)
    for name, weight in weights.items():
        auto += frame[name].to_numpy(dtype=np.float64) * weight
    rho, p_value = spearmanr(auto, frame["score_humain"].to_numpy(dtype=np.float64))
    rho = 0.0 if pd.isna(rho) else float(rho)
    p_value = 1.0 if pd.isna(p_value) else float(p_value)
    return rho, p_value


def random_weight_search(frame: pd.DataFrame, samples: int = 4000, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, float]] = []

    baseline_rho, baseline_p = evaluate_weights(frame, ANALYZER_WEIGHTS)
    baseline_row = {name: float(ANALYZER_WEIGHTS.get(name, 0.0)) for name in CRITERIA}
    baseline_row.update({"rho": baseline_rho, "p_value": baseline_p, "kind": "baseline"})
    rows.append(baseline_row)

    alpha = np.array([1.8, 1.5, 1.2, 0.8, 1.5, 1.4, 1.1], dtype=np.float64)
    for _ in range(samples):
        sample = rng.dirichlet(alpha)
        weights = {name: float(value) for name, value in zip(CRITERIA, sample)}
        rho, p_value = evaluate_weights(frame, weights)
        row = dict(weights)
        row.update({"rho": rho, "p_value": p_value, "kind": "random"})
        rows.append(row)

    results = pd.DataFrame(rows).sort_values("rho", ascending=False).reset_index(drop=True)
    return results


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    labeled = load_annotations()
    feature_frame = build_feature_frame(labeled)
    results = random_weight_search(feature_frame)
    results.to_csv(CALIBRATION_CSV, index=False, encoding="utf-8")

    best = results.iloc[0].to_dict()
    best_weights = {name: round(float(best[name]), 4) for name in CRITERIA}
    payload = {
        "best_weights": best_weights,
        "best_rho": round(float(best["rho"]), 6),
        "best_p_value": round(float(best["p_value"]), 6),
        "baseline_weights": {name: float(ANALYZER_WEIGHTS.get(name, 0.0)) for name in CRITERIA},
        "baseline_rho": round(float(results[results["kind"] == "baseline"].iloc[0]["rho"]), 6),
        "baseline_p_value": round(float(results[results["kind"] == "baseline"].iloc[0]["p_value"]), 6),
    }
    CALIBRATION_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    print(f"CSV: {CALIBRATION_CSV}")
    print(f"JSON: {CALIBRATION_JSON}")


if __name__ == "__main__":
    main()
