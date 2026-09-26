"""
Gemini configuration diagnostic.

Lists the models your GEMINI_API_KEY can use and verifies that the configured
GEMINI_MODEL (structured generation) and GEMINI_EMBEDDING_MODEL work.

Usage:
    python check_gemini.py
"""
import sys

from pydantic import BaseModel

from app.config import settings
from app.services.gemini_client import GeminiClient, GeminiError


class _Probe(BaseModel):
    """Minimal structured-output schema used to probe the model."""

    max_price: float


def main() -> int:
    """Run the diagnostic and return a process exit code."""
    gemini = GeminiClient()
    try:
        print("Models available to this key:")
        for model in gemini.client.models.list():
            actions = model.supported_actions or []
            if "generateContent" in actions or "embedContent" in actions:
                print(f"  {model.name:50} {', '.join(actions)}")

        print(f"\nGEMINI_MODEL={settings.gemini_model}")
        probe = gemini.generate_structured(
            system_instruction="Extract the maximum price in rupees.",
            prompt="Add cold drink which have less price 100 RS",
            response_schema=_Probe,
        )
        print(f"  generateContent OK -> {probe}")

        print(f"GEMINI_EMBEDDING_MODEL={settings.gemini_embedding_model}")
        vectors = gemini.embed(["cold drink"], task_type="RETRIEVAL_QUERY")
        print(f"  embedContent OK -> {len(vectors[0])} dimensions")
    except GeminiError as error:
        print(f"\nERROR: {error.user_message}\n  Details: {error.detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
