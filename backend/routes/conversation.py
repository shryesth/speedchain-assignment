"""Conversation history routes."""
from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversation", tags=["conversation"])

# Service instance will be injected
memory_service = None

def set_memory_service(service):
    """Set the memory service instance."""
    global memory_service
    memory_service = service

@router.get("/history/{user_id}")
async def get_conversation_history(user_id: str):
    """Get conversation history for a user."""
    return memory_service.get_conversation_history(user_id)
