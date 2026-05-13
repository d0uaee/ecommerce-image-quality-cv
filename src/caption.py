"""
BLIP image captioning + French product listing generation for Jumia Morocco.

Generates a structured French product listing from a product image and NLP
entities extracted by src.nlp.extract_entities().

Usage
-----
from src.caption import generate_listing
from src.nlp import extract_entities

entities = extract_entities("Samsung Galaxy A54 128Go Noir 2999DH")
result = generate_listing("data/raw_images/electronics/001_1.jpg", entities)

# result = {
#   "caption":     "a black smartphone on a white background",
#   "title":       "Samsung Galaxy A54 - Smartphone Android Noir 128GB",
#   "description": "Samsung Galaxy A54 — 128GB, coloris Noir. ...",
#   "keywords":    ["Samsung", "Galaxy A54", "128GB", "Noir"],
#   "success":     True,
# }
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

from PIL import Image, UnidentifiedImageError

log = logging.getLogger(__name__)

_BLIP_MODEL     = None
_BLIP_PROCESSOR = None
_BLIP_LOAD_ATTEMPTED = False

# ---------------------------------------------------------------------------
# Lazy BLIP loader
# ---------------------------------------------------------------------------

def _load_blip_once():
    """Load and cache BLIP model/processor once per process."""
    global _BLIP_MODEL, _BLIP_PROCESSOR, _BLIP_LOAD_ATTEMPTED

    if _BLIP_MODEL is not None and _BLIP_PROCESSOR is not None:
        return _BLIP_MODEL, _BLIP_PROCESSOR

    if _BLIP_LOAD_ATTEMPTED:
        return None, None

    _BLIP_LOAD_ATTEMPTED = True
    try:
        from transformers import BlipForConditionalGeneration, BlipProcessor
        model_id = "Salesforce/blip-image-captioning-base"
        log.info("Loading BLIP processor...")
        _BLIP_PROCESSOR = BlipProcessor.from_pretrained(model_id, local_files_only=False)
        log.info("Loading BLIP model (may download if incomplete)...")
        _BLIP_MODEL = BlipForConditionalGeneration.from_pretrained(
            model_id, local_files_only=False
        )
        _BLIP_MODEL.eval()
        log.info("BLIP model loaded successfully.")
        return _BLIP_MODEL, _BLIP_PROCESSOR
    except Exception as exc:
        log.error("BLIP model load failed: %s", exc)
        return None, None


# ---------------------------------------------------------------------------
# BLIP inference
# ---------------------------------------------------------------------------

def _run_blip(image_path: Path) -> str | None:
    """Return English caption from BLIP, or None if model is unavailable."""
    model, processor = _load_blip_once()
    if model is None:
        log.warning("BLIP model not available")
        return None
    try:
        import torch
        log.info("Opening image: %s", image_path)
        img = Image.open(image_path).convert("RGB")
        log.info("Image size: %s", img.size)
        log.info("Processing image with BLIP processor...")
        inputs = processor(images=img, return_tensors="pt")
        log.info("Generating caption...")
        with torch.no_grad():
            ids = model.generate(**inputs, max_new_tokens=50)
        caption = processor.decode(ids[0], skip_special_tokens=True).strip()
        log.info("Caption generated: %s", caption)
        return caption
    except Exception as exc:
        log.error("BLIP inference failed: %s", exc)
        import traceback
        log.error(traceback.format_exc())
        return None


# ---------------------------------------------------------------------------
# English → French vocabulary for caption keywords
# ---------------------------------------------------------------------------

_EN_FR: dict[str, str] = {
    # Product types
    "smartphone": "Smartphone",
    "phone":      "Téléphone",
    "laptop":     "Ordinateur portable",
    "computer":   "Ordinateur",
    "tablet":     "Tablette",
    "camera":     "Appareil photo",
    "headphones": "Casque audio",
    "earphones":  "Écouteurs",
    "speaker":    "Enceinte",
    "watch":      "Montre",
    "keyboard":   "Clavier",
    "mouse":      "Souris",
    "monitor":    "Écran",
    "television": "Téléviseur",
    "tv":         "TV",
    "printer":    "Imprimante",
    "charger":    "Chargeur",
    "stand":      "Support",
    "holder":     "Support",
    "mount":      "Support",
    "cable":      "Câble",
    "power":      "Chargeur",
    "bag":        "Sac",
    "shirt":      "Chemise",
    "dress":      "Robe",
    "shoes":      "Chaussures",
    "jacket":     "Veste",
    "refrigerator": "Réfrigérateur",
    "washing":    "Lave-linge",
    "microwave":  "Micro-ondes",
    # Attributes
    "android":   "Android",
    "wireless":  "Sans fil",
    "portable":  "Portable",
    "digital":   "Numérique",
    "electric":  "Électrique",
    # Colors
    "black":  "Noir",
    "white":  "Blanc",
    "blue":   "Bleu",
    "red":    "Rouge",
    "green":  "Vert",
    "silver": "Argenté",
    "gold":   "Doré",
    "gray":   "Gris",
    "grey":   "Gris",
    "pink":   "Rose",
}


_TYPES = {
    "Smartphone", "Téléphone", "Ordinateur portable", "Ordinateur",
    "Tablette", "Appareil photo", "Casque audio", "Écouteurs", "Enceinte",
    "Montre", "Clavier", "Souris", "Écran", "Téléviseur", "TV",
    "Imprimante", "Chargeur", "Support", "Câble", "Sac", "Chemise", "Robe",
    "Chaussures", "Veste", "Réfrigérateur", "Lave-linge", "Micro-ondes",
}
_ATTRS = {"Android", "Sans fil", "Portable", "Numérique", "Électrique"}


def _caption_keywords_fr(caption: str) -> list[str]:
    """Extract French-translated keywords from a BLIP English caption."""
    words = caption.lower().split()
    seen: set[str] = set()
    result: list[str] = []
    for w in words:
        fr = _EN_FR.get(w)
        if fr and fr not in seen:
            result.append(fr)
            seen.add(fr)
    return result


# ---------------------------------------------------------------------------
# Title builder
# ---------------------------------------------------------------------------

def _build_title(entities: dict, caption: str | None) -> str:
    """
    Build French product title, max 80 chars.
    Format: "Brand Model - Type Attribute Color Storage"
    Example: "Samsung Galaxy A54 - Smartphone Android Noir 128GB"
    """
    left_parts: list[str] = []
    if entities.get("brand"):
        left_parts.append(entities["brand"])
    model = entities.get("model", "")
    # Skip model if it looks like a descriptive English phrase (>2 words, no brand)
    # e.g. "rotatable aluminum alloy stand" from a DINO text prompt
    if model and not (len(model.split()) > 2 and not entities.get("brand")):
        left_parts.append(model)

    right_parts: list[str] = []
    if caption:
        kw_fr = _caption_keywords_fr(caption)
        # types (nouns) first, then attributes (adjectives) — correct French order
        # Colors are excluded here: they come from OCR entities, not the image caption
        # (caption may pick up background colors like "white background")
        types  = [k for k in kw_fr if k in _TYPES]
        attrs  = [k for k in kw_fr if k in _ATTRS]
        right_parts = types + attrs

    existing = {p.lower() for p in right_parts}
    if entities.get("storage") and entities["storage"].lower() not in existing:
        right_parts.append(entities["storage"])
    if entities.get("color") and entities["color"].lower() not in existing:
        right_parts.append(entities["color"])

    if left_parts and right_parts:
        title = f"{' '.join(left_parts)} - {' '.join(right_parts)}"
    elif left_parts:
        title = " ".join(left_parts)
    elif right_parts:
        title = " ".join(right_parts)
    else:
        title = "Produit e-commerce"

    if len(title) > 80:
        title = title[:77].rsplit(" ", 1)[0] + "..."

    return title.strip()


# ---------------------------------------------------------------------------
# Description builder
# ---------------------------------------------------------------------------

def _build_description(entities: dict, caption: str | None) -> str:
    """
    Build French product description (3–4 sentences).
    Always ends with "Livraison disponible partout au Maroc."
    """
    sentences: list[str] = []

    name_parts: list[str] = []
    if entities.get("brand"):
        name_parts.append(entities["brand"])
    model = entities.get("model", "")
    if model and not (len(model.split()) > 2 and not entities.get("brand")):
        name_parts.append(model)
    product_name = " ".join(name_parts) if name_parts else None

    specs: list[str] = []
    if entities.get("storage"):
        specs.append(entities["storage"])
    if entities.get("color"):
        specs.append(f"coloris {entities['color']}")

    # Sentence 1 — only if we have a brand/model
    if product_name:
        if specs:
            sentences.append(f"{product_name} — {', '.join(specs)}.")
        else:
            sentences.append(f"{product_name}.")

    # Sentence 2 — product type + attributes from caption (in French, natural)
    if caption:
        kw_fr  = _caption_keywords_fr(caption)
        types  = [k for k in kw_fr if k in _TYPES]
        attrs  = [k for k in kw_fr if k in _ATTRS]
        if types:
            type_str = types[0].lower()
            if attrs:
                sentences.append(
                    f"Ce {type_str} {' '.join(a.lower() for a in attrs)}"
                    f" est idéal pour un usage quotidien."
                )
            else:
                sentences.append(
                    f"Ce {type_str} est de qualité et adapté à un usage quotidien."
                )
        elif attrs:
            sentences.append(
                f"Produit {' '.join(a.lower() for a in attrs)}, pratique au quotidien."
            )

    # Sentence 3 — price if known
    price    = entities.get("price")
    currency = entities.get("currency", "DH")
    if price:
        sentences.append(f"Prix indicatif : {price:.0f} {currency}.")

    # Sentence 4 — fixed closing (always present)
    sentences.append("Livraison disponible partout au Maroc.")

    return " ".join(sentences)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_listing(
    image_path: Union[str, Path],
    entities: dict,
    lang: str = "fr",
) -> dict:
    """
    Generate a French product listing for Jumia Morocco.

    Parameters
    ----------
    image_path : path to the product image
    entities   : dict returned by ``src.nlp.extract_entities()``
    lang       : language code (only "fr" supported for now)

    Returns
    -------
    dict with keys:
        caption     : str       — raw BLIP English caption (empty if unavailable)
        title       : str       — French title, max 80 chars
        description : str       — French description, 3–4 sentences
        keywords    : list[str] — from entities
        success     : bool      — True if BLIP ran successfully
    """
    image_path = Path(image_path)

    if not image_path.exists():
        log.error("Image not found: %s", image_path)
        return {
            "caption":     "",
            "title":       _build_title(entities, None),
            "description": _build_description(entities, None),
            "keywords":    entities.get("keywords", []),
            "success":     False,
        }

    caption = _run_blip(image_path)
    blip_ok = caption is not None

    return {
        "caption":     caption or "",
        "title":       _build_title(entities, caption),
        "description": _build_description(entities, caption),
        "keywords":    entities.get("keywords", []),
        "success":     blip_ok,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m src.caption <image_path>")
        sys.exit(1)

    img_path = Path(sys.argv[1])

    entities: dict = {}
    try:
        from src.ocr import extract_text
        from src.nlp import extract_entities
        ocr = extract_text(img_path)
        if ocr.get("prompt"):
            entities = extract_entities(ocr["prompt"])
            log.info("OCR entities: %s", entities.get("search_query", ""))
    except Exception as exc:
        log.warning("OCR/NLP unavailable (%s) — running without entities", exc)

    result = generate_listing(img_path, entities)

    print(f"\n{'=' * 60}")
    print(f"Caption     : {result['caption'] or '(BLIP unavailable)'}")
    print(f"Title       : {result['title']}")
    print(f"Description : {result['description']}")
    print(f"Keywords    : {result['keywords']}")
    print(f"Success     : {result['success']}")
    print(f"{'=' * 60}")
