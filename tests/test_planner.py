"""Tests for the Gemini-backed planner agent."""
from app.agent.planner import PlannerAgent
from app.services.gemini_client import GeminiModelNotFoundError
from tests.conftest import COLD_DRINK_UNDER_100, FakeGemini, make_planner_output

QUERY = "Add cold drink which have less price 100 RS"


def test_planner_detects_add_to_cart_intent(wired_app):
    planner = PlannerAgent(gemini=wired_app)
    state = planner.plan({"user_query": QUERY})

    intent = state["intent"]
    assert state.get("error") is None
    assert intent.action == "ADD_TO_CART"
    assert intent.category == "cold_drink"
    assert intent.max_price == 100
    assert state["plan"]["confidence"] == 0.95


def test_planner_drops_unknown_category(wired_app):
    gemini = FakeGemini(planner_output=make_planner_output(search_query="soda", category="fizzy_stuff"))
    state = PlannerAgent(gemini=gemini).plan({"user_query": "add a soda"})
    assert state["intent"].category is None
    assert state["intent"].search_query == "soda"


def test_planner_sets_confirmation_for_confirm_strategy(wired_app):
    gemini = FakeGemini(planner_output=make_planner_output(**COLD_DRINK_UNDER_100, selection_strategy="CONFIRM"))
    assert PlannerAgent(gemini=gemini).plan({"user_query": QUERY})["requires_confirmation"] is True


def test_planner_gemini_failure_returns_safe_error(wired_app):
    error = GeminiModelNotFoundError("404 NOT_FOUND: models/gemini-pro is not found for API version v1beta")
    state = PlannerAgent(gemini=FakeGemini(error=error)).plan({"user_query": QUERY})

    assert state["intent"] is None
    assert state["error"].startswith("Planner error:")
    assert "v1beta" not in state["error"]
