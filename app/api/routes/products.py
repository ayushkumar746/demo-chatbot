import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.schemas import ProductListResponse
from app.services.product_service import product_service
from app.services.vector_store import VectorStoreError

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_PAGE_SIZE = 50


@router.get("/products", response_model=ProductListResponse, tags=["Products"])
async def list_products(
    store_id: str = Query(default=None, description="Store identifier (defaults to DEFAULT_STORE_ID)"),
    q: str = Query(default="", max_length=100, description="Keyword search over name, brand and category"),
    category: Optional[str] = Query(default=None, description="Exact category filter, e.g. cold_drink"),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=12, ge=1, le=MAX_PAGE_SIZE, description="Products per page"),
):
    """
    Browse the store catalog with keyword search and pagination.

    Reads product metadata from the local vector database; no Gemini calls.
    """
    store_id = store_id or settings.default_store_id
    try:
        if not product_service.store_exists(store_id):
            raise HTTPException(status_code=404, detail=f"Unknown store '{store_id}'")
        return product_service.list_products(store_id, query=q, category=category, page=page, page_size=page_size)
    except VectorStoreError as error:
        logger.error("Product listing unavailable: %s", error)
        raise HTTPException(status_code=503, detail="The product catalog is not initialized.")
