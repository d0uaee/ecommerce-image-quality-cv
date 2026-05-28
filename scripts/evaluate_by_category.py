from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
from scipy.stats import spearmanr


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluate_full import HUMAN_TEMPLATE_CSV


REPORT_DIR = PROJECT_ROOT / "output" / "reports"
CATEGORY_EVAL_CSV = REPORT_DIR / "category_evaluation_summary.csv"


def infer_category(image_path: str) -> str:
    path = Path(image_path)
    parts = [part.lower() for part in path.parts]
    for category in ("shoes", "clothing", "portable_electronics"):
        if category in parts:
            return category
    return "unknown"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(HUMAN_TEMPLATE_CSV)
    frame["score_humain"] = pd.to_numeric(frame["score_humain"], errors="coerce")
    frame = frame.dropna(subset=["score_humain"]).copy()
    frame["category"] = frame["image"].map(infer_category)

    rows: list[dict[str, object]] = []
    for category, subset in frame.groupby("category"):
        rho, p_value = spearmanr(subset["score_auto"], subset["score_humain"])
        rows.append(
            {
                "category": category,
                "n": int(len(subset)),
                "score_auto_mean": round(float(subset["score_auto"].mean()), 4),
                "score_humain_mean": round(float(subset["score_humain"].mean()), 4),
                "spearman_rho": 0.0 if pd.isna(rho) else round(float(rho), 6),
                "p_value": 1.0 if pd.isna(p_value) else round(float(p_value), 6),
            }
        )

    summary = pd.DataFrame(rows).sort_values("category").reset_index(drop=True)
    summary.to_csv(CATEGORY_EVAL_CSV, index=False, encoding="utf-8")
    print(summary.to_string(index=False))
    print(f"CSV: {CATEGORY_EVAL_CSV}")


if __name__ == "__main__":
    main()
