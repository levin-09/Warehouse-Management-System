"""Chatbot routes — WMS GenAI assistant (Groq agent loop)."""
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from core import logger
from core.services.chatbot.chat_service import ChatService

chatbot_router = APIRouter(prefix="/v1/chat", tags=["Chatbot"])
logging = logger(__name__)

_service = ChatService()


class UserInputRequest(BaseModel):
    """A single chatbot user message."""

    user_input: str = Field(..., description="The user's message to the assistant")
    session_id: str = Field(default="default", description="Conversation session id")


@chatbot_router.get("/history")
async def chat_history(session_id: str = Query(default="default")):
    """
    Return the conversation history for a session.

    Args:
        session_id (str): The conversation session id.

    Returns:
        list: The session's history.
    """
    try:
        logging.info(f"Calling GET /v1/chat/history?session_id={session_id} endpoint")
        return _service.history(session_id)
    except Exception as error:
        logging.error(f"Error in GET /v1/chat/history endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@chatbot_router.delete("/history")
async def reset_history(session_id: str = Query(default="default")):
    """
    Clear a session's conversation history.

    Args:
        session_id (str): The conversation session id.

    Returns:
        dict: Confirmation message.
    """
    try:
        logging.info(f"Calling DELETE /v1/chat/history?session_id={session_id} endpoint")
        _service.reset(session_id)
        return {"message": "History cleared", "session_id": session_id}
    except Exception as error:
        logging.error(f"Error in DELETE /v1/chat/history endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@chatbot_router.post("")
async def chat(request: UserInputRequest):
    """
    Ask the WMS assistant a question and wait for the full answer.

    Args:
        request (UserInputRequest): User message and optional session id.

    Returns:
        dict: The assistant's response and any tool calls made.

    Raises:
        HTTPException 503: If the Groq API key is not configured.
        HTTPException 500: On unexpected errors.
    """
    try:
        logging.info("Calling POST /v1/chat endpoint")
        return await _service.chat(request.session_id, request.user_input)
    except RuntimeError as error:
        logging.error(f"Chatbot not configured: {error}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))
    except Exception as error:
        logging.error(f"Error in POST /v1/chat endpoint: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chatbot error: {error}",
        )


@chatbot_router.post("/stream")
async def chat_stream(request: UserInputRequest):
    """
    Ask the WMS assistant a question, streaming the answer over SSE.

    Events: ``delta`` (text), ``tool_call``, ``tool_result``, ``error``, ``done``.

    Args:
        request (UserInputRequest): User message and optional session id.

    Returns:
        StreamingResponse: SSE stream.
    """
    try:
        logging.info("Calling POST /v1/chat/stream endpoint")
        return await _service.stream(request.session_id, request.user_input)
    except Exception as error:
        logging.error(f"Error in POST /v1/chat/stream endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
