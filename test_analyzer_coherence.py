from __future__ import annotations

import json
from pathlib import Path

from config import OUTPUT_DIR, RAW_IMAGES_DIR
from src.analyzer import analyze
from src.candidate_region_generator import propose_regions
from src.selector import select_product
from src.text_processor import process_text

REPORT_PATH = OUTPUT_DIR / "reports" / "analyzer_coherence_report.json"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def sample_images(limit: int = 3) -> list[Path]:
    images: list[Path] = []
    for path in RAW_IMAGES_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            images.append(path)
        if len(images) >= limit:
            break
    if len(images) < limit:
        raise RuntimeError("Il faut au moins 3 images pour tester la coherence.")
    return images


def main() -> None:
    text_data = process_text(
        "Produit noir e-commerce",
        "Photo produit noire pour une annonce de type chaussure ou vetement.",
    )

    report = []
    for image_path in sample_images(3):
        candidates = propose_regions(image_path)
        selected = select_product(image_path, candidates, text_data)
        analysis = analyze(selected["selected_crop"], text_data=text_data)
        report.append(
            {
                "image": str(image_path),
                "selected_bbox": selected["selected_bbox"],
                "refined_bbox": selected["refined_bbox"],
                "global_score": analysis["global_score"],
                "coherence": analysis["criteria"]["coherence"],
            }
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    print(json.dumps(report, indent=2))
    print(f"Coherence report saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
