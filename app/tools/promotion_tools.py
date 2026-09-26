from typing import List, Optional, Dict, Any


def get_promotions(store_id: str, product_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get available promotions for a store or specific product.
    
    This is a deterministic function that would connect to a promotion service.
    For now, returns mock data.
    """
    # Mock promotions data
    promotions = [
        {
            "id": "PROMO1",
            "name": "10% Off Cold Drinks",
            "type": "PERCENTAGE",
            "value": 10,
            "category": "cold_drink",
            "min_purchase": 0,
            "max_discount": 50
        },
        {
            "id": "PROMO2",
            "name": "Buy 2 Get 1 Free",
            "type": "BOGO",
            "value": 1,
            "category": "snacks",
            "min_quantity": 2
        }
    ]
    
    if product_id:
        # Filter promotions applicable to specific product
        # In real implementation, this would check product category
        return promotions
    
    return promotions


def calculate_discount(price: float, promotion: Dict[str, Any]) -> float:
    """
    Calculate discount amount based on promotion.
    
    Deterministic Python function.
    """
    promo_type = promotion.get("type")
    value = promotion.get("value", 0)
    
    if promo_type == "PERCENTAGE":
        discount = price * (value / 100)
        max_discount = promotion.get("max_discount")
        if max_discount and discount > max_discount:
            discount = max_discount
        return discount
    
    elif promo_type == "FIXED":
        return min(value, price)
    
    return 0.0


def check_ebt_eligibility(product_id: str) -> bool:
    """
    Check if a product is EBT (SNAP) eligible.
    
    Deterministic function.
    """
    # Mock implementation - in real system, this would check product database
    ebt_eligible_categories = ["groceries", "food", "beverages"]
    # For demo, assume all products are eligible
    return True


def get_membership_benefits(user_id: str) -> Dict[str, Any]:
    """
    Get membership benefits for a user.
    
    Deterministic function.
    """
    # Mock implementation
    return {
        "tier": "GOLD",
        "discount_percentage": 5,
        "free_shipping": True,
        "exclusive_offers": True
    }
