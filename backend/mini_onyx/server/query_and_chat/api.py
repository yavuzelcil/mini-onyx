from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from mini_onyx.chat.service import generate_reply, stream_reply
from mini_onyx.llm.dependencies import get_llm
from mini_onyx.llm.exceptions import LLMError
from mini_onyx.llm.interfaces import LLM
from mini_onyx.server.query_and_chat.models import (
    ChatRequest,
    ChatResponse,
    ChatStreamDelta,
    ChatStreamDone,
    ChatStreamError,
)

router = APIRouter(prefix="/chat", tags=["Chat"])

LLMDependency = Annotated[LLM, Depends(get_llm)]


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
