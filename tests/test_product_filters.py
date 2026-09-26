"""Tests for deterministic product filtering, selection and relevance cut-off."""
import pytest

from app.agent.product_agent import product_agent, validate_price_constraint
from app.schemas import Product, ShoppingIntent
from app.services.product_service import select_relevant
from app.services.vector_store import ScoredProduct
from app.tools.product_tools import (
    filter_by_availability,
    filter_by_category,
    filter_by_price,
    format_price,
    select_product,
)


def product(product_id, price, category="cold_drink", available=True, inventory=10, store_id="STORE_1"):
    return Product(id=product_id, name=product_id, price=price, category=category,
                   available=available, inventory=inventory, store_id=store_id)


PRODUCTS = [
    product("COKE", 45),
    product("SPRITE", 40),
    product("REDBULL", 125, category="energy_drink"),
    product("CAMPA", 30, available=False),
    product("LIMCA", 40, inventory=0),
]


def test_price_filter_applies_max_price_inclusively():
    ids = [p.id for p in filter_by_price(PRODUCTS, max_price=100)]
    assert "REDBULL" not in ids
    assert [p.id for p in filter_by_price(PRODUCTS, max_price=45, min_price=45)] == ["COKE"]


def test_availability_filter_excludes_unavailable_and_out_of_stock():
    assert [p.id for p in filter_by_availability(PRODUCTS)] == ["COKE", "SPRITE", "REDBULL"]


def test_category_filter():
    assert [p.id for p in filter_by_category(PRODUCTS, "energy_drink")] == ["REDBULL"]


def test_cheapest_selection_prefers_most_relevant_on_price_tie():
    candidates = [product("FANTA", 40), product("SPRITE", 40), product("COKE", 45)]
    assert select_product(candidates, "CHEAPEST").id == "FANTA"


def test_confirm_strategy_requires_user_choice():
    assert select_product(PRODUCTS[:2], "CONFIRM") is None


@pytest.mark.parametrize(
    "intent_fields, valid",
    [
        ({"max_price": 100}, True),
        ({"max_price": 0}, False),
        ({"max_price": -5}, False),
        ({"min_price": -1}, False),
        ({"min_price": 200, "max_price": 100}, False),
    ],
)
def test_price_constraint_validation(intent_fields, valid):
    intent = ShoppingIntent(action="ADD_TO_CART", **intent_fields)
    assert (validate_price_constraint(intent) is None) == valid


def test_filter_node_reports_out_of_stock():
    state = {
        "intent": ShoppingIntent(action="ADD_TO_CART", max_price=100),
        "candidate_products": [PRODUCTS[3], PRODUCTS[4]],
        "search_query": "cold drink",
    }
    result = product_agent.filter_products(state)
    assert result["filtered_products"] == []
    assert "out of stock" in result["error"]


def test_filter_node_reports_no_match_under_price():
    state = {
        "intent": ShoppingIntent(action="ADD_TO_CART", max_price=10),
        "candidate_products": PRODUCTS,
        "search_query": "cold drink",
    }
    result = product_agent.filter_products(state)
    assert "under ₹10" in result["error"]


def test_filter_node_rejects_invalid_price_constraint():
    state = {
        "intent": ShoppingIntent(action="ADD_TO_CART", max_price=-1),
        "candidate_products": PRODUCTS,
    }
    assert "Invalid price constraint" in product_agent.filter_products(state)["error"]


def test_relevance_cutoff_keeps_close_matches_only():
    scored = [
        ScoredProduct(product("A", 1), 0.28),
        ScoredProduct(product("B", 1), 0.31),
        ScoredProduct(product("C", 1), 0.35),
    ]
    assert [s.product.id for s in select_relevant(scored)] == ["A", "B"]
    assert select_relevant([ScoredProduct(product("X", 1), 0.45)]) == []
    assert select_relevant([]) == []


def test_format_price():
    assert format_price(45.0) == "₹45"
    assert format_price(1000000.0) == "₹1000000"
    assert format_price(45.5) == "₹45.50"
