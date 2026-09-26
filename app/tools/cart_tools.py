from typing import Optional
from app.schemas import Cart, CartItem, CartValidationResult, Product
from app.config import settings
from app.tools.product_tools import format_price


def validate_cart_addition(cart: Cart, product_id: str, quantity: int) -> CartValidationResult:
    """
    Deterministic Python function to validate cart addition.
    
    Validates:
    - Maximum quantity per item limit (a product already in the cart has its
      quantity increased, so the cart keeps one line item per product)
    - Maximum cart items limit
    """
    if quantity <= 0:
        return CartValidationResult(valid=False, reason="Quantity must be greater than 0")
    
    # Product already in cart: allowed as a quantity increase within the limit
    for item in cart.items:
        if item.product_id == product_id:
            existing_quantity = item.quantity
            new_quantity = existing_quantity + quantity
            
            if new_quantity > settings.max_quantity_per_item:
                return CartValidationResult(
                    valid=False,
                    reason=f"Cannot add {quantity} more. Maximum quantity per item is {settings.max_quantity_per_item}",
                    existing_quantity=existing_quantity
                )
            
            return CartValidationResult(valid=True, existing_quantity=existing_quantity)
    
    if quantity > settings.max_quantity_per_item:
        return CartValidationResult(
            valid=False,
            reason=f"Maximum quantity per item is {settings.max_quantity_per_item}"
        )
    
    # Check cart item limit
    if len(cart.items) >= settings.max_cart_items:
        return CartValidationResult(
            valid=False,
            reason=f"Cannot add more items. Maximum cart items is {settings.max_cart_items}"
        )
    
    return CartValidationResult(valid=True)


def validate_cart_removal(cart: Cart, product_id: str) -> CartValidationResult:
    """
    Deterministic Python function to validate cart removal.
    """
    for item in cart.items:
        if item.product_id == product_id:
            return CartValidationResult(valid=True)
    
    return CartValidationResult(
        valid=False,
        reason="Product not found in cart"
    )


def validate_cart_update(cart: Cart, product_id: str, new_quantity: int) -> CartValidationResult:
    """
    Deterministic Python function to validate cart quantity update.
    """
    if new_quantity <= 0:
        return CartValidationResult(
            valid=False,
            reason="Quantity must be greater than 0"
        )
    
    if new_quantity > settings.max_quantity_per_item:
        return CartValidationResult(
            valid=False,
            reason=f"Maximum quantity per item is {settings.max_quantity_per_item}"
        )
    
    for item in cart.items:
        if item.product_id == product_id:
            return CartValidationResult(valid=True)
    
    return CartValidationResult(
        valid=False,
        reason="Product not found in cart"
    )


def calculate_cart_total(cart: Cart) -> float:
    """
    Deterministic Python function to calculate cart total.
    """
    return sum(item.total_price for item in cart.items)


def update_cart_totals(cart: Cart) -> Cart:
    """
    Deterministic Python function to update cart totals.
    """
    cart.total_items = sum(item.quantity for item in cart.items)
    cart.total_price = calculate_cart_total(cart)
    return cart


def format_cart_summary(cart: Cart) -> str:
    """
    Format cart summary for display to user.
    """
    if not cart.items:
        return "Your cart is empty."
    
    item_label = "item" if cart.total_items == 1 else "items"
    lines = [f"Cart ({cart.total_items} {item_label}):"]
    for item in cart.items:
        lines.append(f"  - {item.name} x{item.quantity} — {format_price(item.total_price)}")
    
    lines.append(f"\nTotal: {format_price(cart.total_price)}")
    return "\n".join(lines)
