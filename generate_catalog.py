"""
Generate a large, deterministic sample catalog for the demo.

Writes `data/products/generated_products.json` with GENERATED_COUNT products
across soft drinks, energy drinks, fruit drinks, water, beer and wine, priced
at the demo price points. The same seed always yields the same file, so
re-running this and `seed_products.py` never creates duplicates.

Usage:
    python generate_catalog.py
    python seed_products.py
"""
import itertools
import json
import math
import random
from pathlib import Path

OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "products" / "generated_products.json"
GENERATED_COUNT = 1000
FIRST_PRODUCT_NUMBER = 1001
RANDOM_SEED = 42

PRICE_POINTS = [10, 20, 30, 35, 40, 50, 80, 90, 100]
STORES = ["STORE_1", "STORE_2", "STORE_3"]
UNAVAILABLE_RATE = 0.05
OUT_OF_STOCK_RATE = 0.07

# Share of GENERATED_COUNT per category (must sum to 1.0)
CATEGORY_SHARE = {
    "cold_drink": 0.25,
    "energy_drink": 0.10,
    "fruit_drink": 0.15,
    "water": 0.05,
    "beer": 0.25,
    "wine": 0.20,
}

# category -> (brands, variants, sizes, description template)
CATEGORY_SPECS = {
    "cold_drink": (
        ["Coca Cola", "Pepsi", "Sprite", "Thums Up", "Fanta", "Mountain Dew", "7Up", "Mirinda",
         "Limca", "Campa", "Bovonto", "Duke's", "Appy Fizz", "Schweppes"],
        ["Original", "Zero Sugar", "Diet", "Lime", "Orange"],
        ["200ml", "250ml", "300ml", "500ml", "600ml", "750ml", "1.25L", "2L"],
        "{variant} {brand} carbonated soft drink. Fizzy, refreshing cold drink, best served chilled.",
    ),
    "energy_drink": (
        ["Sting", "Red Bull", "Monster", "Hell", "Charged", "Gatorade"],
        ["Original", "Sugar Free", "Berry Blast"],
        ["250ml", "350ml", "500ml"],
        "{variant} {brand} caffeinated energy drink for an instant energy boost.",
    ),
    "fruit_drink": (
        ["Maaza", "Slice", "Frooti", "Real", "Tropicana", "Paper Boat", "B Natural", "Minute Maid", "Appy"],
        ["Mango", "Mixed Fruit", "Guava", "Apple", "Litchi"],
        ["160ml", "200ml", "600ml", "1L"],
        "{brand} {variant} fruit juice drink. Non-carbonated fruit beverage.",
    ),
    "water": (
        ["Kinley", "Bisleri", "Aquafina", "Bailley", "Himalayan"],
        ["Mineral Water", "Packaged Drinking Water"],
        ["250ml", "500ml", "1L", "2L"],
        "{brand} {variant}. Purified packaged drinking water.",
    ),
    "beer": (
        ["Kingfisher", "Budweiser", "Heineken", "Tuborg", "Carlsberg", "Corona", "Bira 91",
         "Hoegaarden", "Simba", "Godfather", "Haywards 5000", "Knock Out", "Stella Artois"],
        ["Premium Lager", "Strong", "Wheat Beer", "Blonde", "Ultra", "Pilsner"],
        ["330ml Can", "500ml Can", "650ml Bottle"],
        "{brand} {variant} beer. Alcoholic beverage (brewed malt beer), for customers aged 21+ only.",
    ),
    "wine": (
        ["Sula", "Grover Zampa", "Fratelli", "York", "Jacob's Creek", "Big Banyan", "Four Seasons", "Nine Hills"],
        ["Cabernet Sauvignon", "Shiraz", "Merlot", "Chenin Blanc", "Sauvignon Blanc", "Rose", "Sparkling Brut"],
        ["187ml", "375ml", "750ml"],
        "{brand} {variant} wine. Alcoholic beverage made from fermented grapes, for customers aged 21+ only.",
    ),
}


def price_for_size(rng: random.Random, size_index: int, size_count: int) -> int:
    """Pick a price from the price band of this pack size; bigger packs get higher bands."""
    band_start = size_index * len(PRICE_POINTS) // size_count
    band_end = max(band_start, math.ceil((size_index + 1) * len(PRICE_POINTS) / size_count) - 1)
    return PRICE_POINTS[rng.randint(band_start, band_end)]


def category_quotas() -> dict:
    """Number of products per category, summing exactly to GENERATED_COUNT."""
    quotas = {category: int(GENERATED_COUNT * share) for category, share in CATEGORY_SHARE.items()}
    quotas["cold_drink"] += GENERATED_COUNT - sum(quotas.values())
    return quotas


def generate_products() -> list:
    """Build the generated catalog records deterministically."""
    rng = random.Random(RANDOM_SEED)
    records = []

    for category, quota in category_quotas().items():
        brands, variants, sizes, template = CATEGORY_SPECS[category]
        combinations = list(itertools.product(brands, variants, range(len(sizes)), STORES))
        if quota > len(combinations):
            raise ValueError(f"Only {len(combinations)} unique {category} products possible, need {quota}")
        rng.shuffle(combinations)

        for brand, variant, size_index, store_id in sorted(combinations[:quota]):
            size = sizes[size_index]
            out_of_stock = rng.random() < OUT_OF_STOCK_RATE
            records.append({
                "name": f"{brand} {variant} {size}",
                "description": template.format(brand=brand, variant=variant),
                "category": category,
                "brand": brand,
                "price": price_for_size(rng, size_index, len(sizes)),
                "currency": "INR",
                "store_id": store_id,
                "available": rng.random() >= UNAVAILABLE_RATE,
                "stock": 0 if out_of_stock else rng.randint(5, 250),
            })

    for number, record in enumerate(records, start=FIRST_PRODUCT_NUMBER):
        record["product_id"] = f"PROD_{number}"
    return [{"product_id": r.pop("product_id"), **r} for r in records]


def main() -> None:
    """Write the generated catalog and print a summary."""
    records = generate_products()
    OUTPUT_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote {len(records)} products to {OUTPUT_PATH}")
    for category in CATEGORY_SHARE:
        prices = sorted({r["price"] for r in records if r["category"] == category})
        count = sum(r["category"] == category for r in records)
        print(f"  {category:13} {count:4}  prices: {prices}")


if __name__ == "__main__":
    main()
