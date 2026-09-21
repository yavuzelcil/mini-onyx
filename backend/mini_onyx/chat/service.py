from collections.abc import Iterator

from sqlalchemy.orm import Session

from mini_onyx.chat.exceptions import ChatSessionNotFoundError
from mini_onyx.db.models import ChatSession
from mini_onyx.db.repository import get_chat_session
from mini_onyx.llm.interfaces import LLM

SYSTEM_PROMPT = (
    "You are Mini Onyx, a concise and helpful assistant. "
    "Answer in the same language as the user."
)


def generate_reply(
    message: str,
    *,
    llm: LLM,
) -> str:
    return llm.invoke(
        system_prompt=SYSTEM_PROMPT,
        user_message=message,
    )


def stream_reply(
    message: str,
    *,
    llm: LLM,
) -> Iterator[str]:
    yield from llm.stream(
        system_prompt=SYSTEM_PROMPT,
        user_message=message,
    )


def get_session_or_raise(
    db_session: Session,
    *,
    chat_session_id: int,
) -> ChatSession:
    chat_session = get_chat_session(db_session, chat_session_id=chat_session_id)
    if chat_session is None:
        raise ChatSessionNotFoundError("Chat session not found.")
    return chat_session
