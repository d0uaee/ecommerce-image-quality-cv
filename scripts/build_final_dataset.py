from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from PIL import Image, ImageFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.candidate_region_generator import propose_regions

ImageFile.LOAD_TRUNCATED_IMAGES = False

LOGGER = logging.getLogger("build_final_dataset")

KAGGLE_DATASET_ID = "paramaggarwal/fashion-product-images-dataset"
SHOPIFY_DATASET_ID = "Shopify/product-catalogue"
TARGET_COUNTS = {
    "shoes": 60,
    "clothing": 60,
    "portable_electronics": 60,
}
METADATA_COLUMNS = [
    "image_id",
    "filename",
    "filepath",
    "category",
    "source_dataset",
    "title",
    "description",
    "width",
    "height",
    "source_type",
    "degradation_type",
    "degradation_level",
    "human_score",
    "notes",
]
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SHOE_KEYWORDS = {
    "shoe",
    "shoes",
    "sneaker",
    "sneakers",
    "boot",
    "boots",
    "sandals",
    "slipper",
    "slippers",
    "heels",
    "heel",
    "loafer",
    "loafers",
    "flat",
    "flats",
    "running shoes",
}
KAGGLE_CLOTHING_TYPES = {
    "tshirts",
    "shirts",
    "topwear",
    "bottomwear",
    "jeans",
    "trousers",
    "shorts",
    "skirts",
    "dresses",
    "sarees",
    "kurta sets",
    "kurtas",
    "sweatshirts",
    "jackets",
    "track pants",
    "leggings",
    "night suits",
    "jumpsuit",
    "jumpsuits",
}
PORTABLE_ELECTRONICS_INCLUDE = {
    "smartphone",
    "mobile phone",
    "cell phone",
    "tablet",
    "laptop",
    "notebook",
    "earbud",
    "earbuds",
    "headphone",
    "headphones",
    "speaker",
    "speakers",
    "smartwatch",
    "smart watch",
    "camera",
    "camcorder",
    "power bank",
    "portable speaker",
    "portable audio",
    "portable game console",
    "gaming handheld",
    "e-reader",
    "ebook reader",
}
PORTABLE_ELECTRONICS_EXCLUDE = {
    "case",
    "cover",
    "cable",
    "charger adapter",
    "screen protector",
    "mount",
    "holder",
    "tripod",
    "watch strap",
    "watch band",
    "bracelet",
    "memory card",
    "stylus",
    "remote control",
}


@dataclass
class QualityDecision:
    accepted: bool
    notes: str
    width: int
    height: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the final zero-shot dataset with shoes, clothing, and portable electronics."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("dataset"),
        help="Target dataset root. Default: dataset/",
    )
    parser.add_argument(
        "--kaggle-root",
        type=Path,
        default=None,
        help="Optional local path to the extracted Kaggle fashion dataset.",
    )
    parser.add_argument(
        "--min-width",
        type=int,
        default=800,
        help="Minimum accepted image width.",
    )
    parser.add_argument(
        "--min-height",
        type=int,
        default=800,
        help="Minimum accepted image height.",
    )
    parser.add_argument(
        "--shopify-splits",
        nargs="+",
        default=["train", "test"],
        help="Shopify splits to scan in order.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logs.",
    )
    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s | %(message)s",
    )


def ensure_output_structure(root: Path) -> dict[str, Path]:
    originals_root = root / "originals"
    degraded_root = root / "degraded"
    annotations_root = root / "annotations"

    for path in [
        originals_root / "shoes",
        originals_root / "clothing",
        originals_root / "portable_electronics",
        degraded_root,
        annotations_root,
    ]:
        path.mkdir(parents=True, exist_ok=True)

    return {
        "root": root,
        "originals": originals_root,
        "degraded": degraded_root,
        "annotations": annotations_root,
        "metadata": root / "metadata.csv",
    }


def locate_kaggle_root(cli_root: Path | None) -> Path:
    candidates = []
    if cli_root:
        candidates.append(cli_root)

    env_root = os.environ.get("KAGGLE_FASHION_DATASET_DIR")
    if env_root:
        candidates.append(Path(env_root))

    for candidate in candidates:
        styles_csv = next(candidate.rglob("styles.csv"), None)
        images_dir = next((p for p in candidate.rglob("images") if p.is_dir()), None)
        if styles_csv and images_dir:
            LOGGER.info("Using existing Kaggle dataset at %s", candidate)
            return candidate

    try:
        import kagglehub
    except ImportError as exc:
        raise RuntimeError(
            "Kaggle dataset not found locally. Install kagglehub or provide --kaggle-root "
            "or KAGGLE_FASHION_DATASET_DIR."
        ) from exc

    LOGGER.info("Downloading Kaggle dataset %s into local cache...", KAGGLE_DATASET_ID)
    root = Path(kagglehub.dataset_download(KAGGLE_DATASET_ID))
    LOGGER.info("Kaggle dataset cached at %s", root)
    return root


def locate_styles_and_images(root: Path) -> tuple[Path, Path]:
    styles_csv = next(root.rglob("styles.csv"), None)
    images_dir = next((p for p in root.rglob("images") if p.is_dir()), None)
    if not styles_csv or not images_dir:
        raise FileNotFoundError(f"Could not locate styles.csv and images/ under {root}")
    return styles_csv, images_dir


def load_kaggle_rows(styles_csv: Path) -> Iterable[dict[str, str]]:
    with styles_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").strip().split())


def classify_kaggle_row(row: dict[str, str]) -> str | None:
    master = normalize_text(row.get("masterCategory")).lower()
    sub = normalize_text(row.get("subCategory")).lower()
    article = normalize_text(row.get("articleType")).lower()

    if sub == "shoes" or article in SHOE_KEYWORDS or any(keyword in article for keyword in SHOE_KEYWORDS):
        return "shoes"

    if master == "apparel":
        return "clothing"

    if sub in KAGGLE_CLOTHING_TYPES or article in KAGGLE_CLOTHING_TYPES:
        return "clothing"

    return None


def build_kaggle_description(row: dict[str, str]) -> str:
    parts = [
        normalize_text(row.get("productDisplayName")),
        normalize_text(row.get("gender")),
        normalize_text(row.get("masterCategory")),
        normalize_text(row.get("subCategory")),
        normalize_text(row.get("articleType")),
        normalize_text(row.get("baseColour")),
        normalize_text(row.get("usage")),
        normalize_text(row.get("season")),
    ]
    description = ", ".join(part for part in parts if part)
    return description


def is_portable_electronics_record(record: dict[str, object]) -> bool:
    category = normalize_text(str(record.get("ground_truth_category", ""))).lower()
    title = normalize_text(str(record.get("product_title", ""))).lower()
    description = normalize_text(str(record.get("product_description", ""))).lower()
    text_blob = " ".join([category, title, description])

    if any(token in text_blob for token in PORTABLE_ELECTRONICS_EXCLUDE):
        return False
    return any(token in text_blob for token in PORTABLE_ELECTRONICS_INCLUDE)


def pil_to_bgr(image: Image.Image) -> np.ndarray:
    rgb = image.convert("RGB")
    return cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)


def quality_gate(image: Image.Image, min_width: int, min_height: int) -> QualityDecision:
    try:
        rgb = image.convert("RGB")
    except Exception as exc:
        return QualityDecision(False, f"Unreadable image: {exc}", 0, 0)

    width, height = rgb.size
    if width < min_width or height < min_height:
        return QualityDecision(False, "Below minimum dimensions", width, height)

    bgr = pil_to_bgr(rgb)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur_value = cv2.Laplacian(gray, cv2.CV_64F).var()
    contrast_value = float(gray.std())
    aspect_ratio = max(width, height) / max(1.0, min(width, height))

    if blur_value < 90.0:
        return QualityDecision(False, f"Too blurry (laplacian={blur_value:.2f})", width, height)
    if contrast_value < 18.0:
        return QualityDecision(False, f"Too flat or washed out (contrast={contrast_value:.2f})", width, height)
    if aspect_ratio > 2.6:
        return QualityDecision(False, f"Unusual aspect ratio ({aspect_ratio:.2f})", width, height)

    try:
        regions = propose_regions(bgr)
    except Exception as exc:
        return QualityDecision(False, f"Region proposal failed: {exc}", width, height)

    if not regions:
        return QualityDecision(False, "No visible main product region", width, height)

    main_region = regions[0]
    main_area = float(main_region["area"])
    main_centrality = float(main_region["centrality"])
    if main_area < 0.10:
        return QualityDecision(False, f"Main product too small (area={main_area:.3f})", width, height)
    if main_centrality < 0.15:
        return QualityDecision(False, f"Main product too peripheral (centrality={main_centrality:.3f})", width, height)
    if len(regions) >= 5 and main_area < 0.22:
        return QualityDecision(False, "Possible collage or multi-product layout", width, height)

    return QualityDecision(
        True,
        f"Accepted (laplacian={blur_value:.2f}, contrast={contrast_value:.2f}, area={main_area:.3f})",
        width,
        height,
    )


def save_image(image: Image.Image, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(destination, format="JPEG", quality=96)


def coerce_shopify_image(image_obj: object) -> Image.Image | None:
    if image_obj is None:
        return None
    if isinstance(image_obj, Image.Image):
        return image_obj.convert("RGB")
    if isinstance(image_obj, dict):
        if isinstance(image_obj.get("bytes"), (bytes, bytearray)):
            try:
                from io import BytesIO

                return Image.open(BytesIO(image_obj["bytes"])).convert("RGB")
            except Exception:
                return None
        path = image_obj.get("path")
        if path:
            try:
                return Image.open(path).convert("RGB")
            except Exception:
                return None
    return None


def build_metadata_row(
    *,
    image_id: str,
    filename: str,
    filepath: Path,
    category: str,
    source_dataset: str,
    title: str,
    description: str,
    width: int,
    height: int,
    notes: str,
) -> dict[str, str]:
    return {
        "image_id": image_id,
        "filename": filename,
        "filepath": str(filepath).replace("\\", "/"),
        "category": category,
        "source_dataset": source_dataset,
        "title": title,
        "description": description,
        "width": str(width),
        "height": str(height),
        "source_type": "original",
        "degradation_type": "",
        "degradation_level": "",
        "human_score": "",
        "notes": notes,
    }


def copy_kaggle_subset(
    *,
    output_dirs: dict[str, Path],
    counts: dict[str, int],
    min_width: int,
    min_height: int,
    metadata_rows: list[dict[str, str]],
    counters: dict[str, int],
    kaggle_root: Path,
) -> None:
    styles_csv, images_dir = locate_styles_and_images(kaggle_root)

    for row in load_kaggle_rows(styles_csv):
        category = classify_kaggle_row(row)
        if category not in {"shoes", "clothing"}:
            continue
        if counts[category] >= TARGET_COUNTS[category]:
            continue

        item_id = normalize_text(row.get("id"))
        if not item_id:
            continue

        image_path = images_dir / f"{item_id}.jpg"
        if not image_path.exists():
            continue

        try:
            with Image.open(image_path) as handle:
                image = handle.convert("RGB")
        except Exception:
            continue

        decision = quality_gate(image, min_width, min_height)
        if not decision.accepted:
            LOGGER.debug("Rejected Kaggle %s (%s): %s", item_id, category, decision.notes)
            continue

        counters[category] += 1
        image_id = f"{category[:3].upper()}_{counters[category]:03d}"
        filename = f"{image_id}.jpg"
        destination = output_dirs["originals"] / category / filename
        save_image(image, destination)

        title = normalize_text(row.get("productDisplayName")) or f"{category} item {item_id}"
        description = build_kaggle_description(row) or title
        metadata_rows.append(
            build_metadata_row(
                image_id=image_id,
                filename=filename,
                filepath=destination,
                category=category,
                source_dataset=KAGGLE_DATASET_ID,
                title=title,
                description=description,
                width=decision.width,
                height=decision.height,
                notes=decision.notes,
            )
        )
        counts[category] += 1
        LOGGER.info("Accepted Kaggle %s -> %s (%s/%s)", item_id, image_id, counts[category], TARGET_COUNTS[category])

        if counts["shoes"] >= TARGET_COUNTS["shoes"] and counts["clothing"] >= TARGET_COUNTS["clothing"]:
            return


def iter_shopify_records(splits: list[str]) -> Iterable[dict[str, object]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "The Hugging Face 'datasets' package is required for Shopify streaming. "
            "Install it with: pip install datasets"
        ) from exc

    for split_name in splits:
        LOGGER.info("Streaming Shopify split: %s", split_name)
        dataset = load_dataset(SHOPIFY_DATASET_ID, split=split_name, streaming=True)
        for record in dataset:
            yield record


def copy_shopify_subset(
    *,
    output_dirs: dict[str, Path],
    counts: dict[str, int],
    min_width: int,
    min_height: int,
    metadata_rows: list[dict[str, str]],
    counters: dict[str, int],
    splits: list[str],
) -> None:
    if counts["portable_electronics"] >= TARGET_COUNTS["portable_electronics"]:
        return

    for record in iter_shopify_records(splits):
        if counts["portable_electronics"] >= TARGET_COUNTS["portable_electronics"]:
            return
        if not is_portable_electronics_record(record):
            continue

        image = coerce_shopify_image(record.get("product_image"))
        if image is None:
            continue

        decision = quality_gate(image, min_width, min_height)
        if not decision.accepted:
            LOGGER.debug(
                "Rejected Shopify '%s': %s",
                normalize_text(str(record.get("product_title", ""))),
                decision.notes,
            )
            continue

        counters["portable_electronics"] += 1
        image_id = f"POR_{counters['portable_electronics']:03d}"
        filename = f"{image_id}.jpg"
        destination = output_dirs["originals"] / "portable_electronics" / filename
        save_image(image, destination)

        title = normalize_text(str(record.get("product_title", ""))) or image_id
        description = normalize_text(str(record.get("product_description", ""))) or title
        category_hint = normalize_text(str(record.get("ground_truth_category", "")))
        notes = f"{decision.notes}; source_category={category_hint}"
        metadata_rows.append(
            build_metadata_row(
                image_id=image_id,
                filename=filename,
                filepath=destination,
                category="portable_electronics",
                source_dataset=SHOPIFY_DATASET_ID,
                title=title,
                description=description,
                width=decision.width,
                height=decision.height,
                notes=notes,
            )
        )
        counts["portable_electronics"] += 1
        LOGGER.info(
            "Accepted Shopify '%s' -> %s (%s/%s)",
            title[:80],
            image_id,
            counts["portable_electronics"],
            TARGET_COUNTS["portable_electronics"],
        )


def write_metadata(metadata_path: Path, rows: list[dict[str, str]]) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=METADATA_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def validate_final_counts(counts: dict[str, int]) -> None:
    missing = {category: target - counts[category] for category, target in TARGET_COUNTS.items() if counts[category] < target}
    if missing:
        missing_text = ", ".join(f"{category}: {remaining} missing" for category, remaining in missing.items())
        raise RuntimeError(f"Dataset build incomplete. {missing_text}")


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)

    output_dirs = ensure_output_structure(args.output_root)
    counts = defaultdict(int)
    counters = defaultdict(int)
    metadata_rows: list[dict[str, str]] = []

    kaggle_root = locate_kaggle_root(args.kaggle_root)
    copy_kaggle_subset(
        output_dirs=output_dirs,
        counts=counts,
        min_width=args.min_width,
        min_height=args.min_height,
        metadata_rows=metadata_rows,
        counters=counters,
        kaggle_root=kaggle_root,
    )
    copy_shopify_subset(
        output_dirs=output_dirs,
        counts=counts,
        min_width=args.min_width,
        min_height=args.min_height,
        metadata_rows=metadata_rows,
        counters=counters,
        splits=args.shopify_splits,
    )

    validate_final_counts(counts)
    metadata_rows.sort(key=lambda row: (row["category"], row["image_id"]))
    write_metadata(output_dirs["metadata"], metadata_rows)

    LOGGER.info("Final dataset created at %s", output_dirs["root"])
    for category in ["shoes", "clothing", "portable_electronics"]:
        LOGGER.info("%s: %s images", category, counts[category])


if __name__ == "__main__":
    main()
