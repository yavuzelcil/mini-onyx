from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from mini_onyx.chat.personas import PERSONA_PRESETS
from mini_onyx.chat.service import (
    generate_reply,
    get_session_or_raise,
    reply_in_chat_session,
    start_chat_session,
    stream_reply,
    stream_reply_in_chat_session,
)
from mini_onyx.db.dependencies import get_db_session
from mini_onyx.db.repository import (
    list_messages,
)
from mini_onyx.document_index.dependencies import get_embedder, get_search_index
from mini_onyx.document_index.embedder import Embedder
from mini_onyx.document_index.search_index import SearchIndex
from mini_onyx.document_index.service import (
    format_search_results_as_context,
    search_document_chunks,
)
from mini_onyx.llm.dependencies import get_llm
from mini_onyx.llm.exceptions import LLMError
from mini_onyx.llm.interfaces import LLM
from mini_onyx.server.query_and_chat.models import (
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
    ChatSourceResponse,
    ChatStreamDelta,
    ChatStreamDone,
    ChatStreamError,
    ChatStreamSources,
    CreateChatSessionRequest,
    PersonaResponse,
    SessionChatRequest,
    StoredMessageResponse,
)

router = APIRouter(prefix="/chat", tags=["Chat"])

LLMDependency = Annotated[LLM, Depends(get_llm)]
DBSessionDependency = Annotated[Session, Depends(get_db_session)]
EmbedderDependency = Annotated[Embedder, Depends(get_embedder)]
SearchIndexDependency = Annotated[SearchIndex, Depends(get_search_index)]


def _retrieve_document_context(
    request: SessionChatRequest,
    embedder: Embedder,
    search_index: SearchIndex,
) -> tuple[str | None, list[ChatSourceResponse]]:
    if not request.use_rag:
        return None, []

    results = search_document_chunks(
        embedder,
        search_index,
        query=request.message,
        limit=3,
    )

    sources = [
        ChatSourceResponse(
            chunk_id=result.chunk_id,
            document_id=result.document_id,
            content=result.content,
            score=result.score,
        )
        for result in results
    ]

    return format_search_results_as_context(results), sources


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


@router.get("/personas")
def list_personas() -> list[PersonaResponse]:
    return [PersonaResponse(name=name) for name in PERSONA_PRESETS]


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
        chat_session = start_chat_session(
            db_session,
            title=request.title,
            persona_name=request.persona_name,
        )
        return ChatSessionResponse(
            id=chat_session.id,
            title=chat_session.title,
            persona_name=(
                chat_session.persona.name if chat_session.persona is not None else None
            ),
        )


@router.get("/sessions/{chat_session_id}")
def get_chat_session_route(
    chat_session_id: int,
    db_session: DBSessionDependency,
) -> ChatSessionResponse:
    chat_session = get_session_or_raise(db_session, chat_session_id=chat_session_id)

    return ChatSessionResponse(
        id=chat_session.id,
        title=chat_session.title,
        persona_name=(
            chat_session.persona.name if chat_session.persona is not None else None
        ),
    )


@router.post("/sessions/{chat_session_id}/messages")
def send_session_message(
    chat_session_id: int,
    chat_request: SessionChatRequest,
    db_session: DBSessionDependency,
    llm: LLMDependency,
    embedder: EmbedderDependency,
    search_index: SearchIndexDependency,
) -> ChatResponse:
    document_context, _ = _retrieve_document_context(
        chat_request,
        embedder,
        search_index,
    )

    reply = reply_in_chat_session(
        db_session,
        chat_session_id=chat_session_id,
        message=chat_request.message,
        llm=llm,
        document_context=document_context,
    )
    return ChatResponse(reply=reply)


@router.post("/sessions/{chat_session_id}/messages/stream")
def stream_session_message(
    chat_session_id: int,
    chat_request: SessionChatRequest,
    db_session: DBSessionDependency,
    llm: LLMDependency,
    embedder: EmbedderDependency,
    search_index: SearchIndexDependency,
) -> StreamingResponse:
    with db_session.begin():
        get_session_or_raise(db_session, chat_session_id=chat_session_id)

    def generate_ndjson() -> Iterator[str]:
        try:
            document_context, sources = _retrieve_document_context(
                chat_request,
                embedder,
                search_index,
            )

            if chat_request.use_rag:
                source_packet = ChatStreamSources(sources=sources)
                yield f"{source_packet.model_dump_json()}\n"

            for content in stream_reply_in_chat_session(
                db_session,
                chat_session_id=chat_session_id,
                message=chat_request.message,
                llm=llm,
                document_context=document_context,
            ):
                packet = ChatStreamDelta(content=content)
                yield f"{packet.model_dump_json()}\n"

            yield f"{ChatStreamDone().model_dump_json()}\n"

        except LLMError as error:
            packet = ChatStreamError(detail=str(error))
            yield f"{packet.model_dump_json()}\n"

    return StreamingResponse(
        generate_ndjson(),
        media_type="application/x-ndjson",
    )


@router.get("/sessions/{chat_session_id}/messages")
def get_session_messages(
    chat_session_id: int,
    db_session: DBSessionDependency,
) -> list[StoredMessageResponse]:
    with db_session.begin():
        get_session_or_raise(db_session, chat_session_id=chat_session_id)

        messages = list_messages(db_session, chat_session_id=chat_session_id)
        return [
            StoredMessageResponse(
                id=message.id, role=message.role, content=message.content
            )
            for message in messages
        ]
