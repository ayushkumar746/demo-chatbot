"""
Product images.

Each product gets a locally generated SVG illustration chosen by category and
brand (e.g. a green beer bottle labelled "Heineken"). Images live in
`static/product-images/` and are served by FastAPI at `/static/...`, so no
external image hosting is required. Generate them with
`python generate_product_images.py`.
"""
import re
from pathlib import Path

from app.config import PROJECT_ROOT, settings

STATIC_DIR = PROJECT_ROOT / "static"
STATIC_URL_PREFIX = "/static"
IMAGES_SUBDIR = "product-images"
FALLBACK_IMAGE_NAME = "default"


def slugify(text: str) -> str:
    """Lowercase, hyphen-separated file name for a brand or category."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def image_relative_path(category: str, brand: str) -> Path:
    """Path of a brand image relative to the static directory."""
    return Path(IMAGES_SUBDIR) / slugify(category) / f"{slugify(brand)}.svg"


def category_fallback_path(category: str) -> Path:
    """Generic image for a category, used when a brand has no image."""
    return Path(IMAGES_SUBDIR) / slugify(category) / f"{FALLBACK_IMAGE_NAME}.svg"


def image_url_for(category: str, brand: str) -> str:
    """Absolute URL of the product image, falling back to the category image."""
    relative = image_relative_path(category, brand or "")
    if not (STATIC_DIR / relative).exists():
        relative = category_fallback_path(category)
    return f"{settings.public_base_url.rstrip('/')}{STATIC_URL_PREFIX}/{relative.as_posix()}"
