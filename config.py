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


ANALYZER_WEIGHTS = {
    "sharpness": 0.28,
    "exposure": 0.22,
    "contrast": 0.20,
    "color_balance": 0.08,
    "effective_resolution": 0.22,
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
}


STREAMLIT_DEFAULTS = {
    "page_title": "E-commerce Image Quality",
    "layout": "wide",
}
