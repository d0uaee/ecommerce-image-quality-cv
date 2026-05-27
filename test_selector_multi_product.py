from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from config import OUTPUT_DIR, RAW_IMAGES_DIR
from src.candidate_region_generator import propose_regions
from src.selector import select_product
from src.text_processor import process_text

REPORT_PATH = OUTPUT_DIR / "reports" / "selector_multi_product_report.json"
COMPOSITE_PATH = OUTPUT_DIR / "reports" / "selector_multi_product_input.jpg"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def load_sample_images(limit: int = 3) -> list[np.ndarray]:
    images: list[np.ndarray] = []
    for path in RAW_IMAGES_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if image is not None:
                images.append(image)
        if len(images) >= limit:
            break
    if len(images) < limit:
        raise RuntimeError("Pas assez d'images pour construire le test multi-produits.")
    return images


def build_composite(images: list[np.ndarray]) -> np.ndarray:
    resized = [cv2.resize(image, (260, 260)) for image in images]
    canvas = np.full((320, 920, 3), 245, dtype=np.uint8)
    x_positions = [20, 330, 640]
    y_positions = [35, 20, 42]

    for image, x, y in zip(resized, x_positions, y_positions):
        canvas[y : y + 260, x : x + 260] = image
        cv2.rectangle(canvas, (x, y), (x + 260, y + 260), (30, 30, 30), 2)
    return canvas


def main() -> None:
    images = load_sample_images(3)
    composite = build_composite(images)

    OUTPUT_DIR.joinpath("reports").mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(COMPOSITE_PATH), composite)

    candidates = propose_regions(composite)
    text_data = process_text(
        "Chaussure noire pour homme",
        "Produit principal: basket noire style running pour fiche e-commerce.",
    )
    result = select_product(composite, candidates, text_data)

    report = {
        "input_image": str(COMPOSITE_PATH),
        "candidate_count": len(candidates),
        "selected_bbox": result["selected_bbox"],
        "refined_bbox": result["refined_bbox"],
        "selected_score": result["selected_score"],
        "clip_backend": result["candidates"][0]["clip_backend"],
        "candidates": result["candidates"],
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    print(f"Composite image saved to {COMPOSITE_PATH}")
    print(f"Selection report saved to {REPORT_PATH}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
