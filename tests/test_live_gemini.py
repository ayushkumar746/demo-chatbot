"""
Live tests against the real Google Gemini API and the seeded local vector DB.

Skipped by default. Run with:
    RUN_LIVE_TESTS=1 pytest tests/test_live_gemini.py
Requires GEMINI_API_KEY in .env and `python seed_products.py` to have been run.
"""
import os

import pytest
from fastapi.testclient import TestClient

from app.agent.planner import PlannerAgent
from app.services.cart_service import MOCK_CARTS
from app.services.gemini_client import GeminiClient
from app.services.vector_store import ProductVectorStore

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_TESTS") != "1", reason="set RUN_LIVE_TESTS=1 to call the real Gemini API"
)

QUERY = "Add cold drink which have less price 100 RS"


def test_live_planner_extracts_intent():
    intent = PlannerAgent(gemini=GeminiClient()).plan({"user_query": QUERY})["intent"]
    assert intent.action == "ADD_TO_CART"
    assert intent.category == "cold_drink"
    assert intent.max_price == 100


@pytest.mark.parametrize("query", ["cold drink", "soft drink", "soda", "carbonated drink"])
def test_live_semantic_search_ranks_cold_drinks_first(query):
    results = ProductVectorStore().search(query, store_id="STORE_1")
    assert results[0].product.category == "cold_drink"


def test_live_chat_end_to_end():
    MOCK_CARTS.clear()
    body = TestClient(__import__("main").app).post(
        "/api/chat", json={"query": QUERY, "user_id": "live_user", "store_id": "STORE_1"}
    ).json()
    assert body["success"] is True, body
    item = body["cart_state"]["items"][0]
    assert item["price"] <= 100
    MOCK_CARTS.clear()
