from __future__ import annotations

from pathlib import Path

import pandas as pd

from evaluate_full import HUMAN_TEMPLATE_CSV, NEUTRAL_TEXT_DATA
from src.analyzer import analyze


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "output" / "reports"
DISAGREEMENTS_CSV = REPORT_DIR / "disagreements.csv"

CRITERIA = [
    "sharpness",
    "exposure",
    "contrast",
    "color_balance",
    "effective_resolution",
    "framing",
    "coherence",
]


def resolve_path(path_str: str) -> Path:
    path = PROJECT_ROOT / path_str
    if path.exists():
        return path
    return Path(path_str)


def extract_type_and_level(path: Path) -> tuple[str, str]:
    stem = path.stem
    parts = stem.split("_")
    if len(parts) >= 3:
        return parts[-2], parts[-1]
    source_type = "clean" if "originals" in path.parts else "unknown"
    return source_type, ""


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(HUMAN_TEMPLATE_CSV)
    frame["score_humain"] = pd.to_numeric(frame["score_humain"], errors="coerce")
    labeled = frame.dropna(subset=["score_humain"]).copy()
    rows: list[dict[str, object]] = []

    for _, row in labeled.iterrows():
        image_path = resolve_path(str(row["image"]))
        result = analyze(image_path, text_data=NEUTRAL_TEXT_DATA)
        auto_score = float(result["global_score"]) / 100.0
        gap = auto_score - float(row["score_humain"])
        degradation_type, degradation_level = extract_type_and_level(image_path)

        out_row: dict[str, object] = {
            "image": str(image_path).replace("\\", "/"),
            "source_type": row.get("source_type", ""),
            "degradation_type": degradation_type,
            "degradation_level": degradation_level,
            "score_humain": float(row["score_humain"]),
            "score_auto": round(auto_score, 4),
            "gap_auto_minus_human": round(gap, 4),
            "disagreement_type": (
                "human_high_auto_low"
                if gap <= -0.25
                else "auto_high_human_low"
                if gap >= 0.25
                else "near_agreement"
            ),
        }
        for criterion in CRITERIA:
            out_row[criterion] = float(result["criteria"][criterion]["score"])
        rows.append(out_row)

    out = pd.DataFrame(rows).sort_values(
        ["disagreement_type", "gap_auto_minus_human"],
        ascending=[True, True],
    )
    out.to_csv(DISAGREEMENTS_CSV, index=False, encoding="utf-8")

    summary = out["disagreement_type"].value_counts().to_dict()
    print(f"CSV: {DISAGREEMENTS_CSV}")
    print(f"Summary: {summary}")


if __name__ == "__main__":
    main()
