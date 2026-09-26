import logging
from typing import List, Optional

from app.schemas import PlannerOutput
from app.prompts import PLANNER_SYSTEM_PROMPT, PLANNER_HUMAN_PROMPT
from app.services.gemini_client import GeminiClient, GeminiError, get_gemini_client
from app.services.product_service import product_service
from app.services.vector_store import VectorStoreError
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Planner Agent that extracts structured intent from user queries using Gemini"""

    def __init__(self, gemini: Optional[GeminiClient] = None):
        self._gemini = gemini

    @property
    def gemini(self) -> GeminiClient:
        """Gemini client used for intent extraction."""
        if self._gemini is None:
            self._gemini = get_gemini_client()
        return self._gemini

    def _catalog_categories(self) -> List[str]:
        """Categories to offer the model; planning still works if the index is unavailable."""
        try:
            return product_service.categories()
        except VectorStoreError as error:
            logger.warning("Could not load catalog categories: %s", error)
            return []

    def plan(self, state: AgentState) -> AgentState:
        """
        Extract structured intent from user query.

        This is a LangGraph node function.
        """
        user_query = state.get("user_query", "")
        categories = self._catalog_categories()
        system_prompt = PLANNER_SYSTEM_PROMPT.format(
            categories=", ".join(categories) if categories else "unknown"
        )

        try:
            planner_output = self.gemini.generate_structured(
                system_instruction=system_prompt,
                prompt=PLANNER_HUMAN_PROMPT.format(user_query=user_query),
                response_schema=PlannerOutput,
            )
        except GeminiError as error:
            logger.error("Planner failed: %s", error.detail)
            state["error"] = f"Planner error: {error.user_message}"
            state["intent"] = None
            return state

        intent = planner_output.intent
        # Ignore categories the catalog does not know, so they cannot filter out every product
        if intent.category and intent.category not in categories:
            logger.info("Planner returned unknown category %r; ignoring it", intent.category)
            intent.category = None

        logger.info("Planner intent: %s", intent.model_dump())
        state["intent"] = intent
        state["plan"] = {
            "requires": planner_output.requires,
            "confidence": planner_output.confidence
        }
        state["requires_confirmation"] = intent.selection_strategy == "CONFIRM"
        return state


# Global instance
planner_agent = PlannerAgent()
