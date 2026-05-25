from __future__ import annotations

import csv
from pathlib import Path

import cv2
import numpy as np

from config import DEGRADED_DIR, RAW_IMAGES_DIR


DEGRADED_METADATA_CSV = RAW_IMAGES_DIR.parent / "degraded_metadata.csv"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

BLUR_LEVELS = {
    "low": 3,
    "medium": 7,
    "high": 11,
}

UNDEREXPOSURE_LEVELS = {
    "low": 0.80,
    "medium": 0.60,
    "high": 0.40,
}

OVEREXPOSURE_LEVELS = {
    "low": 1.20,
    "medium": 1.45,
    "high": 1.75,
}

CROP_LEVELS = {
    "low": 0.92,
    "medium": 0.78,
    "high": 0.62,
}

LOW_RES_LEVELS = {
    "low": 0.70,
    "medium": 0.45,
    "high": 0.28,
}

JPEG_LEVELS = {
    "low": 55,
    "medium": 28,
    "high": 12,
}


def iter_source_images() -> list[Path]:
    return sorted(
        path
        for path in RAW_IMAGES_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def load_image(path: Path) -> np.ndarray | None:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        print(f"skip unreadable image: {path}")
    return image


def save_image(path: Path, image: np.ndarray, jpeg_quality: int = 95) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])


def apply_brightness(image: np.ndarray, factor: float) -> np.ndarray:
    adjusted = np.clip(image.astype(np.float32) * factor, 0, 255)
    return adjusted.astype(np.uint8)


def apply_blur(image: np.ndarray, kernel_size: int) -> np.ndarray:
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)


def apply_bad_crop(image: np.ndarray, crop_ratio: float) -> np.ndarray:
    height, width = image.shape[:2]
    crop_width = max(32, int(width * crop_ratio))
    crop_height = max(32, int(height * crop_ratio))

    x0 = max(0, width - crop_width)
    y0 = max(0, height - crop_height)
    cropped = image[y0 : y0 + crop_height, x0 : x0 + crop_width]
    return cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LINEAR)


def apply_low_resolution(image: np.ndarray, scale: float) -> np.ndarray:
    height, width = image.shape[:2]
    small_width = max(32, int(width * scale))
    small_height = max(32, int(height * scale))
    degraded = cv2.resize(image, (small_width, small_height), interpolation=cv2.INTER_AREA)
    return cv2.resize(degraded, (width, height), interpolation=cv2.INTER_LINEAR)


def apply_jpeg_compression(image: np.ndarray, quality: int) -> np.ndarray:
    success, buffer = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not success:
        return image
    decoded = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    return decoded if decoded is not None else image


def output_path(source_path: Path, index: int, degradation: str, level: str) -> Path:
    category = source_path.parent.name
    filename = f"{index:03d}_{degradation}_{level}.jpg"
    return DEGRADED_DIR / category / filename


def write_metadata(rows: list[dict[str, str]]) -> None:
    with open(DEGRADED_METADATA_CSV, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["image", "source", "type_degradation", "niveau"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    source_images = iter_source_images()
    if not source_images:
        print(f"no source images found in {RAW_IMAGES_DIR}")
        return

    metadata_rows: list[dict[str, str]] = []

    for index, source_path in enumerate(source_images, start=1):
        image = load_image(source_path)
        if image is None:
            continue

        generated_variants = [
            ("blur", BLUR_LEVELS, lambda img, value: apply_blur(img, value)),
            ("underexposure", UNDEREXPOSURE_LEVELS, lambda img, value: apply_brightness(img, value)),
            ("overexposure", OVEREXPOSURE_LEVELS, lambda img, value: apply_brightness(img, value)),
            ("bad_crop", CROP_LEVELS, lambda img, value: apply_bad_crop(img, value)),
            ("lowres", LOW_RES_LEVELS, lambda img, value: apply_low_resolution(img, value)),
            ("jpeg", JPEG_LEVELS, lambda img, value: apply_jpeg_compression(img, value)),
        ]

        for degradation_name, levels, transform in generated_variants:
            for level_name, level_value in levels.items():
                degraded = transform(image, level_value)
                destination = output_path(source_path, index, degradation_name, level_name)
                save_image(destination, degraded)
                metadata_rows.append(
                    {
                        "image": str(destination.relative_to(RAW_IMAGES_DIR.parent)),
                        "source": str(source_path.relative_to(RAW_IMAGES_DIR.parent)),
                        "type_degradation": degradation_name,
                        "niveau": level_name,
                    }
                )

    write_metadata(metadata_rows)
    print(
        f"generated {len(metadata_rows)} degraded images from "
        f"{len(source_images)} source images"
    )


if __name__ == "__main__":
    main()
