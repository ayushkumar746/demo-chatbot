from typing import Literal
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.planner import planner_agent
from app.agent.product_agent import product_agent
from app.agent.cart_agent import cart_agent
from app.agent.response_agent import response_agent


def route_intent(state: AgentState) -> Literal["product_flow", "cart_flow", "response"]:
    """
    Route the workflow based on the detected intent.
    
    This is a conditional routing function for LangGraph.
    """
    intent = state.get("intent")
    
    if not intent:
        return "response"
    
    action = intent.action
    
    if action in ["SEARCH_PRODUCT", "ADD_TO_CART"]:
        return "product_flow"
    elif action in ["REMOVE_FROM_CART", "UPDATE_CART", "VIEW_CART"]:
        return "cart_flow"
    else:
        return "response"


def route_product_flow(state: AgentState) -> Literal["filter_products", "response"]:
    """
    Route after product search based on results.
    """
    candidate_products = state.get("candidate_products")
    
    if not candidate_products or len(candidate_products) == 0:
        return "response"
    
    return "filter_products"


def route_after_filter(state: AgentState) -> Literal["select_product", "response"]:
    """
    Route after filtering based on results.
    """
    filtered_products = state.get("filtered_products")
    
    if not filtered_products or len(filtered_products) == 0:
        return "response"
    
    return "select_product"


def route_after_selection(state: AgentState) -> Literal["get_cart", "response"]:
    """
    Route after product selection.
    """
    selected_product = state.get("selected_product")
    intent = state.get("intent")
    
    # If no product selected (confirmation needed) or not adding to cart
    if not selected_product or (intent and intent.action != "ADD_TO_CART"):
        return "response"
    
    return "get_cart"


def route_after_validation(state: AgentState) -> Literal["add_to_cart", "response"]:
    """
    Route after cart validation.
    """
    validation = state.get("validation_result")
    
    if not validation or not validation.valid:
        return "response"
    
    return "add_to_cart"


def route_after_cart_action(state: AgentState) -> Literal["verify_cart", "response"]:
    """
    Route after cart action.
    """
    action_result = state.get("action_result")
    
    if action_result and action_result.get("success"):
        return "verify_cart"
    
    return "response"


def create_shopping_graph() -> StateGraph:
    """
    Create the LangGraph workflow for the shopping assistant.
    
    This function builds the complete graph with all nodes and edges.
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", planner_agent.plan)
    workflow.add_node("search_products", product_agent.search_products)
    workflow.add_node("filter_products", product_agent.filter_products)
    workflow.add_node("select_product", product_agent.select_product)
    workflow.add_node("get_cart", cart_agent.get_cart)
    workflow.add_node("validate_cart", cart_agent.validate_cart_operation)
    workflow.add_node("add_to_cart", cart_agent.add_to_cart)
    workflow.add_node("verify_cart", cart_agent.verify_cart_state)
    workflow.add_node("response", response_agent.generate_response)
    
    # Set entry point
    workflow.set_entry_point("planner")
    
    # Add edges
    workflow.add_conditional_edges(
        "planner",
        route_intent,
        {
            "product_flow": "search_products",
            "cart_flow": "get_cart",
            "response": "response"
        }
    )
    
    workflow.add_conditional_edges(
        "search_products",
        route_product_flow,
        {
            "filter_products": "filter_products",
            "response": "response"
        }
    )
    
    workflow.add_conditional_edges(
        "filter_products",
        route_after_filter,
        {
            "select_product": "select_product",
            "response": "response"
        }
    )
    
    workflow.add_conditional_edges(
        "select_product",
        route_after_selection,
        {
            "get_cart": "get_cart",
            "response": "response"
        }
    )
    
    workflow.add_edge("get_cart", "validate_cart")
    
    workflow.add_conditional_edges(
        "validate_cart",
        route_after_validation,
        {
            "add_to_cart": "add_to_cart",
            "response": "response"
        }
    )
    
    workflow.add_conditional_edges(
        "add_to_cart",
        route_after_cart_action,
        {
            "verify_cart": "verify_cart",
            "response": "response"
        }
    )
    
    workflow.add_edge("verify_cart", "response")
    workflow.add_edge("response", END)
    
    # Compile the graph
    return workflow.compile()


# Global graph instance
shopping_graph = create_shopping_graph()
