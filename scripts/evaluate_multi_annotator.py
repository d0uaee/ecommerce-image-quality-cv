from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
from scipy.stats import spearmanr


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluate_full import HUMAN_TEMPLATE_ANNOTATOR2_CSV, HUMAN_TEMPLATE_CSV, REPORT_DIR


MULTI_ANNOTATOR_CSV = REPORT_DIR / "multi_annotator_summary.csv"
MULTI_ANNOTATOR_MD = REPORT_DIR / "multi_annotator_report.md"


def _normalize_image_column(frame: pd.DataFrame) -> pd.DataFrame:
    subset = frame.copy()
    subset["image"] = subset["image"].astype(str).str.replace("\\", "/", regex=False)
    return subset


def _pairwise_agreement(frame: pd.DataFrame, columns: list[str], tolerance: float) -> dict[str, float]:
    exact_scores: list[float] = []
    tolerance_scores: list[float] = []
    rho_scores: list[float] = []
    p_scores: list[float] = []

    for idx, col_a in enumerate(columns):
        for col_b in columns[idx + 1 :]:
            pair = frame[[col_a, col_b]].dropna()
            if len(pair) < 3:
                continue
            exact_scores.append(float((pair[col_a] == pair[col_b]).mean()))
            tolerance_scores.append(float((pair[col_a] - pair[col_b]).abs().le(tolerance).mean()))
            rho, p_value = spearmanr(pair[col_a], pair[col_b])
            if not pd.isna(rho):
                rho_scores.append(float(rho))
            if not pd.isna(p_value):
                p_scores.append(float(p_value))

    if not exact_scores:
        return {
            "pair_count": 0,
            "exact_agreement_mean": 0.0,
            "tolerance_agreement_mean": 0.0,
            "inter_annotator_spearman_mean": 0.0,
            "inter_annotator_p_value_mean": 1.0,
        }

    return {
        "pair_count": len(exact_scores),
        "exact_agreement_mean": float(sum(exact_scores) / len(exact_scores)),
        "tolerance_agreement_mean": float(sum(tolerance_scores) / len(tolerance_scores)),
        "inter_annotator_spearman_mean": float(sum(rho_scores) / len(rho_scores)) if rho_scores else 0.0,
        "inter_annotator_p_value_mean": float(sum(p_scores) / len(p_scores)) if p_scores else 1.0,
    }


def _write_pending(message: str, n_rows: int) -> None:
    report = [
        "# Evaluation multi-annotateur",
        "",
        "- Statut : pending",
        f"- Message : {message}",
        f"- Lignes completes : {n_rows}",
    ]
    MULTI_ANNOTATOR_MD.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not HUMAN_TEMPLATE_CSV.exists():
        raise FileNotFoundError(f"CSV annotateur 1 introuvable: {HUMAN_TEMPLATE_CSV}")
    if not HUMAN_TEMPLATE_ANNOTATOR2_CSV.exists():
        raise FileNotFoundError(f"CSV annotateur 2 introuvable: {HUMAN_TEMPLATE_ANNOTATOR2_CSV}")

    annotator1 = _normalize_image_column(pd.read_csv(HUMAN_TEMPLATE_CSV))
    annotator2 = _normalize_image_column(pd.read_csv(HUMAN_TEMPLATE_ANNOTATOR2_CSV))

    score_columns = [col for col in annotator2.columns if col.startswith("score_humain")]
    if not score_columns:
        raise ValueError("Aucune colonne score_humain detectee dans le CSV multi-annotateurs.")

    if score_columns == ["score_humain"]:
        annotator1["score_humain"] = pd.to_numeric(annotator1["score_humain"], errors="coerce")
        annotator2["score_humain"] = pd.to_numeric(annotator2["score_humain"], errors="coerce")
        merged = annotator1[["image", "score_auto", "score_humain"]].rename(
            columns={"score_humain": "score_humain_1"}
        ).merge(
            annotator2[["image", "score_humain"]].rename(columns={"score_humain": "score_humain_2"}),
            on="image",
            how="inner",
        )
        complete = merged.dropna(subset=["score_humain_1", "score_humain_2"]).copy()
        if len(complete) < 3:
            _write_pending("au moins 3 images doivent etre notees par les deux annotateurs.", len(complete))
            return

        complete["score_humain_moyen"] = (complete["score_humain_1"] + complete["score_humain_2"]) / 2.0
        metrics = _pairwise_agreement(complete, ["score_humain_1", "score_humain_2"], tolerance=0.5)
        annotator_count = 2
        scale_label = "0..1"
    else:
        multi = annotator2[["image", "score_auto", *score_columns]].copy()
        for col in score_columns:
            multi[col] = pd.to_numeric(multi[col], errors="coerce")

        stacked = pd.concat([multi[col] for col in score_columns], axis=0).dropna()
        if stacked.empty:
            _write_pending("aucune note humaine exploitable detectee dans le CSV multi-annotateurs.", 0)
            return

        scale_divisor = 10.0 if float(stacked.max()) > 1.0 else 1.0
        normalized_columns: list[str] = []
        for col in score_columns:
            norm_col = f"{col}_norm"
            multi[norm_col] = multi[col] / scale_divisor
            normalized_columns.append(norm_col)

        complete = multi.dropna(subset=score_columns, how="all").copy()
        complete["score_humain_moyen"] = complete[normalized_columns].mean(axis=1, skipna=True)
        complete = complete.dropna(subset=["score_humain_moyen"]).copy()
        if len(complete) < 3:
            _write_pending("pas assez de lignes annotees dans le CSV multi-annotateurs.", len(complete))
            return

        metrics = _pairwise_agreement(complete, score_columns, tolerance=1.0 if scale_divisor == 10.0 else 0.5)
        annotator_count = len(score_columns)
        scale_label = "0..10" if scale_divisor == 10.0 else "0..1"

    rho_avg, p_avg = spearmanr(complete["score_auto"], complete["score_humain_moyen"])
    summary_row = {
        "n_multi_annotated": int(len(complete)),
        "annotator_count": int(annotator_count),
        "score_scale": scale_label,
        "pair_count": int(metrics["pair_count"]),
        "exact_agreement_mean": round(metrics["exact_agreement_mean"], 4),
        "tolerance_agreement_mean": round(metrics["tolerance_agreement_mean"], 4),
        "inter_annotator_spearman_mean": round(metrics["inter_annotator_spearman_mean"], 6),
        "inter_annotator_p_value_mean": round(metrics["inter_annotator_p_value_mean"], 6),
        "auto_vs_avg_human_spearman": 0.0 if pd.isna(rho_avg) else round(float(rho_avg), 6),
        "auto_vs_avg_human_p_value": 1.0 if pd.isna(p_avg) else round(float(p_avg), 6),
    }
    pd.DataFrame([summary_row]).to_csv(MULTI_ANNOTATOR_CSV, index=False, encoding="utf-8")

    report = [
        "# Evaluation multi-annotateur",
        "",
        "- Statut : ok",
        f"- Images annotees exploitables : {summary_row['n_multi_annotated']}",
        f"- Nombre d'annotateurs : {summary_row['annotator_count']}",
        f"- Echelle detectee : {summary_row['score_scale']}",
        f"- Paires d'annotateurs comparees : {summary_row['pair_count']}",
        f"- Accord exact moyen : {summary_row['exact_agreement_mean']:.4f}",
        f"- Accord moyen a tolerance : {summary_row['tolerance_agreement_mean']:.4f}",
        f"- Spearman moyen inter-annotateurs : {summary_row['inter_annotator_spearman_mean']:.6f}",
        f"- p-value moyenne inter-annotateurs : {summary_row['inter_annotator_p_value_mean']:.6f}",
        f"- Spearman score auto vs moyenne humaine : {summary_row['auto_vs_avg_human_spearman']:.6f}",
        f"- p-value score auto vs moyenne humaine : {summary_row['auto_vs_avg_human_p_value']:.6f}",
        "",
        f"- CSV resume : `{MULTI_ANNOTATOR_CSV}`",
    ]
    MULTI_ANNOTATOR_MD.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
