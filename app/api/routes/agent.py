import logging

from fastapi import APIRouter, HTTPException
from app.schemas import ChatRequest, ChatResponse
from app.agent.graph import shopping_graph
from app.config import settings
from app.services.product_service import product_service
from app.services.vector_store import VectorStoreError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Process a natural language chat request using the shopping assistant.
    
    This endpoint uses LangGraph workflow to:
    1. Understand user intent (Planner Agent)
    2. Search and filter products (Product Agent)
    3. Validate and execute cart operations (Cart Agent)
    4. Generate natural response (Response Agent)
    
    Example request:
    ```json
    {
        "query": "Add cold drink which have less price 100 RS",
        "user_id": "user123",
        "store_id": "STORE_1"
    }
    ```
    """
    try:
        # Initialize state
        state = {
            "user_query": request.query,
            "user_id": request.user_id,
            "store_id": request.store_id or settings.default_store_id,
            "session_id": request.session_id,
            "requires_confirmation": False,
            "confirmation_options": None
        }
        
        # Run the LangGraph workflow
        result = shopping_graph.invoke(state)
        
        # Extract final response
        final_response = result.get("final_response", "I'm sorry, I couldn't process your request.")
        error = result.get("error")
        cart = result.get("cart")
        intent = result.get("intent")
        
        # Build response
        chat_response = ChatResponse(
            response=final_response,
            success=error is None,
            intent=intent.model_dump() if intent else None,
            cart_state=cart.model_dump() if cart else None,
            error=error
        )
        
        return chat_response
        
    except Exception:
        logger.exception("Unhandled error processing chat request for user=%s", request.user_id)
        raise HTTPException(
            status_code=500,
            detail="Internal error while processing the request."
        )


@router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    try:
        product_index = {"ready": True, "products": product_service.vector_store.count()}
    except VectorStoreError as error:
        product_index = {"ready": False, "detail": str(error)}
    
    return {
        "status": "healthy" if product_index["ready"] else "degraded",
        "service": settings.app_name,
        "version": settings.app_version,
        "product_index": product_index
    }


@router.get("/config", tags=["Configuration"])
async def get_config():
    """
    Get current configuration (for debugging).
    """
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment,
        "default_store_id": settings.default_store_id,
        "selection_policy": settings.selection_policy,
        "gemini_model": settings.gemini_model,
        "gemini_embedding_model": settings.gemini_embedding_model
    }
