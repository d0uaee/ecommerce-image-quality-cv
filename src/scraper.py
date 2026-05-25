"""
Polite scraper for collecting clean e-commerce product images.

Goal:
- gather 200-300 good product images from Amazon, Zara and Shein
- keep only the three supported families:
  shoes, clothing, portable_electronics
- save image + text metadata for a zero-shot dataset

Notes:
- this is a best-effort scraper based on public HTML, JSON-LD and meta tags
- it prioritizes high-resolution image URLs and warns when an image is below 500 px
- some pages can block bots or change markup; failures are logged and skipped
"""

from __future__ import annotations

import csv
import io
import json
import logging
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ALLOWED_CATEGORIES, RAW_IMAGES_DIR  # noqa: E402


METADATA_CSV = PROJECT_ROOT / "data" / "metadata.csv"
TARGET_TOTAL_MIN = 200
TARGET_TOTAL_MAX = 300
TARGET_PER_CATEGORY = 80
REQUEST_DELAY_MIN = 2.0
REQUEST_DELAY_MAX = 4.5
TIMEOUT = 20
MIN_ACCEPTABLE_SIDE = 500

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36 "
        "EcommerceImageQualityPFE/1.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


SITE_SEEDS = {
    "shoes": [
        "https://www.zara.com/fr/fr/femme-chaussures-l1251.html",
        "https://www.zara.com/fr/fr/homme-chaussures-l769.html",
        "https://www.shein.com/pdsearch/shoes/",
        "https://www.amazon.fr/s?k=shoes",
    ],
    "clothing": [
        "https://www.zara.com/fr/fr/femme-vetements-l1180.html",
        "https://www.zara.com/fr/fr/homme-vetements-l746.html",
        "https://www.shein.com/pdsearch/clothing/",
        "https://www.amazon.fr/s?k=clothing",
    ],
    "portable_electronics": [
        "https://www.amazon.fr/s?k=wireless+earbuds",
        "https://www.amazon.fr/s?k=power+bank",
        "https://www.shein.com/pdsearch/portable%20electronics/",
    ],
}


@dataclass
class ProductCandidate:
    category: str
    product_url: str


@dataclass
class ProductRecord:
    category: str
    title: str
    description: str
    product_url: str
    image_url: str


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def polite_sleep() -> None:
    time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text[:80] or "product"


def fetch(session: requests.Session, url: str) -> BeautifulSoup | None:
    try:
        response = session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as exc:
        log.warning("Failed to fetch %s (%s)", url, exc)
        return None


def iter_json_ld(soup: BeautifulSoup) -> Iterable[dict]:
    for node in soup.select('script[type="application/ld+json"]'):
        raw = node.string or node.get_text(strip=True)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield item
        elif isinstance(data, dict):
            yield data


def product_nodes_from_json_ld(soup: BeautifulSoup) -> list[dict]:
    nodes: list[dict] = []
    for data in iter_json_ld(soup):
        data_type = data.get("@type")
        if data_type == "Product":
            nodes.append(data)
        graph = data.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                if isinstance(item, dict) and item.get("@type") == "Product":
                    nodes.append(item)
    return nodes


def normalize_image_url(url: str) -> str:
    if not url:
        return url
    url = url.strip()
    if url.startswith("//"):
        return "https:" + url

    amazon_match = re.search(r"https://m\.media-amazon\.com/images/I/[^.]+\._[^.]+_\.(jpg|jpeg|png|webp)", url, re.IGNORECASE)
    if amazon_match:
        return re.sub(r"\._[^.]+_\.", ".", amazon_match.group(0))

    url = re.sub(r"([?&])(wid|hei|width|height|fit|crop)=[^&]+", "", url, flags=re.IGNORECASE)
    url = url.replace("&amp;", "&")
    return url


def best_image_from_amazon(soup: BeautifulSoup) -> str | None:
    node = soup.select_one("#landingImage")
    dynamic = node.get("data-a-dynamic-image") if node else None
    if dynamic:
        try:
            payload = json.loads(dynamic)
            if payload:
                return max(
                    payload.keys(),
                    key=lambda key: payload[key][0] * payload[key][1],
                )
        except json.JSONDecodeError:
            pass

    html = str(soup)
    match = re.search(r'"hiRes":"(https:[^"]+)"', html)
    if match:
        return match.group(1).replace("\\u0026", "&").replace("\\", "")
    return None


def best_image_from_json_ld(soup: BeautifulSoup) -> str | None:
    for product in product_nodes_from_json_ld(soup):
        image_value = product.get("image")
        if isinstance(image_value, str):
            return image_value
        if isinstance(image_value, list) and image_value:
            return image_value[0]
    return None


def best_image_from_meta(soup: BeautifulSoup) -> str | None:
    for selector in (
        'meta[property="og:image"]',
        'meta[name="twitter:image"]',
        'meta[property="twitter:image"]',
    ):
        node = soup.select_one(selector)
        if node and node.get("content"):
            return node["content"]
    return None


def extract_title(soup: BeautifulSoup) -> str:
    for product in product_nodes_from_json_ld(soup):
        title = product.get("name")
        if isinstance(title, str) and title.strip():
            return title.strip()

    for selector in (
        "#productTitle",
        "h1",
        'meta[property="og:title"]',
        "title",
    ):
        node = soup.select_one(selector)
        if node is None:
            continue
        value = node.get("content") if node.name == "meta" else node.get_text(" ", strip=True)
        if value:
            return value.strip()
    return ""


def extract_description(soup: BeautifulSoup) -> str:
    for product in product_nodes_from_json_ld(soup):
        description = product.get("description")
        if isinstance(description, str) and description.strip():
            return re.sub(r"\s+", " ", description).strip()

    for selector in (
        'meta[property="og:description"]',
        'meta[name="description"]',
        "#feature-bullets",
        ".product-detail-description",
    ):
        node = soup.select_one(selector)
        if node is None:
            continue
        value = node.get("content") if node.name == "meta" else node.get_text(" ", strip=True)
        if value:
            return re.sub(r"\s+", " ", value).strip()
    return ""


def extract_product_record(category: str, product_url: str, soup: BeautifulSoup) -> ProductRecord | None:
    parsed = urlparse(product_url).netloc.lower()

    if "amazon." in parsed:
        image_url = best_image_from_amazon(soup)
    else:
        image_url = None

    image_url = image_url or best_image_from_json_ld(soup) or best_image_from_meta(soup)
    if not image_url:
        log.warning("No usable image found for %s", product_url)
        return None

    title = extract_title(soup)
    if not title:
        log.warning("No title found for %s", product_url)
        return None

    description = extract_description(soup)

    return ProductRecord(
        category=category,
        title=title,
        description=description,
        product_url=product_url,
        image_url=normalize_image_url(image_url),
    )


def is_likely_product_url(url: str, host: str) -> bool:
    if host in url and "/dp/" in url:
        return True
    if "zara.com" in host and "/product/" in url:
        return True
    if "shein.com" in host and ("-p-" in url or "/product/" in url):
        return True
    return False


def collect_listing_links(soup: BeautifulSoup, source_url: str) -> list[str]:
    host = urlparse(source_url).netloc.lower()
    links: list[str] = []
    seen: set[str] = set()

    for anchor in soup.select("a[href]"):
        href = urljoin(source_url, anchor["href"])
        href = href.split("#")[0]
        if not href.startswith("http"):
            continue
        if not is_likely_product_url(href, host):
            continue
        if href in seen:
            continue
        seen.add(href)
        links.append(href)
    return links


def download_image(session: requests.Session, image_url: str, destination: Path) -> tuple[int, int] | None:
    try:
        response = session.get(image_url, timeout=TIMEOUT)
        response.raise_for_status()
        content = response.content
        image = Image.open(io.BytesIO(content)).convert("RGB")
        width, height = image.size
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination, format="JPEG", quality=95)
        return width, height
    except requests.RequestException as exc:
        log.warning("Failed to download image %s (%s)", image_url, exc)
    except OSError as exc:
        log.warning("Invalid image payload %s (%s)", image_url, exc)
    return None


def load_existing_urls() -> set[str]:
    if not METADATA_CSV.exists():
        return set()

    with open(METADATA_CSV, newline="", encoding="utf-8") as handle:
        return {
            row["product_url"]
            for row in csv.DictReader(handle)
            if row.get("product_url")
        }


def next_id(existing_count: int) -> str:
    return f"img_{existing_count + 1:04d}"


def scrape_category(
    session: requests.Session,
    category: str,
    target_count: int,
    writer: csv.DictWriter,
    existing_urls: set[str],
    existing_rows: int,
) -> int:
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"Unsupported category: {category}")

    saved = 0
    category_dir = RAW_IMAGES_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)

    candidate_urls: list[str] = []
    for seed_url in SITE_SEEDS.get(category, []):
        log.info("[%s] Seed page %s", category, seed_url)
        soup = fetch(session, seed_url)
        polite_sleep()
        if soup is None:
            continue
        candidate_urls.extend(collect_listing_links(soup, seed_url))

    deduped_candidates = list(dict.fromkeys(candidate_urls))
    log.info("[%s] %d candidate product pages", category, len(deduped_candidates))

    for product_url in deduped_candidates:
        if saved >= target_count:
            break
        if product_url in existing_urls:
            continue

        soup = fetch(session, product_url)
        polite_sleep()
        if soup is None:
            continue

        record = extract_product_record(category, product_url, soup)
        if record is None:
            continue

        sample_id = next_id(existing_rows + saved)
        filename = f"{sample_id}_{slugify(record.title)}.jpg"
        image_path = category_dir / filename

        image_size = download_image(session, record.image_url, image_path)
        polite_sleep()
        if image_size is None:
            continue

        width, height = image_size
        if width < MIN_ACCEPTABLE_SIDE or height < MIN_ACCEPTABLE_SIDE:
            log.warning(
                "[%s] image below %d px: %s (%dx%d)",
                category,
                MIN_ACCEPTABLE_SIDE,
                image_path.name,
                width,
                height,
            )

        writer.writerow(
            {
                "id": sample_id,
                "category": category,
                "title": record.title,
                "description": record.description,
                "product_url": record.product_url,
                "image_path": str(image_path.relative_to(PROJECT_ROOT)),
                "width": width,
                "height": height,
            }
        )
        existing_urls.add(product_url)
        saved += 1
        log.info("[%s] saved %s (%d/%d)", category, sample_id, saved, target_count)

    return saved


def main() -> None:
    RAW_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    existing_urls = load_existing_urls()
    append_mode = METADATA_CSV.exists()
    existing_rows = len(existing_urls)

    fieldnames = [
        "id",
        "category",
        "title",
        "description",
        "product_url",
        "image_path",
        "width",
        "height",
    ]

    total_saved = 0
    with requests.Session() as session:
        session.headers.update(HEADERS)
        with open(
            METADATA_CSV,
            "a" if append_mode else "w",
            newline="",
            encoding="utf-8",
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            if not append_mode:
                writer.writeheader()

            for category in ALLOWED_CATEGORIES:
                saved = scrape_category(
                    session=session,
                    category=category,
                    target_count=TARGET_PER_CATEGORY,
                    writer=writer,
                    existing_urls=existing_urls,
                    existing_rows=existing_rows + total_saved,
                )
                total_saved += saved
                handle.flush()
                log.info("Progress: %d saved so far", total_saved)
                if total_saved >= TARGET_TOTAL_MAX:
                    break

    log.info(
        "Finished scraping. Saved %d records. Target range: %d-%d.",
        total_saved,
        TARGET_TOTAL_MIN,
        TARGET_TOTAL_MAX,
    )


if __name__ == "__main__":
    main()
