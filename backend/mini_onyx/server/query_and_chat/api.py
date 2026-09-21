from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from mini_onyx.chat.service import generate_reply, stream_reply
from mini_onyx.db.dependencies import get_db_session
from mini_onyx.db.repository import (
    create_chat_session,
    get_chat_session,
)
from mini_onyx.llm.dependencies import get_llm
from mini_onyx.llm.exceptions import LLMError
from mini_onyx.llm.interfaces import LLM
from mini_onyx.server.query_and_chat.models import (
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
    ChatStreamDelta,
    ChatStreamDone,
    ChatStreamError,
    CreateChatSessionRequest,
)

router = APIRouter(prefix="/chat", tags=["Chat"])

LLMDependency = Annotated[LLM, Depends(get_llm)]
DBSessionDependency = Annotated[Session, Depends(get_db_session)]


@router.post("")
def send_chat_message(
    chat_request: ChatRequest,
    llm: LLMDependency,
) -> ChatResponse:
    """Send a chat message and receive a response."""
    reply = generate_reply(
        chat_request.message,
        llm=llm,
    )
    return ChatResponse(reply=reply)


@router.post("/stream")
def stream_chat_message(
    chat_request: ChatRequest,
    llm: LLMDependency,
) -> StreamingResponse:
    """Send a chat message and stream response packets."""

    def generate_ndjson() -> Iterator[str]:
        try:
            for content in stream_reply(
                chat_request.message,
                llm=llm,
            ):
                packet = ChatStreamDelta(content=content)
                yield f"{packet.model_dump_json()}\n"

            done_packet = ChatStreamDone()
            yield f"{done_packet.model_dump_json()}\n"

        except LLMError as error:
            error_packet = ChatStreamError(detail=str(error))
            yield f"{error_packet.model_dump_json()}\n"

    return StreamingResponse(
        generate_ndjson(),
        media_type="application/x-ndjson",
    )


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_chat_session_route(
    request: CreateChatSessionRequest,
    db_session: DBSessionDependency,
) -> ChatSessionResponse:
    with db_session.begin():
        chat_session = create_chat_session(
            db_session,
            title=request.title,
        )
        return ChatSessionResponse(
            id=chat_session.id,
            title=chat_session.title,
        )


@router.get("/sessions/{chat_session_id}")
def get_chat_session_route(
    chat_session_id: int,
    db_session: DBSessionDependency,
) -> ChatSessionResponse:
    chat_session = get_chat_session(
        db_session,
        chat_session_id=chat_session_id,
    )

    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    return ChatSessionResponse(
        id=chat_session.id,
        title=chat_session.title,
    )
