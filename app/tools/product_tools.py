from typing import List, Optional
from app.schemas import Product
from app.config import settings


def format_price(amount: float) -> str:
    """
    Format a rupee amount for display, dropping a trailing ".0" (e.g. 45.0 -> "₹45").
    """
    return f"₹{int(amount)}" if float(amount).is_integer() else f"₹{amount:.2f}"


def filter_by_price(products: List[Product], max_price: Optional[float] = None, min_price: Optional[float] = None) -> List[Product]:
    """
    Deterministic Python function to filter products by price.
    
    This is a pure Python function - no LLM involved.
    """
    filtered = products
    
    if max_price is not None:
        filtered = [p for p in filtered if p.price <= max_price]
    
    if min_price is not None:
        filtered = [p for p in filtered if p.price >= min_price]
    
    return filtered


def filter_by_category(products: List[Product], category: str) -> List[Product]:
    """
    Deterministic Python function to filter products by category.
    """
    return [p for p in products if p.category.lower() == category.lower()]


def filter_by_availability(products: List[Product]) -> List[Product]:
    """
    Deterministic Python function to filter only available products.
    """
    return [p for p in products if p.available and p.inventory > 0]


def select_cheapest(products: List[Product]) -> Optional[Product]:
    """
    Deterministic Python function to select the cheapest product.
    """
    if not products:
        return None
    
    return min(products, key=lambda p: p.price)


def select_first(products: List[Product]) -> Optional[Product]:
    """
    Deterministic Python function to select the first product.
    """
    if not products:
        return None
    
    return products[0]


def select_product(products: List[Product], strategy: str = "CHEAPEST") -> Optional[Product]:
    """
    Deterministic product selection based on business policy.
    
    Args:
        products: List of candidate products
        strategy: Selection strategy (CHEAPEST, FIRST, CONFIRM)
    
    Returns:
        Selected product or None if multiple and strategy is CONFIRM
    """
    if not products:
        return None
    
    if len(products) == 1:
        return products[0]
    
    # Multiple products - apply selection policy
    if strategy == "CHEAPEST":
        return select_cheapest(products)
    elif strategy == "FIRST":
        return select_first(products)
    elif strategy == "CONFIRM":
        # Return None to indicate user confirmation needed
        return None
    
    # Default to cheapest
    return select_cheapest(products)


def format_product_list(products: List[Product]) -> str:
    """
    Format product list for display to user.
    """
    if not products:
        return "No products found."
    
    lines = []
    for i, product in enumerate(products, 1):
        lines.append(f"{i}. {product.name} — {format_price(product.price)}")
    
    return "\n".join(lines)
