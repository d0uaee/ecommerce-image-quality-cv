from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

project = "E-commerce Image Quality"
author = "Projet PFE"
copyright = f"{datetime.now():%Y}, {author}"
release = "1.0"

extensions = [
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "fr"

html_theme = "furo"
html_title = "E-commerce Image Quality"
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/example/ecommerce-image-quality/",
    "source_branch": "main",
    "source_directory": "docs/",
}

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
]

nitpicky = False
