"""
Google Gemini integration.

All communication with Gemini (structured generation and embeddings) goes
through `GeminiClient`, so the rest of the application never touches the
SDK directly and never sees raw SDK exceptions.
"""
import logging
import time
from typing import List, Optional, Type, TypeVar

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)

TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}
RETRY_BASE_DELAY_SECONDS = 1.0


class GeminiError(Exception):
    """Base class for client-safe Gemini failures."""

    user_message = "The AI service failed to process the request."

    def __init__(self, detail: str = ""):
        super().__init__(detail or self.user_message)
        self.detail = detail


class GeminiConfigurationError(GeminiError):
    """Gemini is not configured (for example, a missing API key)."""

    user_message = "Gemini is not configured. Set GEMINI_API_KEY and GEMINI_MODEL."


class GeminiAuthenticationError(GeminiError):
    """The Gemini API key was rejected."""

    user_message = "The Gemini API key is invalid or not authorized."


class GeminiModelNotFoundError(GeminiError):
    """The configured Gemini model does not exist or is not available."""

    user_message = "The configured Gemini model is not available. Check GEMINI_MODEL / GEMINI_EMBEDDING_MODEL."


class GeminiRateLimitError(GeminiError):
    """Gemini quota or rate limit was exceeded."""

    user_message = "The Gemini API rate limit was exceeded. Please try again shortly."


class GeminiUnavailableError(GeminiError):
    """Gemini could not be reached or returned a server error."""

    user_message = "The Gemini API is currently unavailable. Please try again shortly."


class GeminiResponseError(GeminiError):
    """Gemini returned a response the application could not use."""

    user_message = "The Gemini API returned an unexpected response."


def _translate_api_error(error: genai_errors.APIError, model: str) -> GeminiError:
    """Map an SDK APIError to a client-safe application error."""
    message = str(error.message or error)
    detail = f"{error.code} {error.status}: {message}"

    if error.code in (401, 403) or "API key" in message:
        return GeminiAuthenticationError(detail)
    if error.code == 404:
        return GeminiModelNotFoundError(f"model={model}: {detail}")
    if error.code == 429:
        return GeminiRateLimitError(detail)
    if error.code >= 500:
        return GeminiUnavailableError(detail)
    return GeminiResponseError(detail)


class GeminiClient:
    """Thin wrapper around the official `google-genai` SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        embedding_model: Optional[str] = None,
        embedding_dimensions: Optional[int] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.embedding_model = embedding_model or settings.gemini_embedding_model
        self.embedding_dimensions = embedding_dimensions or settings.gemini_embedding_dimensions
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        """Create the SDK client lazily so the app can start without a key."""
        if self._client is None:
            if not self.api_key:
                raise GeminiConfigurationError("GEMINI_API_KEY is not set")
            if not self.model:
                raise GeminiConfigurationError("GEMINI_MODEL is not set")
            self._client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=settings.gemini_timeout_seconds * 1000),
            )
        return self._client

    def _call_with_retries(self, operation, model: str):
        """Run an SDK call, retrying only transient failures with exponential backoff."""
        attempts = settings.gemini_max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                return operation()
            except genai_errors.APIError as error:
                translated = _translate_api_error(error, model)
                retryable = error.code in TRANSIENT_STATUS_CODES
            except (httpx.TimeoutException, httpx.TransportError) as error:
                translated = GeminiUnavailableError(f"{type(error).__name__}: {error}")
                retryable = True

            if not retryable or attempt == attempts:
                logger.error("Gemini call failed (model=%s): %s", model, translated.detail)
                raise translated

            delay = RETRY_BASE_DELAY_SECONDS * 2 ** (attempt - 1)
            logger.warning(
                "Gemini transient failure (model=%s, attempt %d/%d), retrying in %.1fs: %s",
                model, attempt, attempts, delay, translated.detail,
            )
            time.sleep(delay)

    def generate_structured(
        self,
        system_instruction: str,
        prompt: str,
        response_schema: Type[SchemaT],
        temperature: float = 0.1,
    ) -> SchemaT:
        """Generate a response constrained to `response_schema` and parse it."""
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=temperature,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        response = self._call_with_retries(
            lambda: self.client.models.generate_content(
                model=self.model, contents=prompt, config=config
            ),
            self.model,
        )

        parsed = response.parsed
        if isinstance(parsed, response_schema):
            return parsed
        if response.text:
            try:
                return response_schema.model_validate_json(response.text)
            except ValueError as error:
                raise GeminiResponseError(f"Invalid structured output: {error}") from error
        raise GeminiResponseError("Empty response from Gemini")

    def embed(self, texts: List[str], task_type: str) -> List[List[float]]:
        """
        Embed texts with the configured Gemini embedding model.

        `task_type` should be RETRIEVAL_DOCUMENT for indexed content and
        RETRIEVAL_QUERY for search queries.
        """
        if not texts:
            return []
        config = types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=self.embedding_dimensions,
        )
        response = self._call_with_retries(
            lambda: self.client.models.embed_content(
                model=self.embedding_model, contents=texts, config=config
            ),
            self.embedding_model,
        )
        embeddings = response.embeddings or []
        if len(embeddings) != len(texts):
            raise GeminiResponseError(
                f"Expected {len(texts)} embeddings, received {len(embeddings)}"
            )
        return [list(embedding.values) for embedding in embeddings]


_default_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Return the shared GeminiClient configured from settings."""
    global _default_client
    if _default_client is None:
        _default_client = GeminiClient()
    return _default_client
