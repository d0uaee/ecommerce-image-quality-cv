from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from generate_degraded import (
    apply_bad_crop,
    apply_blur,
    apply_brightness,
    apply_jpeg_compression,
    apply_low_resolution,
)
from src.analyzer import analyze

RAW_IMAGES_DIR = Path("data/raw_images")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def first_real_image() -> np.ndarray:
    for path in RAW_IMAGES_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if image is not None:
                return image
    raise RuntimeError("Aucune image de test trouvee dans data/raw_images")


def build_clean_reference() -> np.ndarray:
    image = np.full((1200, 1200, 3), 215, dtype=np.uint8)
    cv2.rectangle(image, (280, 220), (920, 980), (110, 110, 110), -1)
    cv2.rectangle(image, (280, 220), (920, 980), (40, 40, 40), 12)
    cv2.circle(image, (600, 420), 120, (90, 90, 90), -1)
    cv2.line(image, (360, 720), (840, 720), (50, 50, 50), 10)
    cv2.line(image, (360, 800), (840, 800), (70, 70, 70), 8)
    cv2.ellipse(image, (600, 580), (170, 110), 0, 0, 360, (175, 175, 175), -1)
    for offset in range(0, 260, 20):
        cv2.line(image, (430 + offset, 320), (430 + offset, 930), (25, 25, 25), 2)
    for offset in range(0, 180, 18):
        cv2.line(image, (360, 470 + offset), (840, 470 + offset), (230, 230, 230), 2)
    return image


def lower_contrast(image: np.ndarray) -> np.ndarray:
    mean = np.full_like(image, int(image.mean()))
    return cv2.addWeighted(image, 0.35, mean, 0.65, 0.0)


def add_color_cast(image: np.ndarray) -> np.ndarray:
    tinted = image.astype(np.float32)
    tinted[:, :, 2] *= 1.30
    tinted[:, :, 0] *= 0.78
    return np.clip(tinted, 0, 255).astype(np.uint8)


def assert_drop(base: float, degraded: float, criterion: str, min_drop: float = 8.0) -> None:
    if degraded < base - min_drop:
        print(f"[OK] {criterion}: {base:.2f} -> {degraded:.2f}")
        return
    raise AssertionError(
        f"{criterion} ne chute pas assez: score initial={base:.2f}, score degrade={degraded:.2f}"
    )


def main() -> None:
    image = build_clean_reference()
    baseline = analyze(image)
    base_scores = {name: payload["score"] for name, payload in baseline["criteria"].items()}

    degraded_cases = {
        "sharpness": apply_blur(image, 11),
        "exposure": apply_brightness(image, 0.40),
        "contrast": lower_contrast(image),
        "color_balance": add_color_cast(image),
        "effective_resolution": apply_low_resolution(image, 0.28),
    }

    print("Baseline:", base_scores)
    for criterion, degraded_image in degraded_cases.items():
        result = analyze(degraded_image)
        degraded_score = result["criteria"][criterion]["score"]
        assert_drop(base_scores[criterion], degraded_score, criterion)

    extra_cases = {
        "overexposure": analyze(apply_brightness(image, 1.75))["criteria"]["exposure"]["score"],
        "jpeg": analyze(apply_jpeg_compression(image, 12))["criteria"]["sharpness"]["score"],
        "bad_crop": analyze(apply_bad_crop(image, 0.62))["global_score"],
    }

    print("Extra checks:", extra_cases)

    real_image_score = analyze(first_real_image())["global_score"]
    print("Smoke test real image global score:", real_image_score)


if __name__ == "__main__":
    main()
