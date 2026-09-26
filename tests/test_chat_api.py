"""End-to-end tests for POST /api/chat through the full LangGraph workflow."""
import pytest
from fastapi.testclient import TestClient

from app.services.gemini_client import GeminiAuthenticationError, GeminiRateLimitError
from app.services.vector_store import ProductVectorStore
from app.config import settings
from main import app
from tests.conftest import FakeGemini, make_planner_output

REQUEST = {
    "query": "Add cold drink which have less price 100 RS",
    "user_id": "user123",
    "store_id": "STORE_1",
}


@pytest.fixture
def client():
    return TestClient(app)


def valid_cold_drinks(catalog, store_id, max_price=100):
    """Catalog products that satisfy 'cold drink under max_price' in a store."""
    return [
        record for record in catalog
        if record["store_id"] == store_id and record["category"] == "cold_drink"
        and record["available"] and record["stock"] > 0 and record["price"] <= max_price
    ]


def use_planner(monkeypatch, gemini):
    from app.agent.planner import planner_agent
    monkeypatch.setattr(planner_agent, "_gemini", gemini)


def test_add_cold_drink_under_100_adds_valid_product(client, wired_app, catalog):
    response = client.post("/api/chat", json=REQUEST)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["intent"]["action"] == "ADD_TO_CART"
    assert body["intent"]["max_price"] == 100

    cart = body["cart_state"]
    assert cart["user_id"] == "user123" and cart["store_id"] == "STORE_1"
    assert len(cart["items"]) == 1
    item = cart["items"][0]
    # CHEAPEST_MATCH: the cheapest in-stock, available STORE_1 cold drink under ₹100
    valid = valid_cold_drinks(catalog, "STORE_1")
    assert item["product_id"] in {record["product_id"] for record in valid}
    assert item["price"] == min(record["price"] for record in valid)
    assert item["image_url"].endswith(".svg")
    assert cart["total_price"] == item["price"]
    assert item["name"] in body["response"]


def test_repeating_request_increments_quantity_without_duplicate_line(client, wired_app):
    first = client.post("/api/chat", json=REQUEST).json()
    body = client.post("/api/chat", json=REQUEST).json()

    assert body["success"] is True
    items = body["cart_state"]["items"]
    assert len(items) == 1
    assert items[0]["product_id"] == first["cart_state"]["items"][0]["product_id"]
    assert items[0]["quantity"] == 2
    assert body["cart_state"]["total_price"] == 2 * items[0]["price"]
    assert "quantity updated to 2" in body["response"]


def test_store_filtering_uses_requested_store(client, wired_app, catalog):
    body = client.post("/api/chat", json={**REQUEST, "store_id": "STORE_2"}).json()
    assert body["success"] is True
    item = body["cart_state"]["items"][0]
    valid = valid_cold_drinks(catalog, "STORE_2")
    assert item["product_id"] in {record["product_id"] for record in valid}
    assert item["price"] == min(record["price"] for record in valid)


def test_unknown_store_is_rejected(client, wired_app):
    body = client.post("/api/chat", json={**REQUEST, "store_id": "STORE_404"}).json()
    assert body["success"] is False
    assert "Unknown store" in body["error"]
    assert body["cart_state"] is None


def test_no_matching_product(client, monkeypatch, wired_app):
    use_planner(monkeypatch, FakeGemini(planner_output=make_planner_output(
        search_query="cold drink", category="cold_drink", max_price=5)))
    body = client.post("/api/chat", json=REQUEST).json()

    assert body["success"] is False
    assert "under ₹5" in body["error"]
    assert body["cart_state"] is None


def test_irrelevant_product_is_not_added(client, monkeypatch, wired_app):
    use_planner(monkeypatch, FakeGemini(planner_output=make_planner_output(search_query="laptop")))
    body = client.post("/api/chat", json={**REQUEST, "query": "add a laptop"}).json()
    assert body["success"] is False
    assert body["cart_state"] is None


def test_confirmation_policy_lists_options_without_adding(client, monkeypatch, wired_app):
    use_planner(monkeypatch, FakeGemini(planner_output=make_planner_output(
        search_query="cold drink", category="cold_drink", max_price=100, selection_strategy="CONFIRM")))
    body = client.post("/api/chat", json=REQUEST).json()
    assert "Which one would you like" in body["response"]
    assert "Red Bull" not in body["response"]
    option_lines = [line for line in body["response"].splitlines() if line[:1].isdigit()]
    assert 1 <= len(option_lines) <= settings.max_confirmation_options
    assert body["cart_state"] is None


@pytest.mark.parametrize("error", [
    GeminiAuthenticationError("400 INVALID_ARGUMENT: API key not valid"),
    GeminiRateLimitError("429 RESOURCE_EXHAUSTED"),
])
def test_gemini_failure_returns_safe_error(client, monkeypatch, wired_app, error):
    use_planner(monkeypatch, FakeGemini(error=error))
    response = client.post("/api/chat", json=REQUEST)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"] == f"Planner error: {error.user_message}"
    assert error.detail not in body["error"]


def test_uninitialized_vector_db_returns_safe_error(client, monkeypatch, tmp_path, wired_app):
    from app.services.product_service import product_service
    monkeypatch.setattr(product_service, "vector_store",
                        ProductVectorStore(path=tmp_path / "missing", gemini=wired_app))
    body = client.post("/api/chat", json=REQUEST).json()
    assert body["success"] is False
    assert "product index is not initialized" in body["error"]


def test_request_validation(client):
    assert client.post("/api/chat", json={"user_id": "u1"}).status_code == 422


def test_health_reports_product_index(client, wired_app):
    body = client.get("/api/health").json()
    assert body["status"] == "healthy"
    assert body["product_index"]["ready"] is True


def test_alcohol_is_not_added_for_cold_drink_request(client, wired_app, catalog):
    body = client.post("/api/chat", json=REQUEST).json()
    categories = {record["product_id"]: record["category"] for record in catalog}
    assert categories[body["cart_state"]["items"][0]["product_id"]] == "cold_drink"


def test_beer_request_adds_beer(client, monkeypatch, wired_app, catalog):
    use_planner(monkeypatch, FakeGemini(planner_output=make_planner_output(
        search_query="beer", category="beer", max_price=100)))
    body = client.post("/api/chat", json={**REQUEST, "query": "add a beer under 100"}).json()
    categories = {record["product_id"]: record["category"] for record in catalog}
    assert body["success"] is True
    assert categories[body["cart_state"]["items"][0]["product_id"]] == "beer"


def test_product_images_are_served(client, wired_app):
    body = client.post("/api/chat", json=REQUEST).json()
    image_path = body["cart_state"]["items"][0]["image_url"].split("localhost:8000", 1)[1]
    response = client.get(image_path)
    assert response.status_code == 200
    assert response.text.startswith("<svg")
