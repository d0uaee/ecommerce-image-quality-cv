from __future__ import annotations

import argparse
import csv
import logging
import os
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from PIL import Image, ImageFile
import requests

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
        "--fashion-manifest",
        type=Path,
        default=None,
        help="Optional CSV manifest for curated shoes/clothing images. If provided, it replaces Kaggle for fashion categories.",
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
        if _looks_like_kaggle_root(candidate):
            LOGGER.info("Using existing Kaggle dataset at %s", candidate)
            return candidate

    last_error: Exception | None = None

    try:
        import kagglehub

        LOGGER.info("Downloading Kaggle dataset %s into local cache via kagglehub...", KAGGLE_DATASET_ID)
        root = Path(kagglehub.dataset_download(KAGGLE_DATASET_ID))
        LOGGER.info("Kaggle dataset cached at %s", root)
        return root
    except Exception as exc:
        last_error = exc
        LOGGER.warning("kagglehub unavailable or broken, trying Kaggle API fallback: %s", exc)

    try:
        root = _download_with_kaggle_cli()
        LOGGER.info("Kaggle dataset prepared via CLI at %s", root)
        return root
    except Exception as exc:
        last_error = exc
        LOGGER.warning("Kaggle CLI fallback failed, trying Kaggle API fallback: %s", exc)

    try:
        root = _download_with_kaggle_api()
        LOGGER.info("Kaggle dataset extracted at %s", root)
        return root
    except Exception as exc:
        message = (
            "Kaggle dataset not found locally and automatic download failed. "
            "Fix kagglehub/kagglesdk, configure the Kaggle API, or provide --kaggle-root "
            "or KAGGLE_FASHION_DATASET_DIR."
        )
        if last_error is not None:
            raise RuntimeError(f"{message}\nPrevious kagglehub error: {last_error}") from exc
        raise RuntimeError(message) from exc


def _looks_like_kaggle_root(root: Path) -> bool:
    if not root.exists():
        return False
    metadata_candidates = list(root.rglob("styles.csv")) + list(root.rglob("images.csv"))
    images_dir = next((p for p in root.rglob("images") if p.is_dir()), None)
    return bool(metadata_candidates and images_dir)


def _download_with_kaggle_cli() -> Path:
    cache_root = PROJECT_ROOT / "dataset_cache" / "kaggle_fashion"
    extract_root = cache_root / "cli_extracted"
    extract_root.mkdir(parents=True, exist_ok=True)

    if _looks_like_kaggle_root(extract_root):
        return extract_root

    command = [
        str(Path(sys.executable)),
        "-m",
        "kaggle",
        "datasets",
        "download",
        "-d",
        KAGGLE_DATASET_ID,
        "-p",
        str(extract_root),
        "--unzip",
    ]
    LOGGER.info("Downloading Kaggle dataset %s via Kaggle CLI...", KAGGLE_DATASET_ID)
    subprocess.run(command, check=True)

    if not _looks_like_kaggle_root(extract_root):
        raise RuntimeError(f"Kaggle CLI finished but dataset layout is incomplete under {extract_root}")
    return extract_root


def _download_with_kaggle_api() -> Path:
    cache_root = PROJECT_ROOT / "dataset_cache" / "kaggle_fashion"
    cache_root.mkdir(parents=True, exist_ok=True)

    if _looks_like_kaggle_root(cache_root):
        return cache_root

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except Exception as exc:
        raise RuntimeError("Kaggle API package is not available.") from exc

    api = KaggleApi()
    api.authenticate()

    extract_root = cache_root / "api_extracted"
    extract_root.mkdir(parents=True, exist_ok=True)

    if _looks_like_kaggle_root(extract_root):
        return extract_root

    dataset_slug = KAGGLE_DATASET_ID
    LOGGER.info("Downloading Kaggle dataset %s via Kaggle API unzip mode...", dataset_slug)
    api.dataset_download_files(dataset_slug, path=str(extract_root), unzip=True, quiet=False)

    if not _looks_like_kaggle_root(extract_root):
        raise RuntimeError(f"Kaggle API finished but dataset layout is incomplete under {extract_root}")

    return extract_root


def locate_metadata_and_images(root: Path) -> tuple[Path, Path]:
    metadata_csv = next(root.rglob("styles.csv"), None) or next(root.rglob("images.csv"), None)
    images_dir = next((p for p in root.rglob("images") if p.is_dir()), None)
    if not metadata_csv or not images_dir:
        raise FileNotFoundError(f"Could not locate metadata CSV and images/ under {root}")
    return metadata_csv, images_dir


def load_kaggle_rows(metadata_csv: Path) -> Iterable[dict[str, str]]:
    with metadata_csv.open("r", encoding="utf-8", newline="") as handle:
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


def classify_shopify_record(record: dict[str, object]) -> str | None:
    category = normalize_text(str(record.get("ground_truth_category", ""))).lower()
    title = normalize_text(str(record.get("product_title", ""))).lower()
    description = normalize_text(str(record.get("product_description", ""))).lower()
    text_blob = " ".join([category, title, description])

    if "apparel & accessories > shoes" in category:
        return "shoes"
    if "apparel & accessories > clothing" in category:
        return "clothing"
    if is_portable_electronics_record(record):
        return "portable_electronics"
    if any(token in text_blob for token in SHOE_KEYWORDS):
        return "shoes"
    return None


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
    metadata_path: Path,
    counters: dict[str, int],
    kaggle_root: Path,
) -> None:
    metadata_csv, images_dir = locate_metadata_and_images(kaggle_root)

    for row in load_kaggle_rows(metadata_csv):
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
        persist_metadata(metadata_path, metadata_rows)
        counts[category] += 1
        LOGGER.info("Accepted Kaggle %s -> %s (%s/%s)", item_id, image_id, counts[category], TARGET_COUNTS[category])

        if counts["shoes"] >= TARGET_COUNTS["shoes"] and counts["clothing"] >= TARGET_COUNTS["clothing"]:
            return


def load_manifest_rows(manifest_path: Path) -> Iterable[dict[str, str]]:
    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def load_manifest_image(row: dict[str, str]) -> Image.Image | None:
    local_path = normalize_text(row.get("local_path"))
    source_url = normalize_text(row.get("source_url"))

    if local_path:
        path = Path(local_path)
        if not path.is_absolute():
            path = (PROJECT_ROOT / path).resolve()
        try:
            return Image.open(path).convert("RGB")
        except Exception:
            return None

    if source_url:
        try:
            response = requests.get(source_url, timeout=30)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGB")
        except Exception:
            return None

    return None


def copy_manifest_subset(
    *,
    output_dirs: dict[str, Path],
    counts: dict[str, int],
    min_width: int,
    min_height: int,
    metadata_rows: list[dict[str, str]],
    metadata_path: Path,
    counters: dict[str, int],
    manifest_path: Path,
) -> None:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Fashion manifest not found: {manifest_path}")

    LOGGER.info("Building fashion subset from curated manifest: %s", manifest_path)

    for row in load_manifest_rows(manifest_path):
        category = normalize_text(row.get("category")).lower()
        if category not in {"shoes", "clothing"}:
            continue
        if counts[category] >= TARGET_COUNTS[category]:
            continue

        image = load_manifest_image(row)
        if image is None:
            LOGGER.debug("Rejected manifest row with unreadable image: %s", row)
            continue

        decision = quality_gate(image, min_width, min_height)
        if not decision.accepted:
            LOGGER.debug("Rejected manifest row (%s): %s", category, decision.notes)
            continue

        counters[category] += 1
        image_id = f"{category[:3].upper()}_{counters[category]:03d}"
        filename = f"{image_id}.jpg"
        destination = output_dirs["originals"] / category / filename
        save_image(image, destination)

        title = normalize_text(row.get("title")) or f"{category} item {image_id}"
        description = normalize_text(row.get("description")) or title
        source_dataset = normalize_text(row.get("source_dataset")) or "curated_manifest"
        extra_notes = normalize_text(row.get("notes"))
        notes = decision.notes if not extra_notes else f"{decision.notes}; {extra_notes}"

        metadata_rows.append(
            build_metadata_row(
                image_id=image_id,
                filename=filename,
                filepath=destination,
                category=category,
                source_dataset=source_dataset,
                title=title,
                description=description,
                width=decision.width,
                height=decision.height,
                notes=notes,
            )
        )
        persist_metadata(metadata_path, metadata_rows)
        counts[category] += 1
        LOGGER.info(
            "Accepted curated %s -> %s (%s/%s)",
            category,
            image_id,
            counts[category],
            TARGET_COUNTS[category],
        )

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
    metadata_path: Path,
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
        persist_metadata(metadata_path, metadata_rows)
        counts["portable_electronics"] += 1
        LOGGER.info(
            "Accepted Shopify '%s' -> %s (%s/%s)",
            title[:80],
            image_id,
            counts["portable_electronics"],
            TARGET_COUNTS["portable_electronics"],
        )


def copy_shopify_all_categories(
    *,
    output_dirs: dict[str, Path],
    counts: dict[str, int],
    min_width: int,
    min_height: int,
    metadata_rows: list[dict[str, str]],
    metadata_path: Path,
    counters: dict[str, int],
    splits: list[str],
) -> None:
    for record in iter_shopify_records(splits):
        if all(counts[category] >= TARGET_COUNTS[category] for category in TARGET_COUNTS):
            return

        category = classify_shopify_record(record)
        if category not in TARGET_COUNTS:
            continue
        if counts[category] >= TARGET_COUNTS[category]:
            continue

        image = coerce_shopify_image(record.get("product_image"))
        if image is None:
            continue

        decision = quality_gate(image, min_width, min_height)
        if not decision.accepted:
            LOGGER.debug(
                "Rejected Shopify '%s' (%s): %s",
                normalize_text(str(record.get("product_title", ""))),
                category,
                decision.notes,
            )
            continue

        counters[category] += 1
        image_id = f"{category[:3].upper()}_{counters[category]:03d}"
        filename = f"{image_id}.jpg"
        destination = output_dirs["originals"] / category / filename
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
                category=category,
                source_dataset=SHOPIFY_DATASET_ID,
                title=title,
                description=description,
                width=decision.width,
                height=decision.height,
                notes=notes,
            )
        )
        persist_metadata(metadata_path, metadata_rows)
        counts[category] += 1
        LOGGER.info(
            "Accepted Shopify %s '%s' -> %s (%s/%s)",
            category,
            title[:60],
            image_id,
            counts[category],
            TARGET_COUNTS[category],
        )


def write_metadata(metadata_path: Path, rows: list[dict[str, str]]) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=METADATA_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def persist_metadata(metadata_path: Path, rows: list[dict[str, str]]) -> None:
    rows.sort(key=lambda row: (row["category"], row["image_id"]))
    write_metadata(metadata_path, rows)


def load_existing_rows(metadata_path: Path) -> list[dict[str, str]]:
    if not metadata_path.exists():
        return []

    with metadata_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def bootstrap_existing_dataset(
    *,
    output_dirs: dict[str, Path],
    metadata_rows: list[dict[str, str]],
    counts: dict[str, int],
    counters: dict[str, int],
) -> None:
    existing_rows = load_existing_rows(output_dirs["metadata"])
    rows_by_path = {
        str(Path(row["filepath"])).replace("\\", "/"): row
        for row in existing_rows
        if row.get("filepath")
    }
    metadata_rows.extend(existing_rows)

    for category in TARGET_COUNTS:
        category_dir = output_dirs["originals"] / category
        if not category_dir.exists():
            continue

        for image_path in sorted(category_dir.iterdir()):
            if not image_path.is_file() or image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            image_id = image_path.stem
            counts[category] += 1

            try:
                suffix_value = int(image_id.split("_")[-1])
                counters[category] = max(counters[category], suffix_value)
            except ValueError:
                counters[category] = max(counters[category], counts[category])

            path_key = str(image_path).replace("\\", "/")
            if path_key in rows_by_path:
                continue

            try:
                with Image.open(image_path) as image:
                    width, height = image.size
            except OSError:
                width = 0
                height = 0

            metadata_rows.append(
                build_metadata_row(
                    image_id=image_id,
                    filename=image_path.name,
                    filepath=image_path,
                    category=category,
                    source_dataset="bootstrap_existing_dataset",
                    title=image_id,
                    description=image_id,
                    width=width,
                    height=height,
                    notes="Recovered from existing dataset files.",
                )
            )


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
    bootstrap_existing_dataset(
        output_dirs=output_dirs,
        metadata_rows=metadata_rows,
        counts=counts,
        counters=counters,
    )
    if metadata_rows:
        persist_metadata(output_dirs["metadata"], metadata_rows)
        LOGGER.info(
            "Loaded existing dataset state: shoes=%s, clothing=%s, portable_electronics=%s",
            counts["shoes"],
            counts["clothing"],
            counts["portable_electronics"],
        )

    if args.fashion_manifest:
        copy_manifest_subset(
            output_dirs=output_dirs,
            counts=counts,
            min_width=args.min_width,
            min_height=args.min_height,
            metadata_rows=metadata_rows,
            metadata_path=output_dirs["metadata"],
            counters=counters,
            manifest_path=args.fashion_manifest,
        )
    elif args.kaggle_root:
        kaggle_root = locate_kaggle_root(args.kaggle_root)
        copy_kaggle_subset(
            output_dirs=output_dirs,
            counts=counts,
            min_width=args.min_width,
            min_height=args.min_height,
            metadata_rows=metadata_rows,
            metadata_path=output_dirs["metadata"],
            counters=counters,
            kaggle_root=kaggle_root,
        )
    else:
        LOGGER.info("No fashion manifest or local Kaggle root provided. Using Shopify streaming for all categories.")
        copy_shopify_all_categories(
            output_dirs=output_dirs,
            counts=counts,
            min_width=args.min_width,
            min_height=args.min_height,
            metadata_rows=metadata_rows,
            metadata_path=output_dirs["metadata"],
            counters=counters,
            splits=args.shopify_splits,
        )
    if counts["portable_electronics"] < TARGET_COUNTS["portable_electronics"]:
        copy_shopify_subset(
            output_dirs=output_dirs,
            counts=counts,
            min_width=args.min_width,
            min_height=args.min_height,
            metadata_rows=metadata_rows,
            metadata_path=output_dirs["metadata"],
            counters=counters,
            splits=args.shopify_splits,
        )

    validate_final_counts(counts)
    persist_metadata(output_dirs["metadata"], metadata_rows)

    LOGGER.info("Final dataset created at %s", output_dirs["root"])
    for category in ["shoes", "clothing", "portable_electronics"]:
        LOGGER.info("%s: %s images", category, counts[category])


if __name__ == "__main__":
    main()
