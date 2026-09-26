import logging

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.schemas import AddToCartResponse, Cart, CartItemQuantityRequest
from app.services.cart_service import cart_service
from app.services.vector_store import VectorStoreError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/cart", response_model=Cart, tags=["Cart"])
async def get_cart(
    user_id: str = Query(min_length=1, description="User identifier"),
    store_id: str = Query(default=None, description="Store identifier (defaults to DEFAULT_STORE_ID)"),
):
    """Get the user's current cart (the same cart the chatbot updates)."""
    return cart_service.get_cart(user_id, store_id or settings.default_store_id)


@router.put("/cart/items/{product_id}", response_model=AddToCartResponse, tags=["Cart"])
async def set_cart_item_quantity(product_id: str, request: CartItemQuantityRequest):
    """
    Set the absolute quantity of a product in the cart; 0 removes it.

    The cart keeps one line item per product. Returns the updated cart, or
    HTTP 400 with a client-safe reason when the change violates a business rule.
    """
    try:
        result = cart_service.set_item_quantity(
            request.user_id, request.store_id, product_id, request.quantity
        )
    except VectorStoreError as error:
        logger.error("Cart update failed, product catalog unavailable: %s", error)
        raise HTTPException(status_code=503, detail="The product catalog is not initialized.")

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result
