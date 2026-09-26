from pydantic import BaseModel, Field
from typing import Optional, List


class CartItem(BaseModel):
    """Item in shopping cart"""
    product_id: str = Field(description="Product identifier")
    name: str = Field(description="Product name")
    quantity: int = Field(description="Quantity in cart")
    price: float = Field(description="Price per unit")
    total_price: float = Field(description="Total price for this item")
    image_url: Optional[str] = Field(None, description="Product image URL")


class Cart(BaseModel):
    """Shopping cart schema"""
    cart_id: str = Field(description="Cart identifier")
    user_id: str = Field(description="User identifier")
    store_id: str = Field(description="Store identifier")
    items: List[CartItem] = Field(default_factory=list, description="Items in cart")
    total_items: int = Field(0, description="Total number of items")
    total_price: float = Field(0.0, description="Total cart price")


class CartValidationResult(BaseModel):
    """Result of cart validation"""
    valid: bool = Field(description="Whether the operation is valid")
    reason: Optional[str] = Field(None, description="Reason if invalid")
    existing_quantity: Optional[int] = Field(None, description="Existing quantity if already in cart")


class AddToCartRequest(BaseModel):
    """Request to add item to cart"""
    cart_id: str = Field(description="Cart identifier")
    product_id: str = Field(description="Product identifier")
    quantity: int = Field(1, description="Quantity to add")


class AddToCartResponse(BaseModel):
    """Response from add to cart operation"""
    success: bool = Field(description="Whether operation succeeded")
    cart: Optional[Cart] = Field(None, description="Updated cart")
    message: str = Field(description="Operation message")


class CartItemQuantityRequest(BaseModel):
    """Set the absolute quantity of a product in a cart (0 removes it)"""
    user_id: str = Field(min_length=1, description="User identifier")
    store_id: str = Field(min_length=1, description="Store identifier")
    quantity: int = Field(ge=0, description="New quantity; 0 removes the item")
