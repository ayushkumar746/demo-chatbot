from pydantic import BaseModel, Field
from typing import Optional, List


class Product(BaseModel):
    """Product schema"""
    id: str = Field(description="Unique product identifier")
    name: str = Field(description="Product name")
    price: float = Field(description="Product price")
    category: str = Field(description="Product category")
    description: Optional[str] = Field(None, description="Product description")
    brand: Optional[str] = Field(None, description="Product brand")
    currency: str = Field("INR", description="Price currency")
    image_url: Optional[str] = Field(None, description="Product image URL")
    available: bool = Field(True, description="Whether product is available")
    inventory: int = Field(0, description="Available inventory count")
    store_id: str = Field(description="Store identifier")


class ProductSearchRequest(BaseModel):
    """Request for product search"""
    query: str = Field(description="Search query")
    store_id: str = Field(description="Store identifier")
    category: Optional[str] = Field(None, description="Optional category filter")


class ProductSearchResponse(BaseModel):
    """Response from product search"""
    products: List[Product] = Field(description="List of matching products")
    total: int = Field(description="Total number of results")


class ProductListResponse(BaseModel):
    """A page of products for browsing"""
    items: List[Product] = Field(description="Products on this page")
    total: int = Field(description="Total matching products")
    page: int = Field(description="Current page (1-based)")
    page_size: int = Field(description="Products per page")
    total_pages: int = Field(description="Total number of pages")
