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
SPEARMAN_PLOT_PATH = REPORT_DIR / "spearman_correlation.png"
SENSITIVITY_TARGET_CSV = REPORT_DIR / "full_eval_sensitivity_target.csv"
SENSITIVITY_MATRIX_CSV = REPORT_DIR / "full_eval_sensitivity_matrix.csv"
CONSOLIDATED_REPORT_MD = REPORT_DIR / "evaluation_report.md"

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
    rows: list[dict[str, Any]] = []
    cwd = Path.cwd()
    for item in select_evaluation_images(limit):
        image_path = item["image_path"]
        analysis = analyze(image_path, text_data=NEUTRAL_TEXT_DATA)
        rows.append(
            {
                "image": str(image_path.relative_to(cwd)),
                "source_type": item["source_type"],
                "score_auto": round(float(analysis["global_score"]) / 100.0, 4),
                "score_humain": "",
            }
        )

    frame = pd.DataFrame(rows)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(HUMAN_TEMPLATE_CSV, index=False, encoding="utf-8")
    return frame


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
        lines.append(sensitivity_info["target_summary"].to_markdown(index=False))
    lines.append("")

    CONSOLIDATED_REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    template_frame = build_human_template(limit=50)
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
