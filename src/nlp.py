"""
Structured product entity extraction from OCR text.

Extracts brand, model, color, price, and generates search keywords
from unstructured product descriptions (e.g., from EasyOCR on product images).

Usage
-----
from src.nlp import extract_entities

entities = extract_entities("Samsung Galaxy A54 128Go Noir 2999DH")
print(entities)
# {
#   "brand": "Samsung",
#   "model": "Galaxy A54",
#   "color": "Noir",
#   "price": 2999.0,
#   "currency": "DH",
#   "keywords": ["Samsung", "Galaxy A54", "Noir"],
#   "search_query": "Samsung Galaxy A54 Noir"
# }
"""

import logging
import re
from typing import Optional

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known brands (Moroccan e-commerce + international)
# ---------------------------------------------------------------------------

KNOWN_BRANDS = {
    # Electronics
    "Samsung", "Apple", "LG", "Sony", "Philips", "Panasonic", "Toshiba",
    "Huawei", "Xiaomi", "Oppo", "Vivo", "Realme", "OnePlus", "Motorola",
    "Lenovo", "HP", "Asus", "Dell", "Acer", "Canon", "Nikon", "Sony",
    
    # Home Appliances (Ariston, Indesit popular in Morocco)
    "Ariston", "Indesit", "Bosch", "Siemens", "Electrolux", "Whirlpool",
    "AEG", "Beko", "Haier", "Midea", "TCL", "Zanussi",
    
    # Fashion
    "Nike", "Adidas", "Puma", "Reebok", "New Balance", "Converse",
    "Zara", "H&M", "Forever 21", "ASOS", "Uniqlo", "Gap",
    
    # Accessories & Other
    "JBL", "Bose", "Beats", "Anker", "Baseus", "DJI",
}

# ---------------------------------------------------------------------------
# Color patterns (French + English, case-insensitive)
# ---------------------------------------------------------------------------

COLOR_PATTERNS = {
    "Noir": ["noir", "black", "noir", "sombre"],
    "Blanc": ["blanc", "white", "blanche"],
    "Rouge": ["rouge", "red"],
    "Bleu": ["bleu", "blue", "bleue"],
    "Vert": ["vert", "green", "verte"],
    "Rose": ["rose", "pink"],
    "Gris": ["gris", "gray", "grey"],
    "Jaune": ["jaune", "yellow"],
    "Orange": ["orange"],
    "Marron": ["marron", "brown"],
    "Beige": ["beige"],
    "Doré": ["dore", "golden", "or"],
    "Argenté": ["argente", "silver"],
    "Violet": ["violet", "purple"],
}

# Flattened list for regex: all color names
COLOR_NAMES = [
    "noir", "black", "blanc", "white", "rouge", "red",
    "bleu", "blue", "vert", "green", "rose", "pink",
    "gris", "gray", "grey", "jaune", "yellow", "orange",
    "marron", "brown", "beige", "dore", "golden", "or",
    "argente", "silver", "violet", "purple", "blanche", "verte",
]

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Price patterns - try multiple formats in order of specificity
# Pattern 1: Number followed by currency code (DH, MAD, EUR, USD, etc.)
PRICE_PATTERN_1 = re.compile(r'(\d+(?:[.,]\d+)?)\s*(DH|MAD|DHS|EUR|USD)', re.IGNORECASE)
# Pattern 2: Currency symbol followed by number (€1299, $99)
PRICE_PATTERN_2 = re.compile(r'(€|\$)\s*(\d+(?:[.,]\d+)?)', re.IGNORECASE)

# Currency markers
CURRENCY_MAP = {
    "dh": "DH",
    "dhs": "DH",
    "mad": "MAD",
    "€": "EUR",
    "$": "USD",
    "usd": "USD",
    "eur": "EUR",
}

# Memory/Storage sizes (GB, Go, TB, etc.)
STORAGE_PATTERN = re.compile(r'(\d+)\s*(GB|Go|TB|Mo|Mb|b)', re.IGNORECASE)

# Alphanumeric model identifier (after brand name)
MODEL_PATTERN = re.compile(r'([A-Za-z0-9\-\s]+?)(?:\s+(?:' + '|'.join(COLOR_NAMES) + r'))', re.IGNORECASE)

# ---------------------------------------------------------------------------
# Entity extraction
# ---------------------------------------------------------------------------

def extract_brand(text: str) -> Optional[str]:
    """
    Extract brand name from text.
    Matches known brands (case-insensitive, whole word).
    """
    if not text:
        return None
    
    text_lower = text.lower()
    for brand in KNOWN_BRANDS:
        # Try whole-word match first
        if re.search(r'\b' + re.escape(brand.lower()) + r'\b', text_lower):
            return brand
    
    return None


def extract_color(text: str) -> Optional[str]:
    """
    Extract color from text.
    Returns the canonical French color name if found.
    """
    if not text:
        return None
    
    text_lower = text.lower()
    for canonical, aliases in COLOR_PATTERNS.items():
        for alias in aliases:
            if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                return canonical
    
    return None


def extract_price(text: str) -> tuple[Optional[float], Optional[str]]:
    """
    Extract price and currency from text.
    Tries patterns in order: "2999DH", "€1299", "$379".
    Returns (price_float, currency_code) or (None, None).
    """
    if not text:
        return None, None
    
    # Try pattern 1: number followed by currency code
    match = PRICE_PATTERN_1.search(text)
    if match:
        price_str = match.group(1)
        currency_raw = match.group(2).lower()
    else:
        # Try pattern 2: currency symbol before number
        match = PRICE_PATTERN_2.search(text)
        if match:
            symbol = match.group(1)
            price_str = match.group(2)
            currency_raw = "€" if symbol == "€" else "$"
        else:
            return None, None
    
    # Normalize price
    price_str = price_str.replace(',', '.')
    try:
        price = float(price_str)
    except ValueError:
        return None, None
    
    # Normalize currency
    currency = CURRENCY_MAP.get(currency_raw, currency_raw.upper() if currency_raw else "DH")
    if not currency:
        currency = "DH"
    
    return price, currency


def extract_storage(text: str) -> Optional[str]:
    """
    Extract storage capacity from text (e.g., "128Go" → "128GB").
    Returns normalized storage string or None.
    """
    if not text:
        return None
    
    match = STORAGE_PATTERN.search(text)
    if not match:
        return None
    
    size = match.group(1)
    unit = match.group(2).upper()
    
    # Normalize unit
    if unit in ("GO", "GB"):
        return f"{size}GB"
    elif unit == "TB":
        return f"{size}TB"
    elif unit in ("MO", "MB", "M"):
        return f"{size}MB"
    
    return None


def extract_model(text: str, brand: Optional[str] = None) -> Optional[str]:
    """
    Extract model name from text.
    If brand is provided, tries to find model after brand name.
    Otherwise, extracts first alphanumeric sequence that looks like a model.
    """
    if not text:
        return None
    
    # Remove brand from text to isolate model
    model_text = text
    if brand:
        # Remove brand occurrence from text
        model_text = re.sub(r'\b' + re.escape(brand) + r'\b', '', text, flags=re.IGNORECASE).strip()
    
    # Extract first sequence of alphanumerics that includes letters or numbers
    # Stop at colors, price patterns, or end of string
    pattern = r'([A-Za-z0-9\-\s]+?)(?:\s+(?:' + '|'.join(COLOR_NAMES) + r')|(?:\d+(?:DH|MAD|€|$))|$)'
    match = re.search(pattern, model_text, re.IGNORECASE)
    
    if match:
        model = match.group(1).strip()
        # Filter out single words that are likely colors, brands, or stopwords
        if model and len(model) > 1:
            return model
    
    return None


def generate_keywords(brand: Optional[str], model: Optional[str], 
                     color: Optional[str], storage: Optional[str] = None) -> list[str]:
    """
    Generate search keywords from extracted entities.
    Returns list of 3-5 keywords in priority order.
    """
    keywords = []
    
    if brand:
        keywords.append(brand)
    if model:
        keywords.append(model)
    if storage:
        keywords.append(storage)
    if color:
        keywords.append(color)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen:
            unique_keywords.append(kw)
            seen.add(kw_lower)
    
    return unique_keywords[:5]  # Return top 5


def generate_search_query(keywords: list[str], brand: Optional[str] = None) -> str:
    """
    Generate optimized search query from keywords.
    Format: "Brand Model Storage Color"
    """
    if not keywords and not brand:
        return ""
    
    # Prioritize: brand, model, storage, color
    query_parts = []
    
    if brand:
        query_parts.append(brand)
    
    query_parts.extend(keywords)
    
    # Deduplicate
    seen = set()
    final_query = []
    for part in query_parts:
        part_lower = part.lower()
        if part_lower not in seen:
            final_query.append(part)
            seen.add(part_lower)
    
    return " ".join(final_query).strip()


def extract_entities(text: str) -> dict:
    """
    Extract all product entities from OCR text.
    
    Parameters
    ----------
    text : str
        Raw text from OCR (e.g., "Samsung Galaxy A54 128Go Noir 2999DH")
    
    Returns
    -------
    dict with keys:
        - brand: str or None
        - model: str or None
        - color: str or None
        - storage: str or None
        - price: float or None
        - currency: str or None
        - keywords: list[str]
        - search_query: str
    """
    if not text or not isinstance(text, str):
        return {
            "brand": None,
            "model": None,
            "color": None,
            "storage": None,
            "price": None,
            "currency": None,
            "keywords": [],
            "search_query": "",
        }
    
    text = text.strip()
    
    # Extract entities in order
    brand = extract_brand(text)
    color = extract_color(text)
    storage = extract_storage(text)
    price, currency = extract_price(text)
    model = extract_model(text, brand=brand)
    
    # Generate keywords and search query
    keywords = generate_keywords(brand, model, color, storage)
    search_query = generate_search_query(keywords, brand=brand)
    
    return {
        "brand": brand,
        "model": model,
        "color": color,
        "storage": storage,
        "price": price,
        "currency": currency,
        "keywords": keywords,
        "search_query": search_query,
    }


# ---------------------------------------------------------------------------
# CLI / Tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    
    test_cases = [
        "Samsung Galaxy A54 128Go Noir 2999DH",
        "Apple iPhone 15 Pro 256GB Silver €1299",
        "Nike Air Max 90 Noir Blanc 599DH",
        "Ariston Lave-linge 7kg Blanc 3500MAD",
        "Zara Robe Bleu Ciel M 299DH",
        "Sony WH-1000XM5 Gris €379",
        "LG OLED 55 inch Noir 15000DH",
    ]
    
    print("\n" + "=" * 80)
    print("PRODUCT ENTITY EXTRACTION TEST")
    print("=" * 80)
    
    for text in test_cases:
        entities = extract_entities(text)
        print(f"\nInput: {text}")
        print(f"Entities:")
        for key, value in entities.items():
            if key != "keywords":
                print(f"  {key:<15} = {value}")
            else:
                print(f"  {key:<15} = {value}")
        print(f"  search_query    = '{entities['search_query']}'")
