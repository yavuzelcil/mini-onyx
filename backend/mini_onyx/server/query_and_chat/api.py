from fastapi import APIRouter

from mini_onyx.chat.service import generate_reply
from mini_onyx.server.query_and_chat.models import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("")
def send_chat_message(chat_request: ChatRequest) -> ChatResponse:
    """Send a chat message and receive a response."""
    reply = generate_reply(chat_request.message)
    return ChatResponse(reply=reply)
