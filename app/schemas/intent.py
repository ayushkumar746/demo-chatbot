from pydantic import BaseModel, Field
from typing import Literal, Optional, List


class ShoppingIntent(BaseModel):
    """Structured output for the Planner Agent"""
    action: Literal[
        "SEARCH_PRODUCT",
        "ADD_TO_CART",
        "REMOVE_FROM_CART",
        "UPDATE_CART",
        "VIEW_CART"
    ] = Field(description="The primary action the user wants to perform")
    
    search_query: Optional[str] = Field(
        None,
        description="Short description of the product the user wants, used for semantic search (e.g., 'cold drink')"
    )
    
    category: Optional[str] = Field(
        None,
        description="Catalog category the request clearly maps to (e.g., 'cold_drink', 'snacks'), otherwise null"
    )
    
    max_price: Optional[float] = Field(
        None,
        description="Maximum price constraint"
    )
    
    min_price: Optional[float] = Field(
        None,
        description="Minimum price constraint"
    )
    
    quantity: int = Field(
        1,
        description="Quantity of items"
    )
    
    product_name: Optional[str] = Field(
        None,
        description="Specific product name if mentioned"
    )
    
    selection_strategy: Optional[Literal["CHEAPEST", "FIRST", "CONFIRM"]] = Field(
        None,
        description="Only set when the user explicitly asks for the cheapest option (CHEAPEST), "
                    "the first option (FIRST) or to choose themselves (CONFIRM); otherwise null"
    )


class PlannerOutput(BaseModel):
    """Complete planner output with execution plan"""
    intent: ShoppingIntent
    requires: List[str] = Field(
        description="List of required workflow steps"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for the intent classification"
    )
