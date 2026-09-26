from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class AgentResponse(BaseModel):
    """Final response from the agent"""
    message: str = Field(description="Natural language response to user")
    success: bool = Field(description="Whether the operation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data if applicable")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class ChatRequest(BaseModel):
    """Chat request from user"""
    query: str = Field(description="User's natural language query")
    user_id: str = Field(description="User identifier")
    store_id: Optional[str] = Field(None, description="Store identifier, uses default if not provided")
    session_id: Optional[str] = Field(None, description="Session identifier for conversation context")


class ChatResponse(BaseModel):
    """Chat response to user"""
    response: str = Field(description="Natural language response")
    success: bool = Field(description="Whether the request was processed successfully")
    intent: Optional[Dict[str, Any]] = Field(None, description="Detected intent for transparency")
    cart_state: Optional[Dict[str, Any]] = Field(None, description="Current cart state if applicable")
    error: Optional[str] = Field(None, description="Error message if any")
