"""Tests for Gemini configuration, initialization and error handling."""
from types import SimpleNamespace

import httpx
import pytest
from google.genai import errors as genai_errors
from pydantic import BaseModel

from app.config import settings
from app.services import gemini_client as gemini_module
from app.services.gemini_client import (
    GeminiAuthenticationError,
    GeminiClient,
    GeminiConfigurationError,
    GeminiModelNotFoundError,
    GeminiRateLimitError,
    GeminiResponseError,
    GeminiUnavailableError,
)


class Probe(BaseModel):
    max_price: float


def api_error(code: int, message: str) -> genai_errors.APIError:
    status = {400: "INVALID_ARGUMENT", 404: "NOT_FOUND", 429: "RESOURCE_EXHAUSTED", 503: "UNAVAILABLE"}
    error_class = genai_errors.ServerError if code >= 500 else genai_errors.ClientError
    return error_class(code, {"error": {"code": code, "message": message, "status": status.get(code, "")}})


class StubModels:
    """Stands in for `genai.Client().models` and replays scripted outcomes."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def _next(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def generate_content(self, **kwargs):
        return self._next(**kwargs)

    def embed_content(self, **kwargs):
        return self._next(**kwargs)


def client_with(outcomes, **kwargs) -> GeminiClient:
    client = GeminiClient(api_key="test-key", **kwargs)
    client._client = SimpleNamespace(models=StubModels(outcomes))
    return client


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(gemini_module.time, "sleep", lambda seconds: None)


def test_model_configuration_comes_from_settings():
    client = GeminiClient(api_key="test-key")
    assert client.model == settings.gemini_model
    assert client.embedding_model == settings.gemini_embedding_model
    assert client.embedding_dimensions == settings.gemini_embedding_dimensions


def test_configured_model_is_not_obsolete():
    assert settings.gemini_model
    assert settings.gemini_model != "gemini-pro"


def test_missing_api_key_raises_configuration_error():
    with pytest.raises(GeminiConfigurationError):
        GeminiClient(api_key="").client


def test_sdk_client_is_initialized_lazily_with_key():
    client = GeminiClient(api_key="test-key", model="some-flash-model")
    assert client._client is None
    assert client.client is not None
    assert client.model == "some-flash-model"


def test_generate_structured_uses_configured_model_and_parses_output():
    response = SimpleNamespace(parsed=Probe(max_price=100), text='{"max_price": 100}')
    client = client_with([response], model="my-model")
    result = client.generate_structured("system", "prompt", Probe)
    assert result == Probe(max_price=100)
    assert client._client.models.calls[0]["model"] == "my-model"


def test_generate_structured_falls_back_to_text_parsing():
    client = client_with([SimpleNamespace(parsed=None, text='{"max_price": 55}')])
    assert client.generate_structured("system", "prompt", Probe).max_price == 55


def test_generate_structured_rejects_invalid_output():
    client = client_with([SimpleNamespace(parsed=None, text="not json")])
    with pytest.raises(GeminiResponseError):
        client.generate_structured("system", "prompt", Probe)


@pytest.mark.parametrize(
    "error, expected",
    [
        (api_error(400, "API key not valid. Please pass a valid API key."), GeminiAuthenticationError),
        (api_error(403, "Permission denied"), GeminiAuthenticationError),
        (api_error(404, "models/gemini-pro is not found for API version v1beta"), GeminiModelNotFoundError),
        (api_error(400, "Bad request"), GeminiResponseError),
    ],
)
def test_non_transient_errors_are_translated_without_retry(error, expected):
    client = client_with([error, SimpleNamespace(parsed=Probe(max_price=1), text="")])
    with pytest.raises(expected) as raised:
        client.generate_structured("system", "prompt", Probe)
    assert len(client._client.models.calls) == 1
    # The client-facing message never contains raw SDK text
    assert "v1beta" not in raised.value.user_message


def test_rate_limit_is_retried_then_reported(monkeypatch):
    monkeypatch.setattr(settings, "gemini_max_retries", 2)
    client = client_with([api_error(429, "quota")] * 3)
    with pytest.raises(GeminiRateLimitError):
        client.generate_structured("system", "prompt", Probe)
    assert len(client._client.models.calls) == 3


def test_transient_unavailability_recovers_on_retry():
    response = SimpleNamespace(parsed=Probe(max_price=100), text="")
    client = client_with([api_error(503, "overloaded"), response])
    assert client.generate_structured("system", "prompt", Probe).max_price == 100


def test_network_failure_maps_to_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "gemini_max_retries", 0)
    client = client_with([httpx.ConnectError("connection refused")])
    with pytest.raises(GeminiUnavailableError):
        client.generate_structured("system", "prompt", Probe)


def test_embed_returns_vectors_with_configured_dimensions():
    response = SimpleNamespace(embeddings=[SimpleNamespace(values=[0.1, 0.2]), SimpleNamespace(values=[0.3, 0.4])])
    client = client_with([response], embedding_model="emb-model", embedding_dimensions=2)
    assert client.embed(["a", "b"], task_type="RETRIEVAL_DOCUMENT") == [[0.1, 0.2], [0.3, 0.4]]
    call = client._client.models.calls[0]
    assert call["model"] == "emb-model"
    assert call["config"].output_dimensionality == 2
    assert call["config"].task_type == "RETRIEVAL_DOCUMENT"


def test_embed_rejects_mismatched_response():
    client = client_with([SimpleNamespace(embeddings=[SimpleNamespace(values=[0.1])])])
    with pytest.raises(GeminiResponseError):
        client.embed(["a", "b"], task_type="RETRIEVAL_DOCUMENT")
