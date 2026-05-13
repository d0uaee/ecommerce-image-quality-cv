"""
Jumia Morocco product image scraper.

Scrapes ~100 images per category (electronics, clothing, home_appliances)
and saves them to data/raw_images/{category}/ with metadata in data/metadata.csv.

Respects robots.txt:
- Clearly identifies as a bot in User-Agent
- Stays well under 200 req/min via 2-5s random delays between requests
- Avoids disallowed paths (facet filters, user accounts, etc.)
"""

import csv
import io
import logging
import os
import random
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from PIL import Image

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://www.jumia.ma"

CATEGORIES = {
    "electronics": "/telephone-tablette/",
    "clothing": "/fashion-mode/",
    "home_appliances": "/mlp-electromenager/",
}

IMAGES_PER_CATEGORY = 100
MAX_PAGES_PER_CATEGORY = 10   # safety cap; 20 products/page × 10 = 200 candidates

# Delays (seconds) — keeps us well under the 200 req/min robots.txt limit
REQUEST_DELAY_MIN = 2.0
REQUEST_DELAY_MAX = 5.0

TIMEOUT = 15  # seconds per request

HEADERS = {
    "User-Agent": (
        "EcommerceImageQualityBot/1.0 "
        "(University computer-vision project; "
        "contact: student-research@university.edu; "
        "respects robots.txt)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_IMAGES_DIR = DATA_DIR / "raw_images"
METADATA_CSV = DATA_DIR / "metadata.csv"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def polite_sleep():
    """Sleep a random amount to stay within rate limits."""
    delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
    time.sleep(delay)


def fetch_page(session: requests.Session, url: str) -> BeautifulSoup | None:
    """GET a URL and return a BeautifulSoup object, or None on failure."""
    try:
        response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code == 404:
            log.warning("404 Not Found: %s", url)
            return None
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.Timeout:
        log.error("Timeout fetching: %s", url)
    except requests.exceptions.HTTPError as exc:
        log.error("HTTP error %s: %s", exc.response.status_code, url)
    except requests.exceptions.RequestException as exc:
        log.error("Request failed (%s): %s", exc, url)
    return None


def get_image_url(img_tag) -> str | None:
    """
    Extract the real image URL from an <img> tag.
    Jumia lazy-loads images: the real URL is in `data-src`,
    while `src` holds an SVG placeholder.
    """
    if img_tag is None:
        return None
    # Prefer data-src (lazy-load pattern)
    url = img_tag.get("data-src") or img_tag.get("data-image")
    # Fall back to src only if it's not a data: URI placeholder
    if not url:
        src = img_tag.get("src", "")
        if src and not src.startswith("data:"):
            url = src
    return url or None


def download_image(
    session: requests.Session,
    image_url: str,
    dest_path: Path,
) -> tuple[int, int] | None:
    """
    Download an image to dest_path.
    Returns (width, height) on success, None on failure.
    """
    try:
        resp = session.get(image_url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        resp.raise_for_status()
        content = resp.content
        img = Image.open(io.BytesIO(content))
        width, height = img.size
        # Save original file (keep original format)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(content)
        return width, height
    except requests.exceptions.Timeout:
        log.warning("Timeout downloading image: %s", image_url)
    except requests.exceptions.HTTPError as exc:
        log.warning("HTTP %s downloading image: %s", exc.response.status_code, image_url)
    except requests.exceptions.RequestException as exc:
        log.warning("Failed to download image (%s): %s", exc, image_url)
    except Exception as exc:
        log.warning("Could not process image (%s): %s", exc, image_url)
    return None


def parse_products(soup: BeautifulSoup) -> list[dict]:
    """
    Extract product data from a parsed category listing page.
    Returns a list of dicts with keys: name, product_url, image_url.
    """
    products = []
    cards = soup.select("div.c-prd, article.c-prd")
    for card in cards:
        # Product link & URL
        link_tag = card.find("a", href=True)
        if not link_tag:
            continue
        product_url = urljoin(BASE_URL, link_tag["href"])

        # Product name — prefer h2.c-prd-title, fall back to img alt
        name_tag = card.select_one("h2.c-prd-title, h3.c-prd-title, .c-prd-title")
        if name_tag:
            name = name_tag.get_text(strip=True)
        else:
            img_tag = card.find("img")
            name = img_tag.get("alt", "").strip() if img_tag else ""

        if not name:
            continue

        # Image URL
        img_tag = card.find("img")
        image_url = get_image_url(img_tag)
        if not image_url:
            continue

        # Make sure image URL is absolute
        if image_url.startswith("//"):
            image_url = "https:" + image_url
        elif image_url.startswith("/"):
            image_url = urljoin(BASE_URL, image_url)

        products.append(
            {"name": name, "product_url": product_url, "image_url": image_url}
        )
    return products


def scrape_category(
    session: requests.Session,
    category: str,
    path: str,
    target_count: int,
    csv_writer,
    existing_urls: set[str],
) -> int:
    """
    Scrape images for one category.
    Returns the number of images successfully saved.
    """
    category_dir = RAW_IMAGES_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    page = 1

    while saved < target_count and page <= MAX_PAGES_PER_CATEGORY:
        url = f"{BASE_URL}{path}?page={page}"
        log.info("[%s] Fetching page %d → %s", category, page, url)

        soup = fetch_page(session, url)
        polite_sleep()

        if soup is None:
            log.warning("[%s] Skipping page %d (fetch failed)", category, page)
            page += 1
            continue

        products = parse_products(soup)
        if not products:
            log.info("[%s] No products on page %d — stopping", category, page)
            break

        log.info("[%s] Found %d products on page %d", category, len(products), page)

        for product in products:
            if saved >= target_count:
                break

            image_url = product["image_url"]
            if image_url in existing_urls:
                log.debug("Skipping duplicate: %s", image_url)
                continue

            # Build a safe filename from the image URL
            raw_filename = image_url.split("?")[0].split("/")[-1]
            # Ensure it has an image extension
            if not any(raw_filename.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
                raw_filename += ".jpg"
            dest_path = category_dir / f"{saved + 1:03d}_{raw_filename}"

            log.info("[%s] Downloading image %d/%d: %s", category, saved + 1, target_count, raw_filename)
            result = download_image(session, image_url, dest_path)
            polite_sleep()

            if result is None:
                continue

            width, height = result
            existing_urls.add(image_url)
            saved += 1

            csv_writer.writerow(
                {
                    "product_name": product["name"],
                    "product_url": product["product_url"],
                    "image_url": image_url,
                    "category": category,
                    "image_width": width,
                    "image_height": height,
                    "local_path": str(dest_path.relative_to(PROJECT_ROOT)),
                }
            )

        page += 1

    log.info("[%s] Done — saved %d images", category, saved)
    return saved


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "product_name",
        "product_url",
        "image_url",
        "category",
        "image_width",
        "image_height",
        "local_path",
    ]

    # Track already-downloaded image URLs to avoid duplicates across runs
    existing_urls: set[str] = set()
    append_mode = METADATA_CSV.exists()
    if append_mode:
        with open(METADATA_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing_urls.add(row.get("image_url", ""))

    csv_file = open(METADATA_CSV, "a" if append_mode else "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    if not append_mode:
        writer.writeheader()

    session = requests.Session()
    session.headers.update(HEADERS)

    total = 0
    try:
        for category, path in CATEGORIES.items():
            count = scrape_category(
                session,
                category,
                path,
                IMAGES_PER_CATEGORY,
                writer,
                existing_urls,
            )
            csv_file.flush()
            total += count
            log.info("Progress: %d total images saved so far", total)
    finally:
        csv_file.close()
        session.close()

    log.info("Scraping complete. %d images saved. Metadata: %s", total, METADATA_CSV)


if __name__ == "__main__":
    main()
