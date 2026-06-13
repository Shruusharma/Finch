from fastapi import APIRouter
from api.schemas import ChatRequest, ChatResponse
from agents import orchestrator
from core.exceptions import AgentError
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        reply = orchestrator.handle(request.message)
    except Exception as e:
        from core.exceptions import FinchError
        if isinstance(e, FinchError):
            raise
        logger.error(f"Unexpected error in chat: {e}")
        raise AgentError() from e        
    
    return ChatResponse(
            response=reply,
            session_id=request.session_id,
            agent_used="orchestrator"
        )
    