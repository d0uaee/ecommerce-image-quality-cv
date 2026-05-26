from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_IMAGES_DIR = DATA_DIR / "raw_images"
CLEAN_REFERENCES_DIR = DATA_DIR / "clean_references"
DEGRADED_DIR = DATA_DIR / "degraded"
OUTPUT_DIR = PROJECT_ROOT / "output"
SRC_DIR = PROJECT_ROOT / "src"


ALLOWED_CATEGORIES = (
    "shoes",
    "clothing",
    "portable_electronics",
)


SELECTOR_WEIGHTS = {
    "clip_text_similarity": 0.60,
    "size_centrality": 0.25,
    "category_coherence": 0.15,
}

# Poids du score proxy CLIP (utilisé quand le modèle CLIP n'est pas disponible).
# Centraliser ici pour faciliter la calibration sans toucher au code du selector.
PROXY_WEIGHTS = {
    "color": 0.20,
    "detail": 0.40,
    "center": 0.40,
}


REGION_PROPOSAL_CONFIG = {
    "max_regions": 5,
    "min_region_area_ratio": 0.02,
    "max_region_area_ratio": 0.92,
    "saliency_threshold": 0.45,
    "use_dino": False,
    "dino_model_id": "IDEA-Research/grounding-dino-tiny",
    "dino_box_threshold": 0.25,
    "dino_text_threshold": 0.20,
}


ANALYZER_WEIGHTS = {
    "sharpness": 0.24,
    "exposure": 0.20,
    "contrast": 0.18,
    "color_balance": 0.08,
    "effective_resolution": 0.15,
    "coherence": 0.15,
}


QUALITY_THRESHOLDS = {
    "sharpness": {
        "very_blurry_max": 45.0,
        "soft_max": 110.0,
        "good_min": 220.0,
        "excellent_min": 420.0,
    },
    "exposure": {
        "target_mean": 145.0,
        "tolerance_good": 24.0,
        "tolerance_ok": 46.0,
        "extreme_dark": 58.0,
        "extreme_bright": 220.0,
    },
    "contrast": {
        "flat_max": 22.0,
        "acceptable_min": 30.0,
        "good_min": 44.0,
        "strong_min": 58.0,
    },
    "color_balance": {
        "good_max_delta": 10.0,
        "acceptable_max_delta": 22.0,
        "strong_cast_delta": 38.0,
    },
    "effective_resolution": {
        "min_width": 512,
        "min_height": 512,
        "recommended_width": 1000,
        "recommended_height": 1000,
        "detail_soft_min": 0.035,
        "detail_good_min": 0.085,
    },
    "coherence": {
        "clip_weight": 0.85,
        "color_weight": 0.15,
        "color_match_score": 100.0,
        "color_soft_match_score": 65.0,
        "color_missing_score": 55.0,
    },
}


STREAMLIT_DEFAULTS = {
    "page_title": "E-commerce Image Quality",
    "layout": "wide",
}
