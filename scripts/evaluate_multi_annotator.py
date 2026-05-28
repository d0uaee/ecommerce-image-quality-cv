from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
from scipy.stats import spearmanr


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluate_full import (
    HUMAN_TEMPLATE_CSV,
    HUMAN_TEMPLATE_ANNOTATOR2_CSV,
    REPORT_DIR,
)


MULTI_ANNOTATOR_CSV = REPORT_DIR / "multi_annotator_summary.csv"
MULTI_ANNOTATOR_MD = REPORT_DIR / "multi_annotator_report.md"


def _normalize(frame: pd.DataFrame, score_column: str) -> pd.DataFrame:
    subset = frame.copy()
    subset[score_column] = pd.to_numeric(subset[score_column], errors="coerce")
    subset["image"] = subset["image"].astype(str).str.replace("\\", "/", regex=False)
    return subset


def _agreement_metrics(merged: pd.DataFrame) -> dict[str, float]:
    exact = float((merged["score_humain_1"] == merged["score_humain_2"]).mean())
    close = float((merged["score_humain_1"] - merged["score_humain_2"]).abs().le(0.5).mean())
    rho, p_value = spearmanr(merged["score_humain_1"], merged["score_humain_2"])
    return {
        "exact_agreement": exact,
        "tolerance_agreement": close,
        "inter_annotator_spearman": 0.0 if pd.isna(rho) else float(rho),
        "inter_annotator_p_value": 1.0 if pd.isna(p_value) else float(p_value),
    }


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not HUMAN_TEMPLATE_CSV.exists():
        raise FileNotFoundError(f"CSV annotateur 1 introuvable: {HUMAN_TEMPLATE_CSV}")
    if not HUMAN_TEMPLATE_ANNOTATOR2_CSV.exists():
        raise FileNotFoundError(f"CSV annotateur 2 introuvable: {HUMAN_TEMPLATE_ANNOTATOR2_CSV}")

    annotator1 = _normalize(pd.read_csv(HUMAN_TEMPLATE_CSV), "score_humain")
    annotator2 = _normalize(pd.read_csv(HUMAN_TEMPLATE_ANNOTATOR2_CSV), "score_humain")

    merged = annotator1[["image", "score_auto", "score_humain"]].rename(
        columns={"score_humain": "score_humain_1"}
    ).merge(
        annotator2[["image", "score_humain"]].rename(columns={"score_humain": "score_humain_2"}),
        on="image",
        how="inner",
    )

    complete = merged.dropna(subset=["score_humain_1", "score_humain_2"]).copy()
    if len(complete) < 3:
        report = [
            "# Evaluation multi-annotateur",
            "",
            "- Statut : pending",
            "- Message : au moins 3 images doivent etre notees par les deux annotateurs.",
            f"- Lignes completes : {len(complete)}",
        ]
        MULTI_ANNOTATOR_MD.write_text("\n".join(report), encoding="utf-8")
        print("\n".join(report))
        return

    complete["score_humain_moyen"] = (complete["score_humain_1"] + complete["score_humain_2"]) / 2.0
    metrics = _agreement_metrics(complete)
    rho_avg, p_avg = spearmanr(complete["score_auto"], complete["score_humain_moyen"])

    summary_row = {
        "n_double_annotated": int(len(complete)),
        "exact_agreement": round(metrics["exact_agreement"], 4),
        "tolerance_agreement": round(metrics["tolerance_agreement"], 4),
        "inter_annotator_spearman": round(metrics["inter_annotator_spearman"], 6),
        "inter_annotator_p_value": round(metrics["inter_annotator_p_value"], 6),
        "auto_vs_avg_human_spearman": 0.0 if pd.isna(rho_avg) else round(float(rho_avg), 6),
        "auto_vs_avg_human_p_value": 1.0 if pd.isna(p_avg) else round(float(p_avg), 6),
    }
    pd.DataFrame([summary_row]).to_csv(MULTI_ANNOTATOR_CSV, index=False, encoding="utf-8")

    report = [
        "# Evaluation multi-annotateur",
        "",
        "- Statut : ok",
        f"- Images notees par les deux annotateurs : {summary_row['n_double_annotated']}",
        f"- Accord exact : {summary_row['exact_agreement']:.4f}",
        f"- Accord a tolerance ±0.5 : {summary_row['tolerance_agreement']:.4f}",
        f"- Spearman inter-annotateurs : {summary_row['inter_annotator_spearman']:.6f}",
        f"- p-value inter-annotateurs : {summary_row['inter_annotator_p_value']:.6f}",
        f"- Spearman score auto vs moyenne humaine : {summary_row['auto_vs_avg_human_spearman']:.6f}",
        f"- p-value score auto vs moyenne humaine : {summary_row['auto_vs_avg_human_p_value']:.6f}",
        "",
        f"- CSV resume : `{MULTI_ANNOTATOR_CSV}`",
    ]
    MULTI_ANNOTATOR_MD.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
