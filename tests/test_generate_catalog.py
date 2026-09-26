"""Tests for the deterministic sample catalog generator."""
import generate_catalog


def test_generator_is_deterministic():
    assert generate_catalog.generate_products() == generate_catalog.generate_products()


def test_generator_produces_requested_count_with_unique_ids():
    records = generate_catalog.generate_products()
    assert len(records) == generate_catalog.GENERATED_COUNT
    assert len({record["product_id"] for record in records}) == len(records)
    assert len({(record["name"], record["store_id"]) for record in records}) == len(records)


def test_generator_uses_only_demo_price_points_and_covers_all():
    prices = {record["price"] for record in generate_catalog.generate_products()}
    assert prices == set(generate_catalog.PRICE_POINTS)


def test_alcoholic_products_are_labelled():
    for record in generate_catalog.generate_products():
        if record["category"] in ("beer", "wine"):
            assert "Alcoholic" in record["description"]


def test_committed_catalog_matches_generator(catalog):
    generated_ids = {record["product_id"] for record in generate_catalog.generate_products()}
    assert generated_ids <= {record["product_id"] for record in catalog}
