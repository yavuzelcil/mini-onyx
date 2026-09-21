from collections.abc import Generator, Iterator

from sqlalchemy.orm import Session

from mini_onyx.chat.exceptions import ChatSessionNotFoundError
from mini_onyx.db.models import ChatSession
from mini_onyx.db.repository import (
    create_message,
    get_chat_session,
    list_messages,
)
from mini_onyx.llm.exceptions import LLMResponseError
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


def _load_session_context(
    db_session: Session,
    *,
    chat_session_id: int,
) -> tuple[str, list[tuple[str, str]]]:
    with db_session.begin():
        chat_session = get_session_or_raise(
            db_session,
            chat_session_id=chat_session_id,
        )
        system_prompt = (
            chat_session.persona.system_prompt
            if chat_session.persona is not None
            else SYSTEM_PROMPT
        )
        history = [
            (stored.role, stored.content)
            for stored in list_messages(
                db_session,
                chat_session_id=chat_session_id,
            )
        ]

    return system_prompt, history


def reply_in_chat_session(
    db_session: Session,
    *,
    chat_session_id: int,
    message: str,
    llm: LLM,
) -> str:
    system_prompt, history = _load_session_context(
        db_session, chat_session_id=chat_session_id
    )

    reply = llm.invoke(
        system_prompt=system_prompt,
        user_message=message,
        history=history,
    )

    with db_session.begin():
        create_message(
            db_session,
            chat_session_id=chat_session_id,
            role="user",
            content=message,
        )
        create_message(
            db_session,
            chat_session_id=chat_session_id,
            role="assistant",
            content=reply,
        )

    return reply


def stream_reply_in_chat_session(
    db_session: Session,
    *,
    chat_session_id: int,
    message: str,
    llm: LLM,
) -> Generator[str]:
    system_prompt, history = _load_session_context(
        db_session, chat_session_id=chat_session_id
    )

    reply_parts: list[str] = []
    for content in llm.stream(
        system_prompt=system_prompt,
        user_message=message,
        history=history,
    ):
        reply_parts.append(content)
        yield content

    reply = "".join(reply_parts)
    if not reply.strip():
        raise LLMResponseError("The LLM provider returned an empty response.")

    with db_session.begin():
        create_message(
            db_session,
            chat_session_id=chat_session_id,
            role="user",
            content=message,
        )
        create_message(
            db_session,
            chat_session_id=chat_session_id,
            role="assistant",
            content=reply,
        )
