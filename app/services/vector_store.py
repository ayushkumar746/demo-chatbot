"""
Local, persistent product vector index backed by Chroma.

Products are embedded with Gemini embeddings and stored on disk under
`VECTOR_DB_PATH` together with their metadata, so the demo needs no
external vector database.
"""
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.schemas import Product
from app.services.product_images import image_url_for
from app.services.gemini_client import GeminiClient, GeminiRateLimitError, get_gemini_client

logger = logging.getLogger(__name__)

DOCUMENT_TASK_TYPE = "RETRIEVAL_DOCUMENT"
QUERY_TASK_TYPE = "RETRIEVAL_QUERY"
EMBEDDING_BATCH_SIZE = 50
SECONDS_PER_MINUTE = 60
RATE_LIMIT_RETRY_ATTEMPTS = 5
DEFAULT_RATE_LIMIT_WAIT_SECONDS = 60.0
QUERY_EMBEDDING_CACHE_SIZE = 1024
RETRY_DELAY_PATTERN = re.compile(r"retry in ([\d.]+)s", re.IGNORECASE)


class VectorStoreError(Exception):
    """The product index is missing, incompatible or unreadable."""


@dataclass
class SeedReport:
    """Summary of a seed run."""

    total: int
    embedded: int
    unchanged: int
    removed: int
    recreated: bool


@dataclass
class ScoredProduct:
    """A product returned by semantic search with its cosine distance."""

    product: Product
    distance: float


def build_search_text(record: Dict) -> str:
    """Build the text that is embedded for a catalog record."""
    category = record["category"].replace("_", " ")
    return (
        f"{record['name']}. {record['description']} "
        f"Category: {category}. Brand: {record['brand']}."
    )


def _content_hash(record: Dict, embedding_signature: str) -> str:
    """Hash of everything that affects a record's vector or metadata."""
    payload = json.dumps(record, sort_keys=True) + embedding_signature
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _record_to_metadata(record: Dict, content_hash: str) -> Dict:
    """Flatten a catalog record into Chroma-compatible metadata."""
    return {
        "product_id": record["product_id"],
        "name": record["name"],
        "description": record["description"],
        "category": record["category"],
        "brand": record["brand"],
        "price": float(record["price"]),
        "currency": record.get("currency", "INR"),
        "store_id": record["store_id"],
        "available": bool(record["available"]),
        "stock": int(record["stock"]),
        "content_hash": content_hash,
    }


def metadata_to_product(metadata: Dict) -> Product:
    """Convert stored metadata back into the application's Product schema."""
    return Product(
        id=metadata["product_id"],
        name=metadata["name"],
        price=metadata["price"],
        category=metadata["category"],
        description=metadata.get("description"),
        brand=metadata.get("brand"),
        currency=metadata.get("currency", "INR"),
        image_url=image_url_for(metadata["category"], metadata.get("brand") or ""),
        available=metadata["available"],
        inventory=metadata["stock"],
        store_id=metadata["store_id"],
    )


def load_catalog(path: Optional[Path] = None) -> List[Dict]:
    """
    Load the product catalog used to seed the index.

    `path` may be a single JSON file or a directory, in which case every
    `*.json` file in it is loaded (sorted by name).
    """
    catalog_path = Path(path or settings.resolve_path(settings.product_catalog_path))
    files = sorted(catalog_path.glob("*.json")) if catalog_path.is_dir() else [catalog_path]
    if not files:
        raise ValueError(f"No catalog JSON files found in {catalog_path}")

    records = []
    for catalog_file in files:
        with open(catalog_file, encoding="utf-8") as handle:
            records.extend(json.load(handle))

    product_ids = [record["product_id"] for record in records]
    if len(product_ids) != len(set(product_ids)):
        raise ValueError(f"Duplicate product_id values in {catalog_path}")
    return records


class ProductVectorStore:
    """Persistent Chroma collection of products with Gemini embeddings."""

    def __init__(
        self,
        path: Optional[Path] = None,
        collection_name: Optional[str] = None,
        gemini: Optional[GeminiClient] = None,
    ):
        self.path = Path(path) if path else settings.resolve_path(settings.vector_db_path)
        self.collection_name = collection_name or settings.vector_collection_name
        self._gemini = gemini
        self._client = None
        self._query_embedding_cache: Dict[str, List[float]] = {}

    @property
    def gemini(self) -> GeminiClient:
        """Gemini client used for embeddings."""
        if self._gemini is None:
            self._gemini = get_gemini_client()
        return self._gemini

    @property
    def embedding_signature(self) -> str:
        """Identifies the embedding space; vectors from different spaces must not mix."""
        return f"{self.gemini.embedding_model}:{self.gemini.embedding_dimensions}"

    @property
    def client(self):
        """Chroma persistent client, created on first use."""
        if self._client is None:
            self.path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(self.path),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _create_collection(self):
        return self.client.create_collection(
            name=self.collection_name,
            embedding_function=None,
            metadata={
                "hnsw:space": "cosine",
                "embedding_signature": self.embedding_signature,
            },
        )

    def _get_collection(self):
        """Open the existing collection, verifying it was built with the current embedding model."""
        try:
            collection = self.client.get_collection(self.collection_name, embedding_function=None)
        except Exception as error:
            raise VectorStoreError(
                "Product index not found. Run `python seed_products.py` first."
            ) from error

        stored_signature = (collection.metadata or {}).get("embedding_signature")
        if stored_signature != self.embedding_signature:
            raise VectorStoreError(
                f"Product index was built with '{stored_signature}' but the app is configured "
                f"for '{self.embedding_signature}'. Re-run `python seed_products.py`."
            )
        return collection

    def count(self) -> int:
        """Number of indexed products (raises VectorStoreError if not seeded)."""
        return self._get_collection().count()

    def seed(self, records: List[Dict], progress=print) -> SeedReport:
        """
        Idempotently sync the index with `records`.

        Upserts by product_id, re-embeds only changed records, deletes records
        no longer in the catalog, and rebuilds the collection if the embedding
        model changed.
        """
        recreated = False
        try:
            collection = self._get_collection()
        except VectorStoreError:
            existing_names = [c.name if hasattr(c, "name") else c for c in self.client.list_collections()]
            if self.collection_name in existing_names:
                progress("Embedding model changed; rebuilding the product index.")
                self.client.delete_collection(self.collection_name)
            collection = self._create_collection()
            recreated = True

        existing = collection.get(include=["metadatas"])
        existing_hashes = {
            product_id: (metadata or {}).get("content_hash")
            for product_id, metadata in zip(existing["ids"], existing["metadatas"])
        }

        signature = self.embedding_signature
        changed = [
            record for record in records
            if existing_hashes.get(record["product_id"]) != _content_hash(record, signature)
        ]
        progress(f"{len(records)} products in catalog, {len(changed)} new or changed.")

        for start in range(0, len(changed), EMBEDDING_BATCH_SIZE):
            batch = changed[start:start + EMBEDDING_BATCH_SIZE]
            documents = [build_search_text(record) for record in batch]
            progress(
                f"Embedding products {start + 1}-{start + len(batch)} of {len(changed)} "
                f"with {self.gemini.embedding_model}..."
            )
            embeddings = self._embed_documents_with_quota(documents, progress)
            collection.upsert(
                ids=[record["product_id"] for record in batch],
                documents=documents,
                embeddings=embeddings,
                metadatas=[
                    _record_to_metadata(record, _content_hash(record, signature))
                    for record in batch
                ],
            )

            is_last_batch = start + EMBEDDING_BATCH_SIZE >= len(changed)
            if not is_last_batch and settings.seed_embeddings_per_minute > 0:
                # Stay under the per-minute embedding quota (free tier counts each text)
                time.sleep(SECONDS_PER_MINUTE * len(batch) / settings.seed_embeddings_per_minute)

        catalog_ids = {record["product_id"] for record in records}
        stale_ids = [product_id for product_id in existing_hashes if product_id not in catalog_ids]
        if stale_ids:
            progress(f"Removing {len(stale_ids)} products no longer in the catalog.")
            collection.delete(ids=stale_ids)

        return SeedReport(
            total=len(records),
            embedded=len(changed),
            unchanged=len(records) - len(changed),
            removed=len(stale_ids),
            recreated=recreated,
        )

    def _embed_documents_with_quota(self, documents: List[str], progress) -> List[List[float]]:
        """
        Embed a seed batch, waiting out quota errors using Gemini's suggested delay.

        Only used by the offline seed, where waiting is acceptable; API requests
        fail fast instead. Batches already upserted are kept, so an aborted seed
        resumes where it stopped.
        """
        for attempt in range(1, RATE_LIMIT_RETRY_ATTEMPTS + 1):
            try:
                return self.gemini.embed(documents, task_type=DOCUMENT_TASK_TYPE)
            except GeminiRateLimitError as error:
                if attempt == RATE_LIMIT_RETRY_ATTEMPTS:
                    raise
                match = RETRY_DELAY_PATTERN.search(error.detail)
                wait = float(match.group(1)) + 1 if match else DEFAULT_RATE_LIMIT_WAIT_SECONDS
                progress(f"Embedding quota reached; waiting {wait:.0f}s before retrying...")
                time.sleep(wait)

    def _embed_query(self, query: str) -> List[float]:
        """Embed a search query, caching results to save embedding quota on repeated queries."""
        key = f"{self.embedding_signature}|{query.strip().lower()}"
        if key not in self._query_embedding_cache:
            if len(self._query_embedding_cache) >= QUERY_EMBEDDING_CACHE_SIZE:
                self._query_embedding_cache.pop(next(iter(self._query_embedding_cache)))
            self._query_embedding_cache[key] = self.gemini.embed([query], task_type=QUERY_TASK_TYPE)[0]
        return self._query_embedding_cache[key]

    def search(
        self,
        query: str,
        store_id: str,
        category: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[ScoredProduct]:
        """Semantic search restricted to one store (and optionally a category), ordered by relevance."""
        collection = self._get_collection()
        query_embedding = self._embed_query(query)
        where = {"store_id": store_id}
        if category:
            where = {"$and": [{"store_id": store_id}, {"category": category}]}
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k or settings.search_top_k,
            where=where,
            include=["metadatas", "distances"],
        )
        return [
            ScoredProduct(product=metadata_to_product(metadata), distance=distance)
            for metadata, distance in zip(results["metadatas"][0], results["distances"][0])
        ]

    def get_product(self, product_id: str, store_id: str) -> Optional[Product]:
        """Fetch one product by id, restricted to a store."""
        result = self._get_collection().get(ids=[product_id], include=["metadatas"])
        for metadata in result["metadatas"]:
            if metadata and metadata["store_id"] == store_id:
                return metadata_to_product(metadata)
        return None

    def list_products(self, store_id: str) -> List[Product]:
        """All products of a store (metadata only; no embedding calls)."""
        result = self._get_collection().get(where={"store_id": store_id}, include=["metadatas"])
        return [metadata_to_product(metadata) for metadata in result["metadatas"] if metadata]

    def store_exists(self, store_id: str) -> bool:
        """Whether any product is indexed for the store."""
        result = self._get_collection().get(where={"store_id": store_id}, limit=1)
        return bool(result["ids"])

    def categories(self) -> List[str]:
        """Distinct product categories present in the index."""
        result = self._get_collection().get(include=["metadatas"])
        return sorted({metadata["category"] for metadata in result["metadatas"] if metadata})
