from typing import Dict, Any, Optional


def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Get user profile information.
    
    Deterministic function that would connect to user service.
    For now, returns mock data.
    """
    # Mock user data
    return {
        "user_id": user_id,
        "name": "Demo User",
        "email": "user@example.com",
        "preferred_store": "STORE_1",
        "membership_tier": "GOLD",
        "preferences": {
            "currency": "INR",
            "language": "en"
        }
    }


def get_user_subscription(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user subscription information.
    
    Deterministic function.
    """
    # Mock implementation
    return {
        "plan": "PREMIUM",
        "status": "ACTIVE",
        "renewal_date": "2024-12-31",
        "benefits": ["free_delivery", "exclusive_deals"]
    }


def get_delivery_address(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user's default delivery address.
    
    Deterministic function.
    """
    # Mock implementation
    return {
        "address_id": "ADDR1",
        "street": "123 Main Street",
        "city": "Mumbai",
        "state": "Maharashtra",
        "zip": "400001",
        "country": "India",
        "is_default": True
    }


def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """
    Get user preferences for shopping.
    
    Deterministic function.
    """
    # Mock implementation
    return {
        "default_quantity": 1,
        "auto_select_cheapest": True,
        "require_confirmation": False,
        "notification_enabled": True
    }
