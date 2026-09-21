from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from mini_onyx.chat.exceptions import ChatSessionNotFoundError
from mini_onyx.chat.service import (
    SYSTEM_PROMPT,
    get_session_or_raise,
    reply_in_chat_session,
)
from mini_onyx.db.models import Base
from mini_onyx.db.repository import (
    create_chat_session,
    get_or_create_persona,
    list_messages,
)


class RecordingLLM:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, list[tuple[str, str]] | None]] = []

    def invoke(
        self,
        *,
        system_prompt: str,
        user_message: str,
        history: list[tuple[str, str]] | None = None,
    ) -> str:
        self.calls.append((system_prompt, user_message, history))
        return f"Yanıt: {user_message}"

    def stream(self, *, system_prompt: str, user_message: str) -> Iterator[str]:
        yield f"Yanıt: {user_message}"


def test_get_session_or_raise_returns_existing_session() -> None:
    engine = create_engine("sqlite+pysqlite://")
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db_session, db_session.begin():
            created = create_chat_session(db_session, title="Python")
            found = get_session_or_raise(db_session, chat_session_id=created.id)

            assert found.id == created.id
    finally:
        engine.dispose()


def test_get_session_or_raise_raises_for_missing_session() -> None:
    engine = create_engine("sqlite+pysqlite://")
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db_session:
            with pytest.raises(ChatSessionNotFoundError):
                get_session_or_raise(db_session, chat_session_id=999)
    finally:
        engine.dispose()


def test_reply_uses_persona_system_prompt() -> None:
    engine = create_engine("sqlite+pysqlite://")
    Base.metadata.create_all(engine)
    llm = RecordingLLM()

    try:
        with Session(engine) as db_session:
            with db_session.begin():
                persona = get_or_create_persona(
                    db_session, name="pirate", system_prompt="Talk like a pirate."
                )
                chat_session = create_chat_session(
                    db_session, title="Test", persona_id=persona.id
                )
                chat_session_id = chat_session.id

            reply_in_chat_session(
                db_session,
                chat_session_id=chat_session_id,
                message="Merhaba",
                llm=llm,
            )

        assert llm.calls[0][0] == "Talk like a pirate."
    finally:
        engine.dispose()


def test_reply_falls_back_to_default_prompt_without_persona() -> None:
    engine = create_engine("sqlite+pysqlite://")
    Base.metadata.create_all(engine)
    llm = RecordingLLM()

    try:
        with Session(engine) as db_session:
            with db_session.begin():
                chat_session = create_chat_session(db_session, title="Test")
                chat_session_id = chat_session.id

            reply_in_chat_session(
                db_session,
                chat_session_id=chat_session_id,
                message="Merhaba",
                llm=llm,
            )

        assert llm.calls[0][0] == SYSTEM_PROMPT
    finally:
        engine.dispose()


def test_second_reply_receives_previous_messages_as_history() -> None:
    engine = create_engine("sqlite+pysqlite://")
    Base.metadata.create_all(engine)
    llm = RecordingLLM()

    try:
        with Session(engine) as db_session:
            with db_session.begin():
                chat_session = create_chat_session(db_session, title="Test")
                chat_session_id = chat_session.id

            reply_in_chat_session(
                db_session,
                chat_session_id=chat_session_id,
                message="Merhaba",
                llm=llm,
            )
            reply_in_chat_session(
                db_session,
                chat_session_id=chat_session_id,
                message="Nasılsın?",
                llm=llm,
            )
            stored = list_messages(db_session, chat_session_id=chat_session_id)

        assert llm.calls[0][2] == []
        assert llm.calls[1][2] == [
            ("user", "Merhaba"),
            ("assistant", "Yanıt: Merhaba"),
        ]
        assert [message.role for message in stored] == [
            "user",
            "assistant",
            "user",
            "assistant",
        ]
    finally:
        engine.dispose()
