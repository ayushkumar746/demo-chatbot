from typing import Dict, Optional

from app.config import settings
from app.schemas import Cart, CartItem, AddToCartRequest, AddToCartResponse
from app.services.product_service import product_service
from app.tools.cart_tools import update_cart_totals


# Mock cart database
MOCK_CARTS: Dict[str, Cart] = {}


class CartService:
    """Mock cart service for demo purposes"""
    
    def __init__(self):
        self.carts = MOCK_CARTS
    
    def get_cart(self, user_id: str, store_id: str) -> Cart:
        """
        Get or create a cart for the user.
        
        In production, this would call an external cart API.
        """
        cart_id = f"CART_{user_id}_{store_id}"
        
        # Carts are keyed by cart_id so add/remove/update can look them up directly
        if cart_id not in self.carts:
            self.carts[cart_id] = Cart(
                cart_id=cart_id,
                user_id=user_id,
                store_id=store_id,
                items=[],
                total_items=0,
                total_price=0.0
            )
        
        return self.carts[cart_id]
    
    def add_to_cart(self, request: AddToCartRequest) -> AddToCartResponse:
        """
        Add a product to the cart.
        
        In production, this would call an external cart API.
        """
        # Get the cart
        cart = self.carts.get(request.cart_id)
        if not cart:
            return AddToCartResponse(
                success=False,
                cart=None,
                message="Cart not found"
            )
        
        # Get product details
        product = product_service.get_product(request.product_id, cart.store_id)
        if not product:
            return AddToCartResponse(
                success=False,
                cart=cart,
                message="Product not found"
            )
        
        existing_item = self._find_item(cart, request.product_id)
        total_quantity = request.quantity + (existing_item.quantity if existing_item else 0)
        
        # Check inventory for the resulting quantity, not just the increment
        if not product_service.check_inventory(request.product_id, cart.store_id, total_quantity):
            return AddToCartResponse(
                success=False,
                cart=cart,
                message=f"{product.name} is out of stock or has insufficient inventory"
            )
        
        # Product already in cart: increase quantity (one line item per product)
        if existing_item:
            existing_item.quantity = total_quantity
            existing_item.total_price = existing_item.quantity * existing_item.price
            update_cart_totals(cart)
            return AddToCartResponse(
                success=True,
                cart=cart,
                message=f"Updated {product.name} quantity to {existing_item.quantity}"
            )
        
        # Add new item
        new_item = CartItem(
            product_id=product.id,
            name=product.name,
            quantity=request.quantity,
            price=product.price,
            total_price=product.price * request.quantity,
            image_url=product.image_url
        )
        cart.items.append(new_item)
        update_cart_totals(cart)
        
        return AddToCartResponse(
            success=True,
            cart=cart,
            message=f"Added {product.name} to cart"
        )
    
    @staticmethod
    def _find_item(cart: Cart, product_id: str) -> Optional[CartItem]:
        """Return the cart line for a product, if present."""
        return next((item for item in cart.items if item.product_id == product_id), None)
    
    def set_item_quantity(self, user_id: str, store_id: str, product_id: str, quantity: int) -> AddToCartResponse:
        """
        Set the absolute quantity of a product in the user's cart.
        
        Quantity 0 removes the line. Setting an absolute value (instead of
        incrementing) makes repeated or retried requests safe.
        """
        cart = self.get_cart(user_id, store_id)
        existing_item = self._find_item(cart, product_id)
        
        if quantity == 0:
            if existing_item:
                self.remove_from_cart(cart.cart_id, product_id)
            return AddToCartResponse(success=True, cart=cart, message="Item removed from cart")
        
        if quantity > settings.max_quantity_per_item:
            return AddToCartResponse(
                success=False, cart=cart,
                message=f"Maximum quantity per item is {settings.max_quantity_per_item}"
            )
        
        product = product_service.get_product(product_id, store_id)
        if not product:
            return AddToCartResponse(success=False, cart=cart, message="Product not found in this store")
        
        if not product_service.check_inventory(product_id, store_id, quantity):
            return AddToCartResponse(
                success=False, cart=cart,
                message=f"Only {product.inventory if product.available else 0} of {product.name} available"
            )
        
        if existing_item:
            self.update_cart_item(cart.cart_id, product_id, quantity)
            return AddToCartResponse(success=True, cart=cart, message=f"Updated {product.name} quantity to {quantity}")
        
        if len(cart.items) >= settings.max_cart_items:
            return AddToCartResponse(
                success=False, cart=cart,
                message=f"Maximum cart items is {settings.max_cart_items}"
            )
        
        return self.add_to_cart(AddToCartRequest(cart_id=cart.cart_id, product_id=product_id, quantity=quantity))
    
    def remove_from_cart(self, cart_id: str, product_id: str) -> Cart:
        """
        Remove a product from the cart.
        """
        cart = self.carts.get(cart_id)
        if cart:
            cart.items = [item for item in cart.items if item.product_id != product_id]
            update_cart_totals(cart)
        return cart
    
    def update_cart_item(self, cart_id: str, product_id: str, quantity: int) -> Cart:
        """
        Update quantity of a cart item.
        """
        cart = self.carts.get(cart_id)
        if cart:
            for item in cart.items:
                if item.product_id == product_id:
                    item.quantity = quantity
                    item.total_price = item.quantity * item.price
                    update_cart_totals(cart)
                    break
        return cart
    
    def clear_cart(self, cart_id: str) -> Cart:
        """
        Clear all items from the cart.
        """
        cart = self.carts.get(cart_id)
        if cart:
            cart.items = []
            update_cart_totals(cart)
        return cart


# Global instance
cart_service = CartService()
