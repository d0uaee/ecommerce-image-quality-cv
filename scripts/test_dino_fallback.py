from __future__ import annotations

from pathlib import Path
import sys

import cv2
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import REGION_PROPOSAL_CONFIG
from src.candidate_region_generator import detect_with_dino, propose_regions


REPORT_DIR = PROJECT_ROOT / "output" / "reports"
DISAGREEMENTS_CSV = REPORT_DIR / "disagreements.csv"
DINO_FALLBACK_CSV = REPORT_DIR / "dino_fallback_cases.csv"
DINO_FALLBACK_MD = REPORT_DIR / "dino_fallback_report.md"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not DISAGREEMENTS_CSV.exists():
        raise FileNotFoundError(f"CSV introuvable: {DISAGREEMENTS_CSV}")

    frame = pd.read_csv(DISAGREEMENTS_CSV)
    difficult = frame[
        (frame["disagreement_type"] == "human_high_auto_low")
        & (frame["image"].str.contains("originals", case=False, na=False))
    ].copy()
    if difficult.empty:
        difficult = frame[frame["image"].str.contains("originals", case=False, na=False)].copy()
        difficult["abs_gap"] = difficult["gap_auto_minus_human"].abs()
        difficult = difficult.sort_values("abs_gap", ascending=False).head(8)
    else:
        difficult = difficult.sort_values("gap_auto_minus_human").head(8)

    rows: list[dict[str, object]] = []
    original_flag = REGION_PROPOSAL_CONFIG["use_dino"]
    try:
        for _, row in difficult.iterrows():
            image_path = Path(str(row["image"]))
            image_bgr = cv2.imread(str(image_path))
            if image_bgr is None:
                continue
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

            REGION_PROPOSAL_CONFIG["use_dino"] = False
            saliency_regions = propose_regions(image_rgb)
            dino_regions = detect_with_dino(image_rgb, "product")

            rows.append(
                {
                    "image": str(image_path).replace("\\", "/"),
                    "category": next((part for part in image_path.parts if part in {"shoes", "clothing", "portable_electronics"}), "unknown"),
                    "saliency_count": len(saliency_regions),
                    "dino_count": len(dino_regions),
                    "saliency_top_bbox": saliency_regions[0]["bbox"] if saliency_regions else None,
                    "dino_top_bbox": dino_regions[0]["bbox"] if dino_regions else None,
                    "saliency_top_area": saliency_regions[0]["area"] if saliency_regions else None,
                    "dino_top_area": dino_regions[0]["area"] if dino_regions else None,
                }
            )
    finally:
        REGION_PROPOSAL_CONFIG["use_dino"] = original_flag

    result = pd.DataFrame(rows)
    result.to_csv(DINO_FALLBACK_CSV, index=False, encoding="utf-8")

    dino_available_cases = int(result["dino_count"].fillna(0).gt(0).sum()) if not result.empty else 0
    report = [
        "# Test DINO fallback",
        "",
        "- Statut : ok",
        f"- Cas difficiles testes : {len(result)}",
        f"- Cas ou DINO retourne au moins une region : {dino_available_cases}",
        f"- CSV detaille : `{DINO_FALLBACK_CSV}`",
        "",
        "## Lecture",
        "",
        "- Ce test compare la saliency par defaut avec DINO sur un petit echantillon de cas difficiles : prioritairement les `human_high_auto_low`, sinon les plus gros desaccords absolus.",
        "- Il sert de preuve experimentale pour la soutenance : le fallback existe, il est testable, mais il n'est active par defaut que si son gain est juge utile.",
    ]
    if dino_available_cases == 0:
        report.append("- Sur cet echantillon, DINO n'apporte pas de region exploitable supplementaire.")
    else:
        report.append("- Sur cet echantillon, DINO propose au moins une region sur plusieurs cas difficiles et peut donc servir de filet de securite ciblé.")

    DINO_FALLBACK_MD.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
