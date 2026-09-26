from typing import TypedDict, Any, Optional, List
from app.schemas import ShoppingIntent, Product, Cart, CartValidationResult


class AgentState(TypedDict, total=False):
    """Shared state for all agents in the LangGraph workflow"""
    
    # Input
    user_query: str
    user_id: str
    store_id: str
    session_id: Optional[str]
    
    # Planner output
    intent: Optional[ShoppingIntent]
    plan: Optional[dict]
    
    # Product discovery
    search_query: Optional[str]
    candidate_products: Optional[List[Product]]
    filtered_products: Optional[List[Product]]
    selected_product: Optional[Product]
    
    # Cart operations
    cart: Optional[Cart]
    validation_result: Optional[CartValidationResult]
    action_result: Optional[dict]
    
    # Final output
    final_response: Optional[str]
    
    # Error handling
    error: Optional[str]
    
    # Metadata
    requires_confirmation: bool
    confirmation_options: Optional[List[dict]]
