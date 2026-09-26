import logging
from typing import Optional

from app.schemas import ProductSearchRequest, ShoppingIntent
from app.services.gemini_client import GeminiError
from app.services.product_service import product_service
from app.services.vector_store import VectorStoreError
from app.tools.product_tools import (
    filter_by_price,
    filter_by_category,
    filter_by_availability,
    select_product,
    format_price,
)
from app.config import settings
from app.agent.state import AgentState

logger = logging.getLogger(__name__)

# Maps the configured SELECTION_POLICY to a product_tools selection strategy
POLICY_TO_STRATEGY = {
    "CHEAPEST_MATCH": "CHEAPEST",
    "FIRST_MATCH": "FIRST",
    "ASK_CONFIRMATION": "CONFIRM",
}


def build_search_query(intent: ShoppingIntent, user_query: str) -> str:
    """Pick the most specific product description available for semantic search."""
    if intent.product_name:
        return intent.product_name
    if intent.search_query:
        return intent.search_query
    if intent.category:
        return intent.category.replace("_", " ")
    return user_query


def validate_price_constraint(intent: ShoppingIntent) -> Optional[str]:
    """Return an error message if the price constraint is impossible, else None."""
    if intent.max_price is not None and intent.max_price <= 0:
        return "Invalid price constraint: maximum price must be greater than ₹0."
    if intent.min_price is not None and intent.min_price < 0:
        return "Invalid price constraint: minimum price cannot be negative."
    if (
        intent.min_price is not None
        and intent.max_price is not None
        and intent.min_price > intent.max_price
    ):
        return "Invalid price constraint: minimum price is greater than maximum price."
    return None


def describe_price_constraint(intent: ShoppingIntent) -> str:
    """Human-readable price constraint, e.g. ' under ₹100'."""
    if intent.max_price is not None and intent.min_price is not None:
        return f" between {format_price(intent.min_price)} and {format_price(intent.max_price)}"
    if intent.max_price is not None:
        return f" under {format_price(intent.max_price)}"
    if intent.min_price is not None:
        return f" above {format_price(intent.min_price)}"
    return ""


class ProductAgent:
    """Product Agent that handles product discovery and selection"""

    def search_products(self, state: AgentState) -> AgentState:
        """
        Search for products semantically using the vector index, restricted to the store.

        This is a LangGraph node function.
        """
        intent = state.get("intent")
        store_id = state.get("store_id", settings.default_store_id)
        state["candidate_products"] = []

        if not intent:
            state["error"] = "No intent found in state"
            return state

        search_query = build_search_query(intent, state.get("user_query", ""))
        state["search_query"] = search_query

        try:
            if not product_service.store_exists(store_id):
                state["error"] = f"Unknown store '{store_id}'. Please choose a valid store."
                return state

            search_response = product_service.search_products(
                ProductSearchRequest(query=search_query, store_id=store_id, category=intent.category)
            )
        except VectorStoreError as error:
            logger.error("Vector store unavailable: %s", error)
            state["error"] = "Product search is unavailable: the product index is not initialized."
            return state
        except GeminiError as error:
            logger.error("Embedding query failed: %s", error.detail)
            state["error"] = f"Product search error: {error.user_message}"
            return state

        state["candidate_products"] = search_response.products
        if not search_response.products:
            state["error"] = f"No products matching '{search_query}' were found in this store."
        return state

    def filter_products(self, state: AgentState) -> AgentState:
        """
        Filter products using deterministic Python functions.

        This is a LangGraph node function.
        """
        candidate_products = state.get("candidate_products", [])
        intent = state.get("intent")
        state["filtered_products"] = []

        if not candidate_products or not intent:
            return state

        price_error = validate_price_constraint(intent)
        if price_error:
            state["error"] = price_error
            return state

        matching = candidate_products
        if intent.category:
            matching = filter_by_category(matching, intent.category)
        matching = filter_by_price(matching, max_price=intent.max_price, min_price=intent.min_price)

        label = state.get("search_query") or "products"
        if not matching:
            state["error"] = (
                f"No products matching '{label}'{describe_price_constraint(intent)} were found in this store."
            )
            return state

        available = filter_by_availability(matching)
        if not available:
            names = ", ".join(product.name for product in matching)
            state["error"] = f"Matching products are currently out of stock: {names}."
            return state

        state["filtered_products"] = available
        return state

    def select_product(self, state: AgentState) -> AgentState:
        """
        Select a product from filtered results using deterministic logic.

        This is a LangGraph node function.
        """
        filtered_products = state.get("filtered_products", [])
        intent = state.get("intent")

        if not filtered_products:
            state["selected_product"] = None
            state["error"] = "No products found matching criteria"
            return state

        # The user's explicit preference wins over the configured business policy
        strategy = (
            intent.selection_strategy if intent and intent.selection_strategy
            else POLICY_TO_STRATEGY[settings.selection_policy]
        )

        selected = select_product(filtered_products, strategy)

        if selected:
            state["selected_product"] = selected
            state["requires_confirmation"] = False
        else:
            # Multiple products and confirmation needed
            state["selected_product"] = None
            state["requires_confirmation"] = True
            state["confirmation_options"] = [
                {"id": p.id, "name": p.name, "price": p.price}
                for p in filtered_products[:settings.max_confirmation_options]
            ]

        return state


# Global instance
product_agent = ProductAgent()
