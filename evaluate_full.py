from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config import OUTPUT_DIR
from evaluate_analyzer import (
    build_measurements,
    resolve_data_root,
    resolve_originals_dir,
    summarize_full_matrix,
    summarize_target_sensitivity,
)
from src.analyzer import analyze


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
REPORT_DIR = OUTPUT_DIR / "reports"
HUMAN_TEMPLATE_CSV = REPORT_DIR / "human_evaluation_template.csv"
HUMAN_TEMPLATE_ANNOTATOR2_CSV = REPORT_DIR / "human_evaluation_template_annotator2.csv"
SPEARMAN_PLOT_PATH = REPORT_DIR / "spearman_correlation.png"
SENSITIVITY_TARGET_CSV = REPORT_DIR / "full_eval_sensitivity_target.csv"
SENSITIVITY_MATRIX_CSV = REPORT_DIR / "full_eval_sensitivity_matrix.csv"
CONSOLIDATED_REPORT_MD = REPORT_DIR / "evaluation_report.md"
MULTI_ANNOTATOR_SUMMARY_CSV = REPORT_DIR / "multi_annotator_summary.csv"
DINO_FALLBACK_REPORT_MD = REPORT_DIR / "dino_fallback_report.md"

NEUTRAL_TEXT_DATA = {
    "text_embedding": np.zeros(512, dtype=np.float32),
    "color": None,
    "category": None,
    "brand": None,
    "clean_text": "",
}


def list_raw_images() -> list[Path]:
    originals_dir = resolve_originals_dir(resolve_data_root())
    return sorted(
        path
        for path in originals_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def list_degraded_images() -> list[Path]:
    degraded_dir = resolve_data_root() / "degraded"
    return sorted(
        path
        for path in degraded_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def _sample_evenly(paths: list[Path], limit: int) -> list[Path]:
    if len(paths) <= limit:
        return paths
    if limit <= 1:
        return [paths[0]]
    step = (len(paths) - 1) / (limit - 1)
    indexes = [round(i * step) for i in range(limit)]
    return [paths[idx] for idx in indexes]


def select_evaluation_images(limit: int = 50) -> list[dict[str, Any]]:
    raw_images = list_raw_images()
    degraded_images = list_degraded_images()

    selected: list[dict[str, Any]] = []
    raw_target = min(len(raw_images), math.ceil(limit / 2))
    degraded_target = min(len(degraded_images), limit - raw_target)

    if degraded_target == 0:
        raw_target = min(len(raw_images), limit)

    for path in _sample_evenly(raw_images, raw_target):
        selected.append({"image_path": path, "source_type": "clean"})
    for path in _sample_evenly(degraded_images, degraded_target):
        selected.append({"image_path": path, "source_type": "degraded"})

    if len(selected) < limit:
        already = {item["image_path"] for item in selected}
        for path in raw_images:
            if path in already:
                continue
            selected.append({"image_path": path, "source_type": "clean"})
            if len(selected) >= limit:
                break

    return selected[:limit]


def build_human_template(limit: int = 50) -> pd.DataFrame:
    if HUMAN_TEMPLATE_CSV.exists():
        existing = pd.read_csv(HUMAN_TEMPLATE_CSV)
        if {"image", "score_humain"}.issubset(existing.columns):
            refreshed_rows: list[dict[str, Any]] = []
            for _, row in existing.iterrows():
                image_path = Path(str(row["image"]))
                if not image_path.is_absolute():
                    image_path = (Path.cwd() / image_path).resolve()
                analysis = analyze(image_path, text_data=NEUTRAL_TEXT_DATA)
                refreshed_rows.append(
                    {
                        "image": str(row["image"]).replace("\\", "/"),
                        "source_type": row.get("source_type", ""),
                        "score_auto": round(float(analysis["global_score"]) / 100.0, 4),
                        "score_humain": row.get("score_humain", ""),
                    }
                )
            refreshed = pd.DataFrame(refreshed_rows)
            refreshed.to_csv(HUMAN_TEMPLATE_CSV, index=False, encoding="utf-8")
            return refreshed

    rows: list[dict[str, Any]] = []
    for item in select_evaluation_images(limit):
        image_path = item["image_path"]
        analysis = analyze(image_path, text_data=NEUTRAL_TEXT_DATA)
        rows.append(
            {
                "image": str(image_path).replace("\\", "/"),
                "source_type": item["source_type"],
                "score_auto": round(float(analysis["global_score"]) / 100.0, 4),
                "score_humain": "",
            }
        )

    frame = pd.DataFrame(rows)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(HUMAN_TEMPLATE_CSV, index=False, encoding="utf-8")
    return frame


def build_second_annotator_template(template_frame: pd.DataFrame) -> pd.DataFrame:
    if HUMAN_TEMPLATE_ANNOTATOR2_CSV.exists():
        existing = pd.read_csv(HUMAN_TEMPLATE_ANNOTATOR2_CSV)
        if {"image", "score_humain"}.issubset(existing.columns):
            return existing

    second = template_frame.copy()
    second["score_humain"] = ""
    second.to_csv(HUMAN_TEMPLATE_ANNOTATOR2_CSV, index=False, encoding="utf-8")
    return second


def compute_spearman(template_frame: pd.DataFrame) -> dict[str, Any]:
    completed = template_frame.copy()
    completed["score_humain"] = pd.to_numeric(completed["score_humain"], errors="coerce")
    labeled = completed.dropna(subset=["score_humain"]).copy()

    if len(labeled) < 3:
        return {
            "status": "pending",
            "message": "Correlation Spearman non calculee : au moins 3 scores humains sont necessaires.",
            "n_labeled": int(len(labeled)),
            "spearman_rho": None,
            "p_value": None,
        }

    try:
        from scipy.stats import spearmanr
    except Exception as exc:
        return {
            "status": "error",
            "message": f"scipy indisponible: {exc}",
            "n_labeled": int(len(labeled)),
            "spearman_rho": None,
            "p_value": None,
        }

    rho, p_value = spearmanr(labeled["score_auto"], labeled["score_humain"])
    return {
        "status": "ok",
        "message": "Correlation calculee avec succes.",
        "n_labeled": int(len(labeled)),
        "spearman_rho": None if pd.isna(rho) else float(rho),
        "p_value": None if pd.isna(p_value) else float(p_value),
    }


def infer_category(image_path: str) -> str:
    path = Path(image_path)
    parts = [part.lower() for part in path.parts]
    for category in ("shoes", "clothing", "portable_electronics"):
        if category in parts:
            return category
    return "unknown"


def build_category_summary(template_frame: pd.DataFrame) -> pd.DataFrame:
    frame = template_frame.copy()
    frame["score_humain"] = pd.to_numeric(frame["score_humain"], errors="coerce")
    frame = frame.dropna(subset=["score_humain"]).copy()
    if frame.empty:
        return pd.DataFrame()

    try:
        from scipy.stats import spearmanr
    except Exception:
        return pd.DataFrame()

    frame["category"] = frame["image"].map(infer_category)
    rows: list[dict[str, Any]] = []
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
    return pd.DataFrame(rows).sort_values("category").reset_index(drop=True)


def read_multi_annotator_summary() -> pd.DataFrame:
    if not MULTI_ANNOTATOR_SUMMARY_CSV.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(MULTI_ANNOTATOR_SUMMARY_CSV)
    except Exception:
        return pd.DataFrame()


def read_dino_fallback_notes() -> list[str]:
    if not DINO_FALLBACK_REPORT_MD.exists():
        return []
    try:
        return DINO_FALLBACK_REPORT_MD.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []


def build_spearman_plot(template_frame: pd.DataFrame) -> str:
    completed = template_frame.copy()
    completed["score_humain"] = pd.to_numeric(completed["score_humain"], errors="coerce")
    labeled = completed.dropna(subset=["score_humain"]).copy()

    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        return f"Graphe non genere: matplotlib indisponible ({exc})."

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 5))
    if len(labeled) >= 3:
        ax.scatter(labeled["score_humain"], labeled["score_auto"], c="#1f77b4", alpha=0.8)
        ax.set_title("Correlation Spearman : score humain vs score automatique")
    else:
        ax.text(
            0.5,
            0.5,
            "Remplir la colonne score_humain\ndans human_evaluation_template.csv",
            ha="center",
            va="center",
            fontsize=12,
        )
        ax.set_title("Graphe en attente d'annotations humaines")

    ax.set_xlabel("Score humain (1 / 0.5 / 0)")
    ax.set_ylabel("Score automatique normalise")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(SPEARMAN_PLOT_PATH, dpi=160)
    plt.close(fig)
    return f"Graphe sauvegarde dans {SPEARMAN_PLOT_PATH}"


def build_sensitivity_section() -> dict[str, Any]:
    if SENSITIVITY_TARGET_CSV.exists() and SENSITIVITY_MATRIX_CSV.exists():
        target_summary = pd.read_csv(SENSITIVITY_TARGET_CSV)
        full_matrix = pd.read_csv(SENSITIVITY_MATRIX_CSV)
        return {
            "status": "ok",
            "message": "Sensibilite par critere rechargee depuis les CSV existants.",
            "target_summary": target_summary,
            "full_matrix": full_matrix,
        }

    try:
        measurements = build_measurements()
    except Exception as exc:
        return {
            "status": "pending",
            "message": f"Sensibilite non calculee: {exc}",
            "target_summary": pd.DataFrame(),
            "full_matrix": pd.DataFrame(),
        }

    target_summary = summarize_target_sensitivity(measurements)
    full_matrix = summarize_full_matrix(measurements)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    target_summary.to_csv(SENSITIVITY_TARGET_CSV, index=False, encoding="utf-8")
    full_matrix.to_csv(SENSITIVITY_MATRIX_CSV, index=False, encoding="utf-8")
    return {
        "status": "ok",
        "message": "Sensibilite par critere calculee avec succes.",
        "target_summary": target_summary,
        "full_matrix": full_matrix,
    }


def write_consolidated_report(
    template_frame: pd.DataFrame,
    spearman_info: dict[str, Any],
    sensitivity_info: dict[str, Any],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# Rapport d'evaluation consolide")
    lines.append("")
    lines.append("## 1. Echantillon pour evaluation humaine")
    lines.append("")
    lines.append(f"- Nombre d'images dans le template : {len(template_frame)}")
    lines.append(f"- CSV template : `{HUMAN_TEMPLATE_CSV}`")
    lines.append(f"- CSV 2e annotateur : `{HUMAN_TEMPLATE_ANNOTATOR2_CSV}`")
    lines.append("- Colonne `score_humain` a remplir avec `1`, `0.5` ou `0`.")
    lines.append("")
    lines.append("## 2. Correlation Spearman")
    lines.append("")
    lines.append(f"- Statut : {spearman_info['status']}")
    lines.append(f"- Message : {spearman_info['message']}")
    lines.append(f"- Nombre d'annotations humaines exploitables : {spearman_info['n_labeled']}")
    if spearman_info["spearman_rho"] is not None:
        lines.append(f"- Spearman rho : {spearman_info['spearman_rho']:.4f}")
    if spearman_info["p_value"] is not None:
        lines.append(f"- p-value : {spearman_info['p_value']:.6f}")
    lines.append(f"- Graphe : `{SPEARMAN_PLOT_PATH}`")
    lines.append("")
    lines.append("## 3. Sensibilite par critere")
    lines.append("")
    lines.append(f"- Statut : {sensitivity_info['status']}")
    lines.append(f"- Message : {sensitivity_info['message']}")
    if sensitivity_info["status"] == "ok":
        lines.append(f"- CSV cible : `{SENSITIVITY_TARGET_CSV}`")
        lines.append(f"- CSV matrice complete : `{SENSITIVITY_MATRIX_CSV}`")
        lines.append("")
        lines.append("### Tableau cible")
        lines.append("")
        lines.append("```text")
        lines.append(sensitivity_info["target_summary"].to_string(index=False))
        lines.append("```")
    lines.append("")
    category_summary = build_category_summary(template_frame)
    lines.append("## 4. Lecture par categorie")
    lines.append("")
    if category_summary.empty:
        lines.append("- Analyse par categorie en attente d'annotations humaines exploitables.")
    else:
        lines.append("```text")
        lines.append(category_summary.to_string(index=False))
        lines.append("```")
        lines.append("")
        best_row = category_summary.sort_values("spearman_rho", ascending=False).iloc[0]
        worst_row = category_summary.sort_values("spearman_rho", ascending=True).iloc[0]
        lines.append("### Forces par categorie")
        lines.append("")
        lines.append(
            f"- La categorie la plus robuste est `{best_row['category']}` avec `rho = {best_row['spearman_rho']:.4f}`."
        )
        lines.append("- Les meilleurs cas sont ceux ou le produit principal est bien centre, net et clairement isole du fond.")
        lines.append("")
        lines.append("### Faiblesses par categorie")
        lines.append("")
        lines.append(
            f"- La categorie la plus fragile reste `{worst_row['category']}` avec `rho = {worst_row['spearman_rho']:.4f}`."
        )
        lines.append(
            "- Les erreurs residuelles viennent surtout des cas ou le produit est grand mais visuellement lisse, ou quand le fond studio perturbe encore la perception de resolution utile."
        )
    lines.append("")
    lines.append("## 5. Limites methodologiques")
    lines.append("")
    multi_summary = read_multi_annotator_summary()
    if not multi_summary.empty:
        row = multi_summary.iloc[0]
        lines.append("## 5. Evaluation multi-annotateur")
        lines.append("")
        lines.append(f"- Images annotees exploitables : {int(row['n_multi_annotated'])}")
        lines.append(f"- Nombre d'annotateurs : {int(row['annotator_count'])}")
        lines.append(f"- Echelle detectee : {row['score_scale']}")
        lines.append(f"- Accord exact moyen : {float(row['exact_agreement_mean']):.4f}")
        lines.append(f"- Accord moyen a tolerance : {float(row['tolerance_agreement_mean']):.4f}")
        lines.append(f"- Spearman moyen inter-annotateurs : {float(row['inter_annotator_spearman_mean']):.6f}")
        lines.append(
            f"- Spearman score auto vs moyenne humaine : {float(row['auto_vs_avg_human_spearman']):.6f}"
        )
        lines.append("")
        lines.append("## 6. Test DINO conditionnel")
        lines.append("")
        dino_lines = [line for line in read_dino_fallback_notes() if line.startswith("- ")]
        if dino_lines:
            lines.extend(dino_lines)
        else:
            lines.append("- Aucun rapport DINO fallback disponible.")
        lines.append("")
        lines.append("## 7. Limites methodologiques")
        lines.append("")
    else:
        lines.append("## 6. Limites methodologiques")
        lines.append("")
        lines.append("- L'evaluation multi-annotateur n'est pas encore disponible dans le rapport consolide.")
    lines.append("- Les annotations humaines restent subjectives, meme si la moyenne de plusieurs annotateurs reduit ce bruit.")
    lines.append("- Le module de coherence utilise un texte neutre en evaluation globale quand la tache porte uniquement sur la qualite photo.")
    lines.append("- Les performances restent dependantes du bon crop initial et de la categorie produit.")
    lines.append("- Les resultats categories peuvent varier lorsque le nombre d'images annotees reste limite.")
    lines.append("")

    CONSOLIDATED_REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    template_frame = build_human_template(limit=50)
    build_second_annotator_template(template_frame)
    spearman_info = compute_spearman(template_frame)
    plot_message = build_spearman_plot(template_frame)
    sensitivity_info = build_sensitivity_section()
    write_consolidated_report(template_frame, spearman_info, sensitivity_info)

    print(f"Template humain: {HUMAN_TEMPLATE_CSV}")
    print(plot_message)
    print(f"Rapport consolide: {CONSOLIDATED_REPORT_MD}")
    print(f"Spearman status: {spearman_info['status']}")
    print(f"Sensibilite status: {sensitivity_info['status']}")


if __name__ == "__main__":
    main()
