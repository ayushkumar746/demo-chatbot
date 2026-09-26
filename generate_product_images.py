"""
Generate product illustrations (SVG) for every category/brand in the catalog.

Each image shows a category-specific container (bottle, can, carton, wine
bottle, ...) in the brand's colour with the brand name on the label. Output
goes to `static/product-images/<category>/<brand>.svg`, plus a
`default.svg` per category. Safe to re-run; files are overwritten.

Usage:
    python generate_product_images.py
"""
from html import escape

from app.services.product_images import (
    STATIC_DIR,
    category_fallback_path,
    image_relative_path,
)
from app.services.vector_store import load_catalog

SIZE = 256

# Brand colours: (primary, label text colour)
BRAND_COLORS = {
    "coca cola": ("#E61D2B", "#FFFFFF"), "pepsi": ("#004B93", "#FFFFFF"), "sprite": ("#0A8A3E", "#FFE600"),
    "thums up": ("#1B2A6B", "#FFFFFF"), "fanta": ("#FF8200", "#FFFFFF"), "mountain dew": ("#6CB33F", "#FFFFFF"),
    "7up": ("#00A94F", "#FFFFFF"), "mirinda": ("#F57C00", "#FFFFFF"), "limca": ("#9ACD32", "#1B5E20"),
    "campa": ("#B71C1C", "#FFFFFF"), "bovonto": ("#6A1B9A", "#FFFFFF"), "duke's": ("#0277BD", "#FFFFFF"),
    "appy fizz": ("#C62828", "#FFD54F"), "schweppes": ("#F9A825", "#1A237E"),
    "sting": ("#D50000", "#FFEB3B"), "red bull": ("#1E3A8A", "#FFC107"), "monster": ("#111111", "#76FF03"),
    "hell": ("#212121", "#FF5252"), "charged": ("#263238", "#FFD600"), "gatorade": ("#FF6D00", "#FFFFFF"),
    "maaza": ("#F9A825", "#1B5E20"), "slice": ("#FFB300", "#B71C1C"), "frooti": ("#43A047", "#FFEB3B"),
    "real": ("#EF6C00", "#FFFFFF"), "tropicana": ("#FB8C00", "#2E7D32"), "paper boat": ("#8D6E63", "#FFFFFF"),
    "b natural": ("#7CB342", "#FFFFFF"), "minute maid": ("#FFA000", "#1B5E20"), "appy": ("#C62828", "#FFFFFF"),
    "kinley": ("#0288D1", "#FFFFFF"), "bisleri": ("#00897B", "#FFFFFF"), "aquafina": ("#1565C0", "#FFFFFF"),
    "bailley": ("#0097A7", "#FFFFFF"), "himalayan": ("#5C6BC0", "#FFFFFF"),
    "kingfisher": ("#C62828", "#FFFFFF"), "budweiser": ("#B71C1C", "#FFFFFF"), "heineken": ("#1B7F3B", "#FFFFFF"),
    "tuborg": ("#2E7D32", "#FFFFFF"), "carlsberg": ("#1B5E20", "#FFFFFF"), "corona": ("#F9A825", "#0D47A1"),
    "bira 91": ("#FDD835", "#212121"), "hoegaarden": ("#E3F2FD", "#0D47A1"), "simba": ("#F57F17", "#FFFFFF"),
    "godfather": ("#3E2723", "#FFD54F"), "haywards 5000": ("#6D4C41", "#FFFFFF"),
    "knock out": ("#212121", "#FFC107"), "stella artois": ("#B71C1C", "#FFD54F"),
    "sula": ("#6A1B4D", "#FFFFFF"), "grover zampa": ("#4A148C", "#FFFFFF"), "fratelli": ("#880E4F", "#FFFFFF"),
    "york": ("#5D4037", "#FFFFFF"), "jacob's creek": ("#7B1FA2", "#FFFFFF"), "big banyan": ("#33691E", "#FFFFFF"),
    "four seasons": ("#AD1457", "#FFFFFF"), "nine hills": ("#4E342E", "#FFFFFF"),
    "lays": ("#FDD835", "#C62828"), "kurkure": ("#FF6F00", "#FFFFFF"),
}
CATEGORY_COLORS = {
    "cold_drink": "#E53935", "energy_drink": "#1E88E5", "fruit_drink": "#FB8C00",
    "water": "#29B6F6", "beer": "#F9A825", "wine": "#8E24AA", "snacks": "#FDD835",
}
CATEGORY_BACKGROUNDS = {
    "cold_drink": "#FFEBEE", "energy_drink": "#E3F2FD", "fruit_drink": "#FFF3E0",
    "water": "#E1F5FE", "beer": "#FFF8E1", "wine": "#F3E5F5", "snacks": "#FFFDE7",
}


def label(text: str, color: str, y: int, width: int, center_x: int = 128) -> str:
    """Brand name centred on the container label, shrunk to fit."""
    font_size = max(9, min(18, int(width * 1.6 / max(len(text), 1))))
    return (
        f'<text x="{center_x}" y="{y}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" '
        f'font-weight="bold" font-size="{font_size}" fill="{color}">{escape(text)}</text>'
    )


def soda_bottle(color: str, text_color: str, name: str) -> str:
    return (
        f'<path d="M112 28h32v22c0 10 20 22 20 48v118c0 8-6 14-14 14h-44c-8 0-14-6-14-14V98c0-26 20-38 20-48z" fill="{color}"/>'
        '<rect x="110" y="18" width="36" height="14" rx="3" fill="#424242"/>'
        f'<rect x="92" y="120" width="72" height="44" fill="#FFFFFF" opacity="0.18"/>'
        f'{label(name, text_color, 148, 72)}'
        '<path d="M104 104c0-10 6-18 10-22v120h-10z" fill="#FFFFFF" opacity="0.25"/>'
    )


def can(color: str, text_color: str, name: str) -> str:
    return (
        f'<rect x="88" y="44" width="80" height="176" rx="12" fill="{color}"/>'
        '<rect x="94" y="34" width="68" height="14" rx="5" fill="#9E9E9E"/>'
        '<rect x="94" y="216" width="68" height="10" rx="4" fill="#9E9E9E"/>'
        f'{label(name, text_color, 138, 80)}'
        '<rect x="98" y="56" width="10" height="150" rx="5" fill="#FFFFFF" opacity="0.25"/>'
    )


def carton(color: str, text_color: str, name: str) -> str:
    return (
        f'<path d="M84 72l20-36h48l20 36v150H84z" fill="{color}"/>'
        '<path d="M104 36h48l20 36H84z" fill="#FFFFFF" opacity="0.3"/>'
        '<rect x="140" y="20" width="6" height="30" fill="#EEEEEE"/>'
        f'<circle cx="128" cy="170" r="26" fill="#FFFFFF" opacity="0.3"/>'
        f'{label(name, text_color, 128, 88)}'
    )


def water_bottle(color: str, text_color: str, name: str) -> str:
    return (
        '<path d="M110 30h36v20c0 8 22 18 22 40v130c0 8-6 14-14 14h-52c-8 0-14-6-14-14V90c0-22 22-32 22-40z" '
        'fill="#B3E5FC" opacity="0.8"/>'
        '<rect x="108" y="18" width="40" height="16" rx="3" fill="#0277BD"/>'
        f'<rect x="88" y="120" width="80" height="44" fill="{color}"/>'
        f'{label(name, text_color, 148, 80)}'
    )


def beer_bottle(color: str, text_color: str, name: str) -> str:
    return (
        f'<path d="M116 20h24v50c0 12 26 24 26 50v100c0 8-6 14-14 14h-48c-8 0-14-6-14-14V120c0-26 26-38 26-50z" fill="#5D4037"/>'
        '<rect x="114" y="14" width="28" height="10" rx="2" fill="#FFC107"/>'
        f'<rect x="92" y="136" width="72" height="54" rx="4" fill="{color}"/>'
        f'{label(name, text_color, 168, 72)}'
        '<path d="M100 128c0-14 8-22 14-28v120h-14z" fill="#FFFFFF" opacity="0.15"/>'
    )


def wine_bottle(color: str, text_color: str, name: str) -> str:
    return (
        '<path d="M102 14h20v56c0 10 18 20 18 44v110c0 6-4 10-10 10h-36c-6 0-10-4-10-10V114c0-24 18-34 18-44z" fill="#1B1B2F"/>'
        f'<rect x="102" y="12" width="20" height="18" fill="{color}"/>'
        f'<rect x="86" y="140" width="52" height="56" rx="3" fill="#FFF8E1"/>'
        f'<rect x="86" y="140" width="52" height="10" fill="{color}"/>'
        f'{label(name, "#3E2723", 176, 52, center_x=112)}'
        f'<path d="M160 120h52c0 26-10 42-26 44v44h16v8h-40v-8h16v-44c-16-2-26-18-26-44z" fill="#FFFFFF" stroke="#BDBDBD" stroke-width="2"/>'
        f'<path d="M162 132h48c-2 16-10 26-24 28-14-2-22-12-24-28z" fill="{color}"/>'
    )


def snack_pack(color: str, text_color: str, name: str) -> str:
    return (
        f'<path d="M72 40h112l-8 20 8 20v120l-8 20H80l-8-20V80l8-20z" fill="{color}"/>'
        '<ellipse cx="128" cy="170" rx="34" ry="18" fill="#FFE082"/>'
        f'{label(name, text_color, 116, 100)}'
    )


CONTAINERS = {
    "cold_drink": soda_bottle, "energy_drink": can, "fruit_drink": carton,
    "water": water_bottle, "beer": beer_bottle, "wine": wine_bottle, "snacks": snack_pack,
}


def render_svg(category: str, brand: str) -> str:
    """Render one product illustration."""
    fallback_color = CATEGORY_COLORS.get(category, "#757575")
    color, text_color = BRAND_COLORS.get(brand.lower(), (fallback_color, "#FFFFFF"))
    container = CONTAINERS.get(category, can)
    background = CATEGORY_BACKGROUNDS.get(category, "#F5F5F5")
    title = escape(f"{brand} {category.replace('_', ' ')}".strip())
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" viewBox="0 0 256 256" '
        f'role="img" aria-label="{title}"><title>{title}</title>'
        f'<rect width="256" height="256" rx="24" fill="{background}"/>'
        f'<ellipse cx="128" cy="236" rx="60" ry="8" fill="#000000" opacity="0.08"/>'
        f'{container(color, text_color, brand)}</svg>\n'
    )


def main() -> None:
    """Write brand and category-default images for the whole catalog."""
    pairs = sorted({(record["category"], record["brand"]) for record in load_catalog()})
    categories = sorted({category for category, _ in pairs})

    for category, brand in pairs:
        path = STATIC_DIR / image_relative_path(category, brand)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_svg(category, brand), encoding="utf-8")

    for category in categories:
        path = STATIC_DIR / category_fallback_path(category)
        path.parent.mkdir(parents=True, exist_ok=True)
        label_text = category.replace("_", " ").title()
        path.write_text(render_svg(category, label_text), encoding="utf-8")

    missing = sorted({brand for _, brand in pairs if brand.lower() not in BRAND_COLORS})
    print(f"Wrote {len(pairs)} brand images + {len(categories)} category defaults to {STATIC_DIR / 'product-images'}")
    if missing:
        print(f"Brands using category colours (no brand colour defined): {', '.join(missing)}")


if __name__ == "__main__":
    main()
