from pathlib import Path
from typing import List, Literal

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables and `.env`."""

    # Application
    app_name: str = "Chatbot API"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Google Gemini (the only LLM provider)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_dimensions: int = 768
    gemini_timeout_seconds: int = 30
    gemini_max_retries: int = 2

    # Seed throttling; the free tier allows 100 embedded texts per minute (0 disables)
    seed_embeddings_per_minute: int = 90

    # Local vector database (Chroma)
    vector_db_path: str = "data/vector_db"
    vector_collection_name: str = "products"
    # A JSON file or a directory of JSON files
    product_catalog_path: str = "data/products"

    # Semantic search tuning
    search_top_k: int = 100
    # Cosine distances (0 = identical), calibrated for gemini-embedding-001 on the sample catalog.
    # Candidates beyond the absolute ceiling are irrelevant (e.g. "laptop" scores ~0.43+).
    search_max_distance: float = 0.41
    # Candidates must also be within this margin of the best match, which separates
    # e.g. sodas (~0.29) from fruit drinks (~0.33) for the query "cold drink".
    search_relevance_margin: float = 0.04

    # Browser origins allowed to call the API (Vite dev server, preview, legacy static UI)
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://localhost:3000",
    ]

    # Base URL used to build absolute product image URLs
    public_base_url: str = "http://localhost:8000"

    # Store
    default_store_id: str = "STORE_1"

    # Selection Policy
    selection_policy: Literal["CHEAPEST_MATCH", "ASK_CONFIRMATION", "FIRST_MATCH"] = "CHEAPEST_MATCH"
    # Most relevant options shown when the user is asked to choose
    max_confirmation_options: int = 5

    # Cart Validation
    max_cart_items: int = 50
    max_quantity_per_item: int = 10

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        case_sensitive = False
        extra = "ignore"

    def resolve_path(self, path: str) -> Path:
        """Resolve a configured path relative to the project root unless absolute."""
        candidate = Path(path)
        return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


settings = Settings()
