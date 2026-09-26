"""
Seed the local product vector database.

Loads the sample catalog, embeds each product with Gemini and upserts it
into the persistent Chroma index. Safe to run repeatedly: unchanged products
are skipped and no duplicates are created.

Usage:
    python seed_products.py
"""
import sys

from app.config import settings
from app.services.gemini_client import GeminiError
from app.services.vector_store import ProductVectorStore, VectorStoreError, load_catalog


def main() -> int:
    """Run the seed and return a process exit code."""
    catalog_path = settings.resolve_path(settings.product_catalog_path)
    store = ProductVectorStore()

    print(f"Catalog:          {catalog_path}")
    print(f"Vector DB:        {store.path} (collection '{store.collection_name}')")
    print(f"Embedding model:  {settings.gemini_embedding_model} ({settings.gemini_embedding_dimensions} dims)")

    try:
        records = load_catalog(catalog_path)
        report = store.seed(records)
        indexed = store.count()
    except GeminiError as error:
        print(f"\nERROR: {error.user_message}\n  Details: {error.detail}", file=sys.stderr)
        return 1
    except (VectorStoreError, OSError, ValueError, KeyError) as error:
        print(f"\nERROR: Failed to seed products: {error}", file=sys.stderr)
        return 1

    print(
        f"\nDone. embedded={report.embedded} unchanged={report.unchanged} "
        f"removed={report.removed} rebuilt={report.recreated} indexed={indexed}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
