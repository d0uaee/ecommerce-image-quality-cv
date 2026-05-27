#!/usr/bin/env python3
"""Smoke test du critere de coherence avec text_data."""

from __future__ import annotations

from pathlib import Path

from config import RAW_IMAGES_DIR
from src.analyzer import analyze
from src.text_processor import process_text


def main() -> None:
    candidates = sorted((RAW_IMAGES_DIR / "portable_electronics").glob("*"))
    if not candidates:
        raise FileNotFoundError(f"Aucune image trouvee dans {RAW_IMAGES_DIR / 'portable_electronics'}")
    image_path = candidates[0]
    text_data = process_text("chargeur portable", "chargeur portable noir")

    result = analyze(image_path, text_data=text_data)
    coherence = result["criteria"]["coherence"]

    print(f"Image: {image_path}")
    print(f"Score global: {result['global_score']}")
    print(f"Score coherence: {coherence['score']}")
    print("Detail coherence:")
    print(coherence["raw_value"])


if __name__ == "__main__":
    main()
