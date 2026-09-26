import logging
from typing import List, Optional

from app.config import settings
import math

from app.schemas import Product, ProductListResponse, ProductSearchRequest, ProductSearchResponse
from app.services.vector_store import ProductVectorStore, ScoredProduct

logger = logging.getLogger(__name__)


def select_relevant(scored: List[ScoredProduct]) -> List[ScoredProduct]:
    """
    Keep only semantically relevant candidates.

    A candidate must be under the absolute distance ceiling and within the
    relevance margin of the best match. Input order (most relevant first) is kept.
    """
    if not scored:
        return []
    best_distance = scored[0].distance
    cutoff = min(settings.search_max_distance, best_distance + settings.search_relevance_margin)
    return [candidate for candidate in scored if candidate.distance <= cutoff]


def matches_keywords(product: Product, query: str) -> bool:
    """True when every query word appears in the product's name, brand or category."""
    haystack = " ".join([product.name, product.brand or "", product.category.replace("_", " ")]).lower()
    return all(word in haystack for word in query.lower().split())


class ProductService:
    """Product catalog backed by the local Chroma vector index."""

    def __init__(self, vector_store: Optional[ProductVectorStore] = None):
        self.vector_store = vector_store or ProductVectorStore()

    def search_products(self, request: ProductSearchRequest) -> ProductSearchResponse:
        """
        Semantic product search within a single store.

        Returns relevant candidates ordered by similarity. When a category is
        known it narrows the vector query; price and availability filtering is
        done separately by deterministic tools.
        """
        scored = self.vector_store.search(
            request.query, store_id=request.store_id, category=request.category
        )
        relevant = select_relevant(scored)
        logger.info(
            "Semantic search query=%r store=%s: %d candidates, %d relevant",
            request.query, request.store_id, len(scored), len(relevant),
        )
        products = [candidate.product for candidate in relevant]
        return ProductSearchResponse(products=products, total=len(products))

    def list_products(
        self,
        store_id: str,
        query: str = "",
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 12,
    ) -> ProductListResponse:
        """
        Browse a store's catalog with keyword search and pagination.
        
        Uses stored metadata only (no Gemini calls), so browsing never consumes
        embedding quota. Chat requests use semantic search instead.
        """
        products = self.vector_store.list_products(store_id)
        if category:
            products = [product for product in products if product.category == category]
        if query.strip():
            products = [product for product in products if matches_keywords(product, query)]
        products.sort(key=lambda product: (product.name.lower(), product.id))
        
        total = len(products)
        total_pages = max(1, math.ceil(total / page_size))
        start = (page - 1) * page_size
        return ProductListResponse(
            items=products[start:start + page_size],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    def get_product(self, product_id: str, store_id: str) -> Optional[Product]:
        """Get a specific product by ID from the given store."""
        return self.vector_store.get_product(product_id, store_id)

    def check_inventory(self, product_id: str, store_id: str, quantity: int) -> bool:
        """Check if the product is available with sufficient stock."""
        product = self.get_product(product_id, store_id)
        return bool(product and product.available and product.inventory >= quantity)

    def store_exists(self, store_id: str) -> bool:
        """Whether the store has any products in the catalog."""
        return self.vector_store.store_exists(store_id)

    def categories(self) -> List[str]:
        """Distinct product categories in the catalog."""
        return self.vector_store.categories()


# Global instance
product_service = ProductService()
