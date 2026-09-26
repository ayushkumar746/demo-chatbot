"""
Shared fixtures.

Unit/integration tests use `FakeGemini`, a deterministic stand-in for
`GeminiClient`, so they need no network or API key. Live tests against the
real Gemini API are in `test_live_gemini.py` and run only with RUN_LIVE_TESTS=1.
"""
import math
import re
from typing import List, Optional

import pytest

from app.schemas import PlannerOutput, ShoppingIntent
from app.services.cart_service import MOCK_CARTS
from app.services.gemini_client import GeminiError
from app.services.vector_store import ProductVectorStore, load_catalog

# Keyword -> concept dimension. Mimics how real embeddings group synonyms.
CONCEPTS = {
    "cold": 0, "soft": 0, "soda": 0, "carbonated": 0, "cola": 0, "fizzy": 0,
    "energy": 1, "caffeinated": 1,
    "mango": 2, "fruit": 2,
    "chips": 3, "snack": 3, "potato": 3,
    "water": 4,
    "beer": 5, "lager": 5, "malt": 5,
    "wine": 6, "grapes": 6,
}
DIMENSIONS = 7


def fake_embedding(text: str) -> List[float]:
    """Bag-of-concepts vector; unrelated text gets a uniform low-similarity vector."""
    vector = [0.0] * DIMENSIONS
    for word in re.findall(r"[a-z]+", text.lower()):
        if word in CONCEPTS:
            vector[CONCEPTS[word]] += 1.0
    if not any(vector):
        vector = [1.0] * DIMENSIONS
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector]


class FakeGemini:
    """Deterministic GeminiClient replacement for tests."""

    def __init__(self, planner_output: Optional[PlannerOutput] = None, error: Optional[GeminiError] = None):
        self.model = "fake-flash"
        self.embedding_model = "fake-embedding"
        self.embedding_dimensions = DIMENSIONS
        self.planner_output = planner_output
        self.error = error
        self.embed_calls = 0
        self.generate_calls = 0

    def generate_structured(self, system_instruction, prompt, response_schema, temperature=0.1):
        """Return the preset planner output, or raise the configured error."""
        self.generate_calls += 1
        if self.error:
            raise self.error
        return self.planner_output

    def embed(self, texts, task_type):
        """Embed with the keyword concept model (or raise the configured error)."""
        if self.error:
            raise self.error
        self.embed_calls += 1
        return [fake_embedding(text) for text in texts]


def make_planner_output(**intent_fields) -> PlannerOutput:
    """Build a PlannerOutput for an ADD_TO_CART intent with overrides."""
    fields = {"action": "ADD_TO_CART"}
    fields.update(intent_fields)
    return PlannerOutput(
        intent=ShoppingIntent(**fields),
        requires=["product_search", "price_filter", "cart_validation", "add_to_cart"],
        confidence=0.95,
    )


@pytest.fixture(autouse=True)
def no_seed_throttling(monkeypatch):
    """Fake embeddings have no quota, so tests seed without pacing."""
    from app.config import settings
    monkeypatch.setattr(settings, "seed_embeddings_per_minute", 0)


COLD_DRINK_UNDER_100 = dict(search_query="cold drink", category="cold_drink", max_price=100)


@pytest.fixture(scope="session")
def session_catalog():
    """The real sample catalog, loaded once."""
    return load_catalog()


@pytest.fixture
def catalog(session_catalog):
    """The real sample catalog."""
    return session_catalog


@pytest.fixture(scope="session")
def seeded_index_path(tmp_path_factory, session_catalog):
    """Seed the full catalog once per session; tests only read this index."""
    from app.config import settings
    original_rate = settings.seed_embeddings_per_minute
    settings.seed_embeddings_per_minute = 0
    path = tmp_path_factory.mktemp("shared") / "vector_db"
    ProductVectorStore(path=path, gemini=FakeGemini()).seed(session_catalog, progress=lambda message: None)
    settings.seed_embeddings_per_minute = original_rate
    return path


@pytest.fixture
def fake_gemini():
    """FakeGemini planning 'cold drink under ₹100' by default."""
    return FakeGemini(planner_output=make_planner_output(**COLD_DRINK_UNDER_100))


@pytest.fixture
def vector_store(seeded_index_path, fake_gemini):
    """A read-only view of the session's seeded vector store."""
    return ProductVectorStore(path=seeded_index_path, gemini=fake_gemini)


@pytest.fixture
def wired_app(monkeypatch, vector_store, fake_gemini):
    """Point the global agents/services at the fake Gemini and temp index; reset carts."""
    from app.agent.planner import planner_agent
    from app.services.product_service import product_service

    monkeypatch.setattr(product_service, "vector_store", vector_store)
    monkeypatch.setattr(planner_agent, "_gemini", fake_gemini)
    MOCK_CARTS.clear()
    yield fake_gemini
    MOCK_CARTS.clear()
