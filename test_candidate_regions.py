from __future__ import annotations

import json
from pathlib import Path

from config import OUTPUT_DIR, RAW_IMAGES_DIR, REGION_PROPOSAL_CONFIG
from src.candidate_region_generator import detect_with_dino, propose_regions

OUTPUT_PATH = OUTPUT_DIR / "reports" / "candidate_region_comparison.json"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_DINO_PROMPT = "product. clothing item. shoe. electronic device."


def sample_images(limit: int = 5) -> list[Path]:
    images: list[Path] = []
    for path in RAW_IMAGES_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            images.append(path)
        if len(images) >= limit:
            break
    return images


def main() -> None:
    images = sample_images(5)
    if len(images) < 5:
        raise RuntimeError("Il faut au moins 5 images pour comparer saliency et DINO.")

    report = []
    original_use_dino = REGION_PROPOSAL_CONFIG["use_dino"]
    try:
        for image_path in images:
            REGION_PROPOSAL_CONFIG["use_dino"] = False
            saliency_regions = propose_regions(image_path)
            REGION_PROPOSAL_CONFIG["use_dino"] = True
            dino_regions = propose_regions(image_path)
            direct_dino_regions = detect_with_dino(image_path, DEFAULT_DINO_PROMPT)
            report.append(
                {
                    "image": str(image_path),
                    "saliency_regions": saliency_regions,
                    "dino_regions": dino_regions,
                    "direct_dino_regions": direct_dino_regions,
                    "dino_available": bool(dino_regions or direct_dino_regions),
                }
            )
    finally:
        REGION_PROPOSAL_CONFIG["use_dino"] = original_use_dino

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    print(f"Comparison report saved to {OUTPUT_PATH}")
    for item in report:
        print(f"\nImage: {item['image']}")
        print("Saliency:", item["saliency_regions"])
        print("DINO:", item["dino_regions"] if item["dino_regions"] else "unavailable or no regions")


if __name__ == "__main__":
    main()
