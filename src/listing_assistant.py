from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from io import BytesIO
from typing import Any
from urllib import error as urlerror
from urllib import request

import cv2
import numpy as np
from PIL import Image

from config import ASSISTANT_CONFIG
from src.candidate_region_generator import propose_regions, refine_crop
from src.dictionaries import EMBEDDING_VECTOR_SIZE, FRENCH_COLOR_TO_RGB
from src.text_processor import encode_image_embedding, process_text


@dataclass(frozen=True)
class ProductPrototype:
    key: str
    category: str
    prompt: str
    title_fr: str
    description_fr: str
    attributes: tuple[str, ...]
    missing_info: tuple[str, ...]
    price_hint: tuple[int, int]


PRODUCT_PROTOTYPES: tuple[ProductPrototype, ...] = (
    ProductPrototype(
        key="sneakers",
        category="shoes",
        prompt="chaussures sneakers mode",
        title_fr="Sneakers {color} style urbain",
        description_fr="Paire de sneakers {color} au style polyvalent, adaptee a un usage quotidien avec une silhouette moderne et facile a porter.",
        attributes=("style urbain", "usage quotidien", "forme basse"),
        missing_info=("taille exacte", "etat du produit", "matiere principale"),
        price_hint=(250, 650),
    ),
    ProductPrototype(
        key="heels",
        category="shoes",
        prompt="chaussures a talons elegantes",
        title_fr="Chaussures a talons {color} elegantes",
        description_fr="Chaussures a talons {color} au rendu habille, adaptees aux tenues de sortie ou evenements avec une ligne feminine marquee.",
        attributes=("style habille", "talon visible", "silhouette feminine"),
        missing_info=("hauteur du talon", "pointure", "etat de la semelle"),
        price_hint=(300, 850),
    ),
    ProductPrototype(
        key="boots",
        category="shoes",
        prompt="bottines ou bottes mode",
        title_fr="Bottines {color} look structure",
        description_fr="Bottines {color} au look structure, faciles a integrer dans une tenue casual ou habillee selon le style du vendeur.",
        attributes=("forme montante", "look structure", "usage ville"),
        missing_info=("pointure", "matiere", "fermeture"),
        price_hint=(320, 900),
    ),
    ProductPrototype(
        key="dress",
        category="clothing",
        prompt="robe femme elegante",
        title_fr="Robe {color} coupe elegante",
        description_fr="Robe {color} a la coupe elegante, pensee pour un rendu soigné et un port confortable au quotidien ou en sortie.",
        attributes=("coupe feminine", "tenue habillee", "style elegant"),
        missing_info=("taille", "matiere", "longueur"),
        price_hint=(220, 700),
    ),
    ProductPrototype(
        key="jacket",
        category="clothing",
        prompt="veste ou manteau mode",
        title_fr="Veste {color} style moderne",
        description_fr="Veste {color} au style moderne, pratique pour completer une tenue avec une piece visuellement forte et facile a assortir.",
        attributes=("piece exterieure", "style moderne", "coupe structurée"),
        missing_info=("taille", "matiere", "saison d'usage"),
        price_hint=(280, 950),
    ),
    ProductPrototype(
        key="top",
        category="clothing",
        prompt="haut vetement blouse ou pull",
        title_fr="Haut {color} style polyvalent",
        description_fr="Haut {color} au style polyvalent, adapte a une utilisation quotidienne avec une coupe simple et facile a associer.",
        attributes=("usage quotidien", "style polyvalent", "coupe simple"),
        missing_info=("taille", "matiere", "coupe exacte"),
        price_hint=(120, 400),
    ),
    ProductPrototype(
        key="earbuds",
        category="portable_electronics",
        prompt="ecouteurs sans fil portables",
        title_fr="Ecouteurs {color} format compact",
        description_fr="Ecouteurs {color} au format compact, penses pour un usage mobile avec un design moderne et facile a transporter.",
        attributes=("format compact", "usage mobile", "design moderne"),
        missing_info=("marque", "autonomie", "connectivite"),
        price_hint=(180, 900),
    ),
    ProductPrototype(
        key="charger",
        category="portable_electronics",
        prompt="chargeur portable ou power bank",
        title_fr="Chargeur portable {color} format pratique",
        description_fr="Chargeur portable {color} au format pratique, adapte a un usage quotidien pour accompagner les besoins de recharge mobile.",
        attributes=("portable", "usage quotidien", "format pratique"),
        missing_info=("capacite", "puissance", "ports disponibles"),
        price_hint=(150, 650),
    ),
    ProductPrototype(
        key="smartwatch",
        category="portable_electronics",
        prompt="montre connectee portable",
        title_fr="Montre connectee {color} look moderne",
        description_fr="Montre connectee {color} au look moderne, pensee pour un usage quotidien avec une presentation nette et technologique.",
        attributes=("wearable", "look moderne", "usage quotidien"),
        missing_info=("marque", "taille de l'ecran", "etat de la batterie"),
        price_hint=(260, 1200),
    ),
)


def _normalize_image(image_rgb: np.ndarray) -> np.ndarray:
    array = np.asarray(image_rgb, dtype=np.uint8)
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError("L'image fournie a l'assistant doit etre un tableau RGB HxWx3.")
    return array


def _rgb_to_base64_jpeg(image_rgb: np.ndarray) -> str:
    image = Image.fromarray(image_rgb)
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=92)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _truncate_sentence(text: str, max_chars: int = 180) -> str:
    clean = " ".join(str(text or "").split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip(" ,;:-") + "…"


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float32).reshape(-1)
    b = np.asarray(b, dtype=np.float32).reshape(-1)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _closest_color_name(image_rgb: np.ndarray) -> str:
    rgb_mean = image_rgb.mean(axis=(0, 1)).astype(np.float32)
    best_name = "gris"
    best_distance = float("inf")
    for name, rgb in FRENCH_COLOR_TO_RGB.items():
        distance = float(np.linalg.norm(rgb_mean - np.array(rgb, dtype=np.float32)))
        if distance < best_distance:
            best_name = name
            best_distance = distance
    return best_name


def _detect_listing_subtype(hints: str, category: str) -> str | None:
    hint = hints.lower()
    mapping = {
        "shoes": {
            "talon": "chaussures a talons",
            "escarpin": "escarpins",
            "bott": "bottines",
            "sandale": "sandales",
            "sneaker": "sneakers",
            "basket": "baskets",
        },
        "clothing": {
            "veste": "veste",
            "robe": "robe",
            "chemise": "chemise",
            "pull": "pull",
            "collant": "collants",
            "pantalon": "pantalon",
            "jupe": "jupe",
        },
        "portable_electronics": {
            "chargeur": "chargeur portable",
            "power bank": "power bank",
            "ecouteur": "ecouteurs",
            "earbuds": "ecouteurs",
            "montre": "montre connectee",
            "smartwatch": "montre connectee",
            "casque": "casque audio",
        },
    }
    for needle, subtype in mapping.get(category, {}).items():
        if needle in hint:
            return subtype
    return None


def _build_prompt_contract(seller_hints: str) -> dict[str, Any]:
    return {
        "instruction": (
            "Analyser l'image produit et generer une sortie JSON stricte pour une fiche e-commerce. "
            "Ne pas inventer la marque. Garder un style vendeur simple, naturel et prudent. "
            "La categorie doit etre une de shoes, clothing, portable_electronics."
        ),
        "seller_hints": seller_hints,
        "response_schema": {
            "title": "string",
            "description": "string",
            "category": "string",
            "attributes": ["string"],
            "seller_recommendations": {
                "missing_info": ["string"],
                "listing_checklist": ["string"],
                "price_hint": {
                    "currency": "string",
                    "min": "number|null",
                    "max": "number|null",
                    "note": "string",
                },
            },
        },
    }


def _select_crop(image_rgb: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    image_bgr = image_rgb[:, :, ::-1]
    regions = propose_regions(image_bgr)
    bbox = regions[0]["bbox"] if regions else (0, 0, image_rgb.shape[1], image_rgb.shape[0])
    refined = refine_crop(image_bgr, bbox)
    crop_bgr = refined["crop"]
    crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    return crop_rgb, tuple(int(v) for v in refined["bbox"])


def _best_prototype(image_rgb: np.ndarray, seller_hints: str) -> ProductPrototype:
    image_embedding = encode_image_embedding(image_rgb)
    hint_data = process_text(seller_hints, seller_hints) if seller_hints.strip() else None
    hinted_category = hint_data.get("category") if hint_data else None
    best_proto = PRODUCT_PROTOTYPES[0]
    best_score = -1.0
    for prototype in PRODUCT_PROTOTYPES:
        if hinted_category and prototype.category != hinted_category:
            continue
        prompt = prototype.prompt
        if seller_hints.strip():
            prompt = f"{prompt} {seller_hints}"
        text_embedding = process_text(prompt, prompt)["text_embedding"]
        score = _cosine(image_embedding, text_embedding)
        if score > best_score:
            best_score = score
            best_proto = prototype
    if best_score < 0.0 and hinted_category:
        for prototype in PRODUCT_PROTOTYPES:
            if prototype.category == hinted_category:
                return prototype
    return best_proto


def _build_local_payload(image_rgb: np.ndarray, seller_hints: str = "") -> dict[str, Any]:
    crop_rgb, bbox = _select_crop(image_rgb)
    prototype = _best_prototype(crop_rgb, seller_hints)
    hint_data = process_text(seller_hints, seller_hints) if seller_hints.strip() else {}
    color = hint_data.get("color") or _closest_color_name(crop_rgb)
    hints_text = seller_hints.strip()
    subtype = _detect_listing_subtype(hints_text, hint_data.get("category") or prototype.category)
    title = prototype.title_fr.format(color=color)
    if hints_text:
        title = hints_text[:90].strip().rstrip(".")
    elif subtype:
        title = f"{subtype.capitalize()} {color}"

    description = prototype.description_fr.format(color=color)
    if subtype:
        description = description.replace("Haut", subtype.capitalize()).replace("Chaussures a talons", subtype.capitalize())
    if hints_text:
        description = f"{description} Informations vendeur a verifier: {_truncate_sentence(hints_text, 120)}."

    attributes = list(prototype.attributes) + [f"couleur percue: {color}", f"categorie estimee: {prototype.category}"]
    missing_info = list(prototype.missing_info)
    checklist = [
        "Verifier que la marque est mentionnee si elle est connue.",
        "Ajouter les dimensions, la taille ou la capacite selon le produit.",
        "Confirmer l'etat du produit et la presence d'accessoires si necessaire.",
    ]

    return {
        "source": "local_assistant",
        "crop_bbox": list(bbox),
        "category": hint_data.get("category") or prototype.category,
        "title": title,
        "description": _truncate_sentence(description, 320),
        "attributes": attributes,
        "seller_recommendations": {
            "missing_info": missing_info,
            "listing_checklist": checklist,
            "price_hint": {
                "currency": ASSISTANT_CONFIG["default_currency"],
                "min": prototype.price_hint[0],
                "max": prototype.price_hint[1],
                "note": "Estimation prudente basee sur la categorie visuelle. A confirmer avec la marque, l'etat et les specifications exactes.",
            },
        },
    }


def _call_n8n_webhook(image_rgb: np.ndarray, seller_hints: str = "") -> dict[str, Any] | None:
    webhook_url = ASSISTANT_CONFIG["n8n_webhook_url"]
    if not ASSISTANT_CONFIG["enable_n8n"] or not webhook_url:
        return None

    payload = {
        "image_base64_jpeg": _rgb_to_base64_jpeg(image_rgb),
        "seller_hints": seller_hints,
        "schema_version": ASSISTANT_CONFIG["webhook_schema_version"],
        "contract": _build_prompt_contract(seller_hints),
        "requested_fields": [
            "title",
            "description",
            "category",
            "attributes",
            "seller_recommendations",
        ],
    }
    headers = {"Content-Type": "application/json"}
    auth_token = ASSISTANT_CONFIG["n8n_auth_token"]
    auth_header = ASSISTANT_CONFIG["n8n_auth_header"]
    if auth_token and auth_header:
        headers[auth_header] = auth_token
    req = request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=ASSISTANT_CONFIG["request_timeout_seconds"]) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urlerror.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None

    if not isinstance(data, dict):
        return None
    return _normalize_external_payload(data, seller_hints=seller_hints)


def _normalize_external_payload(payload: dict[str, Any], seller_hints: str = "") -> dict[str, Any] | None:
    title = str(payload.get("title", "") or "").strip()
    description = str(payload.get("description", "") or "").strip()
    category = str(payload.get("category", "") or "").strip()
    if not title or not description:
        return None
    if category not in {"shoes", "clothing", "portable_electronics"}:
        category = process_text(seller_hints, seller_hints).get("category") or "clothing"

    seller = payload.get("seller_recommendations", {})
    price_hint = seller.get("price_hint", {}) if isinstance(seller, dict) else {}
    normalized = {
        "source": "n8n_webhook",
        "category": category,
        "title": _truncate_sentence(title, 100),
        "description": _truncate_sentence(description, 360),
        "attributes": [str(item) for item in payload.get("attributes", [])][:8],
        "seller_recommendations": {
            "missing_info": [str(item) for item in seller.get("missing_info", [])][:8] if isinstance(seller, dict) else [],
            "listing_checklist": [str(item) for item in seller.get("listing_checklist", [])][:8] if isinstance(seller, dict) else [],
            "price_hint": {
                "currency": str(price_hint.get("currency", ASSISTANT_CONFIG["default_currency"])),
                "min": price_hint.get("min"),
                "max": price_hint.get("max"),
                "note": str(
                    price_hint.get(
                        "note",
                        "Estimation a confirmer selon la marque, l'etat et les specifications exactes.",
                    )
                ),
            },
        },
    }
    return normalized


def generate_listing_assistance(image_rgb: np.ndarray, seller_hints: str = "") -> dict[str, Any]:
    image_rgb = _normalize_image(image_rgb)
    webhook_payload = _call_n8n_webhook(image_rgb, seller_hints=seller_hints)
    if webhook_payload is not None:
        return webhook_payload
    return _build_local_payload(image_rgb, seller_hints=seller_hints)
