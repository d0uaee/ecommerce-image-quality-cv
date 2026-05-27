#!/usr/bin/env python3
"""Smoke test du pipeline zero-shot actuel."""

from __future__ import annotations

from pathlib import Path

import cv2

from src.analyzer import analyze
from src.candidate_region_generator import propose_regions
from src.selector import select_product
from src.text_processor import process_text


def main() -> None:
    image_path = Path("data/raw_images/electronics/001_1.jpg")
    title = "chargeur portable"
    description = "chargeur portable noir"

    print("\n" + "=" * 80)
    print("PIPELINE ZERO-SHOT - TEST D'INTEGRATION")
    print("=" * 80)
    print(f"Image de test : {image_path}")
    print(f"Titre       : {title}")
    print(f"Description : {description}")

    image_bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise FileNotFoundError(f"Impossible de lire l'image de test: {image_path}")

    print("\n[1/4] Traitement du texte...")
    text_data = process_text(title, description)
    print(f"  clean_text : {text_data['clean_text']}")
    print(f"  category   : {text_data['category']}")
    print(f"  color      : {text_data['color']}")

    print("\n[2/4] Proposition de regions candidates...")
    candidates = propose_regions(image_bgr)
    print(f"  nombre de regions : {len(candidates)}")
    for index, candidate in enumerate(candidates, start=1):
        print(
            f"  #{index} bbox={candidate['bbox']} "
            f"area={candidate['area']:.4f} centrality={candidate['centrality']:.4f}"
        )

    print("\n[3/4] Selection du produit...")
    selection = select_product(image_bgr, candidates, text_data)
    best = selection["candidates"][0]
    print(f"  selected_bbox : {selection['selected_bbox']}")
    print(f"  refined_bbox  : {selection['refined_bbox']}")
    print(f"  clip_backend  : {best['clip_backend']}")
    print(f"  score_clip    : {best['score_clip']}")
    print(f"  score_total   : {best['score_total']}")

    print("\n[4/4] Analyse de qualite...")
    analysis = analyze(selection["selected_crop"], text_data=text_data)
    print(f"  global_score  : {analysis['global_score']}")
    print(f"  summary       : {analysis['summary_fr']}")
    for name, payload in analysis["criteria"].items():
        print(f"  - {name:20s}: {payload['score']:6.2f}")

    print("\nRESULTAT")
    print("-" * 80)
    print("Le pipeline zero-shot courant s'est execute sans OCR ni anciens modules.")


if __name__ == "__main__":
    main()
