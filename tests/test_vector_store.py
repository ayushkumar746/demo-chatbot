"""Tests for product seeding, the local vector database and semantic search."""
import json

import pytest

from app.schemas import ProductSearchRequest
from app.services.product_service import ProductService
from app.services.vector_store import ProductVectorStore, VectorStoreError, build_search_text, load_catalog
from tests.conftest import FakeGemini


def test_catalog_contains_required_fields(catalog):
    required = {"product_id", "name", "description", "category", "brand", "price",
                "currency", "store_id", "available", "stock"}
    assert catalog
    for record in catalog:
        assert required <= record.keys()


def test_duplicate_product_ids_are_rejected(tmp_path, catalog):
    path = tmp_path / "products.json"
    path.write_text(json.dumps([catalog[0], catalog[0]]))
    with pytest.raises(ValueError):
        load_catalog(path)


def test_search_text_includes_name_description_category_and_brand(catalog):
    text = build_search_text(catalog[0])
    for part in (catalog[0]["name"], catalog[0]["brand"], "cold drink"):
        assert part in text


def test_seed_persists_all_products_to_disk(tmp_path, catalog):
    path = tmp_path / "vector_db"
    ProductVectorStore(path=path, gemini=FakeGemini()).seed(catalog, progress=lambda m: None)
    # A fresh store instance reads the persisted index
    reopened = ProductVectorStore(path=path, gemini=FakeGemini())
    assert reopened.count() == len(catalog)
    assert any(path.iterdir())


def test_seed_is_idempotent_and_skips_unchanged_products(tmp_path, catalog):
    gemini = FakeGemini()
    store = ProductVectorStore(path=tmp_path / "vector_db", gemini=gemini)
    first = store.seed(catalog, progress=lambda m: None)
    calls_after_first = gemini.embed_calls

    second = store.seed(catalog, progress=lambda m: None)

    assert first.embedded == len(catalog)
    assert second.embedded == 0 and second.unchanged == len(catalog)
    assert gemini.embed_calls == calls_after_first
    assert store.count() == len(catalog)


def test_seed_updates_changed_products_and_removes_stale_ones(tmp_path, catalog):
    store = ProductVectorStore(path=tmp_path / "vector_db", gemini=FakeGemini())
    store.seed(catalog, progress=lambda m: None)

    changed = [dict(record) for record in catalog[:-1]]
    changed[0]["price"] = 99
    report = store.seed(changed, progress=lambda m: None)

    assert report.embedded == 1 and report.removed == 1
    assert store.count() == len(catalog) - 1
    assert store.get_product(changed[0]["product_id"], changed[0]["store_id"]).price == 99


def test_embedding_model_change_rebuilds_index(tmp_path, catalog):
    path = tmp_path / "vector_db"
    ProductVectorStore(path=path, gemini=FakeGemini()).seed(catalog, progress=lambda m: None)

    other_model = FakeGemini()
    other_model.embedding_model = "another-embedding"
    store = ProductVectorStore(path=path, gemini=other_model)
    with pytest.raises(VectorStoreError):
        store.count()

    report = store.seed(catalog, progress=lambda m: None)
    assert report.recreated and store.count() == len(catalog)


def test_unseeded_index_reports_clear_error(tmp_path):
    store = ProductVectorStore(path=tmp_path / "empty", gemini=FakeGemini())
    with pytest.raises(VectorStoreError, match="seed_products"):
        store.search("cold drink", store_id="STORE_1")


def test_search_is_restricted_to_store(vector_store):
    results = vector_store.search("cold drink", store_id="STORE_2")
    assert results
    assert {result.product.store_id for result in results} == {"STORE_2"}


def test_search_orders_by_semantic_relevance(vector_store):
    results = vector_store.search("cold drink", store_id="STORE_1")
    assert results[0].product.category == "cold_drink"
    distances = [result.distance for result in results]
    assert distances == sorted(distances)


@pytest.mark.parametrize("query", ["cold drink", "soft drink", "soda", "carbonated drink"])
def test_semantic_search_understands_synonyms(vector_store, query):
    response = ProductService(vector_store).search_products(
        ProductSearchRequest(query=query, store_id="STORE_1")
    )
    assert response.products
    assert {product.category for product in response.products} == {"cold_drink"}


def test_irrelevant_query_returns_no_products(vector_store):
    response = ProductService(vector_store).search_products(
        ProductSearchRequest(query="laptop", store_id="STORE_1")
    )
    assert response.products == []


def test_store_and_category_lookups(vector_store):
    assert vector_store.store_exists("STORE_1")
    assert not vector_store.store_exists("STORE_404")
    assert "cold_drink" in vector_store.categories()
    assert vector_store.get_product("PROD_001", "STORE_2") is None
    assert vector_store.get_product("PROD_001", "STORE_1").name == "Coca Cola 750ml"


def test_catalog_directory_loads_all_files(catalog):
    assert len(catalog) >= 1000
    assert {"beer", "wine", "cold_drink"} <= {record["category"] for record in catalog}


def test_search_can_be_restricted_to_category(vector_store):
    results = vector_store.search("drink", store_id="STORE_1", category="beer")
    assert results
    assert {result.product.category for result in results} == {"beer"}


def test_products_have_existing_image(vector_store):
    from app.services.product_images import STATIC_DIR
    for result in vector_store.search("cold drink", store_id="STORE_1")[:5]:
        relative = result.product.image_url.split("/static/", 1)[1]
        assert (STATIC_DIR / relative).exists()


def test_repeated_query_embeddings_are_cached(vector_store, fake_gemini):
    vector_store.search("cold drink", store_id="STORE_1")
    calls = fake_gemini.embed_calls
    vector_store.search("Cold Drink ", store_id="STORE_2")
    assert fake_gemini.embed_calls == calls
