from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

import numpy as np

try:
    from rapidfuzz import fuzz, process
except Exception:
    fuzz = None
    process = None

from src.dictionaries import (
    ALL_BRANDS,
    BRANDS,
    CATEGORY_KEYWORDS,
    COLOR_ALIASES,
    EMBEDDING_VECTOR_SIZE,
)


_SPACY_NLP = None
_SPACY_LOAD_ATTEMPTED = False
_EMBEDDING_MODEL = None
_EMBEDDING_LOAD_ATTEMPTED = False


def _normalize(text: str) -> str:
    lowered = text.lower().strip()
    normalized = unicodedata.normalize("NFKD", lowered)
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    ascii_text = re.sub(r"[^a-z0-9\s\-/+]", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def _load_spacy_model():
    global _SPACY_NLP, _SPACY_LOAD_ATTEMPTED
    if _SPACY_NLP is not None:
        return _SPACY_NLP
    if _SPACY_LOAD_ATTEMPTED:
        return None

    _SPACY_LOAD_ATTEMPTED = True
    try:
        import spacy

        _SPACY_NLP = spacy.load("fr_core_news_md")
    except Exception:
        _SPACY_NLP = None
    return _SPACY_NLP


def _load_embedding_model():
    global _EMBEDDING_MODEL, _EMBEDDING_LOAD_ATTEMPTED
    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL
    if _EMBEDDING_LOAD_ATTEMPTED:
        return None

    _EMBEDDING_LOAD_ATTEMPTED = True
    try:
        from sentence_transformers import SentenceTransformer

        _EMBEDDING_MODEL = SentenceTransformer(
            "sentence-transformers/clip-ViT-B-32-multilingual-v1"
        )
    except Exception:
        _EMBEDDING_MODEL = None
    return _EMBEDDING_MODEL


def _tokenize(text: str) -> list[str]:
    nlp = _load_spacy_model()
    if nlp is None:
        return _normalize(text).split()

    doc = nlp(text)
    return [token.lemma_.lower().strip() for token in doc if not token.is_space and not token.is_punct]


def _fuzzy_best_match(query: str, candidates: list[str], min_score: int = 86) -> str | None:
    if not query:
        return None
    if process is not None and fuzz is not None:
        result = process.extractOne(query, candidates, scorer=fuzz.WRatio)
        if result is None:
            return None
        value, score, *_ = result
        return value if score >= min_score else None

    best_value = None
    best_score = 0.0
    for candidate in candidates:
        score = SequenceMatcher(None, query, candidate).ratio() * 100.0
        if score > best_score:
            best_value = candidate
            best_score = score
    return best_value if best_score >= min_score else None


def _extract_brand(clean_text: str) -> str | None:
    tokens = clean_text.split()
    windows: list[str] = []
    for size in range(1, 4):
        for index in range(0, max(0, len(tokens) - size + 1)):
            windows.append(" ".join(tokens[index : index + size]))

    direct = _fuzzy_best_match(clean_text, [brand.lower() for brand in ALL_BRANDS], min_score=91)
    if direct is not None:
        return next(brand for brand in ALL_BRANDS if brand.lower() == direct)

    for window in windows:
        matched = _fuzzy_best_match(window, [brand.lower() for brand in ALL_BRANDS], min_score=88)
        if matched is not None:
            return next(brand for brand in ALL_BRANDS if brand.lower() == matched)
    return None


def _extract_color(clean_text: str) -> str | None:
    for canonical, aliases in COLOR_ALIASES.items():
        for alias in aliases:
            if re.search(rf"\b{re.escape(_normalize(alias))}\b", clean_text):
                return canonical

    joined_aliases = {
        alias: canonical
        for canonical, aliases in COLOR_ALIASES.items()
        for alias in aliases
    }
    best = _fuzzy_best_match(clean_text, list(joined_aliases.keys()), min_score=89)
    if best is None:
        return None
    return joined_aliases[best]


def _extract_category(clean_text: str, brand: str | None) -> str | None:
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            normalized_keyword = _normalize(keyword)
            if normalized_keyword in clean_text:
                score += 30
            else:
                fuzzy_match = _fuzzy_best_match(clean_text, [normalized_keyword], min_score=90)
                if fuzzy_match is not None:
                    score += 18
        if brand and brand in BRANDS.get(category, []):
            score += 12
        scores[category] = score

    best_category = max(scores, key=scores.get)
    return best_category if scores[best_category] > 0 else None


@lru_cache(maxsize=2048)
def _embed_cached(clean_text: str) -> np.ndarray:
    model = _load_embedding_model()
    if model is None:
        return np.zeros(EMBEDDING_VECTOR_SIZE, dtype=np.float32)

    try:
        vector = model.encode(clean_text, convert_to_numpy=True, normalize_embeddings=True)
    except Exception:
        return np.zeros(EMBEDDING_VECTOR_SIZE, dtype=np.float32)

    array = np.asarray(vector, dtype=np.float32).reshape(-1)
    if array.size == EMBEDDING_VECTOR_SIZE:
        return array
    if array.size > EMBEDDING_VECTOR_SIZE:
        return array[:EMBEDDING_VECTOR_SIZE]

    padded = np.zeros(EMBEDDING_VECTOR_SIZE, dtype=np.float32)
    padded[: array.size] = array
    return padded


def process_text(title: str, description: str) -> dict[str, Any]:
    title = title or ""
    description = description or ""
    raw_text = f"{title} {description}".strip()
    clean_text = _normalize(raw_text)

    _ = _tokenize(raw_text)
    brand = _extract_brand(clean_text)
    color = _extract_color(clean_text)
    category = _extract_category(clean_text, brand)
    text_embedding = _embed_cached(clean_text).copy()

    return {
        "clean_text": clean_text,
        "color": color,
        "category": category,
        "brand": brand,
        "text_embedding": text_embedding,
    }


if __name__ == "__main__":
    sample = process_text(
        "Nike Air Max homme noir",
        "Chaussures de running confortables en mesh avec semelle visible.",
    )
    print("clean_text:", sample["clean_text"])
    print("color:", sample["color"])
    print("category:", sample["category"])
    print("brand:", sample["brand"])
    print("embedding_shape:", sample["text_embedding"].shape)
