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


QUALITY_THRESHOLDS = {
    "sharpness": {
        "poor_max": 80.0,
        "acceptable_min": 80.0,
        "good_min": 160.0,
    },
    "exposure": {
        "underexposed_max": 70.0,
        "overexposed_min": 185.0,
        "target_min": 95.0,
        "target_max": 170.0,
    },
    "contrast": {
        "poor_max": 25.0,
        "good_min": 45.0,
    },
    "color_consistency": {
        "max_cast_delta": 18.0,
    },
    "resolution": {
        "min_width": 512,
        "min_height": 512,
        "recommended_width": 1000,
        "recommended_height": 1000,
    },
    "clip_coherence": {
        "poor_max": 0.18,
        "good_min": 0.28,
    },
}


STREAMLIT_DEFAULTS = {
    "page_title": "E-commerce Image Quality",
    "layout": "wide",
}
