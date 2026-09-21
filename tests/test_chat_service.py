from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from mini_onyx.chat.exceptions import ChatSessionNotFoundError
from mini_onyx.chat.service import (
    SYSTEM_PROMPT,
    get_session_or_raise,
    reply_in_chat_session,
    start_chat_session,
    stream_reply_in_chat_session,
)
from mini_onyx.db.models import Base, Persona, User
from mini_onyx.db.repository import (
    create_chat_session,
    get_or_create_persona,
    list_messages,
)


class RecordingLLM:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, list[tuple[str, str]] | None]] = []
        self.stream_calls: list[tuple[str, str, list[tuple[str, str]] | None]] = []

    def invoke(
        self,
        *,
        system_prompt: str,
        user_message: str,
        history: list[tuple[str, str]] | None = None,
    ) -> str:
        self.calls.append((system_prompt, user_message, history))
        return f"Yanıt: {user_message}"

    def stream(
        self,
        *,
        system_prompt: str,
        user_message: str,
        history: list[tuple[str, str]] | None = None,
    ) -> Iterator[str]:
        self.stream_calls.append((system_prompt, user_message, history))
        yield "Yanıt: "
        yield user_message


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


def test_session_stream_uses_history_and_saves_completed_replies() -> None:
    engine = create_engine("sqlite+pysqlite://")
    Base.metadata.create_all(engine)
    llm = RecordingLLM()

    try:
        with Session(engine) as db_session:
            with db_session.begin():
                persona = get_or_create_persona(
                    db_session, name="teacher", system_prompt="Teach patiently."
                )
                chat_session = create_chat_session(
                    db_session, title="Test", persona_id=persona.id
                )
                chat_session_id = chat_session.id

            first = list(
                stream_reply_in_chat_session(
                    db_session,
                    chat_session_id=chat_session_id,
                    message="Hello",
                    llm=llm,
                )
            )
            second = list(
                stream_reply_in_chat_session(
                    db_session,
                    chat_session_id=chat_session_id,
                    message="Again",
                    llm=llm,
                )
            )
            stored = list_messages(db_session, chat_session_id=chat_session_id)

        assert first == ["Yanıt: ", "Hello"]
        assert second == ["Yanıt: ", "Again"]
        assert llm.stream_calls[0] == ("Teach patiently.", "Hello", [])
        assert llm.stream_calls[1] == (
            "Teach patiently.",
            "Again",
            [("user", "Hello"), ("assistant", "Yanıt: Hello")],
        )
        assert [(item.role, item.content) for item in stored] == [
            ("user", "Hello"),
            ("assistant", "Yanıt: Hello"),
            ("user", "Again"),
            ("assistant", "Yanıt: Again"),
        ]
    finally:
        engine.dispose()


def test_stopped_session_stream_does_not_save_partial_reply() -> None:
    engine = create_engine("sqlite+pysqlite://")
    Base.metadata.create_all(engine)
    llm = RecordingLLM()

    try:
        with Session(engine) as db_session:
            with db_session.begin():
                chat_session = create_chat_session(db_session, title="Test")
                chat_session_id = chat_session.id

            stream = stream_reply_in_chat_session(
                db_session,
                chat_session_id=chat_session_id,
                message="Hello",
                llm=llm,
            )
            assert next(stream) == "Yanıt: "
            stream.close()

            assert list_messages(db_session, chat_session_id=chat_session_id) == []
    finally:
        engine.dispose()


def test_start_chat_session_links_default_user_and_persona() -> None:
    engine = create_engine("sqlite+pysqlite://")
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db_session, db_session.begin():
            first = start_chat_session(db_session, title="A", persona_name="teacher")
            second = start_chat_session(db_session, title="B", persona_name="teacher")
            third = start_chat_session(db_session, title="C", persona_name=None)

            assert first.user_id is not None
            assert first.user_id == second.user_id == third.user_id
            assert first.persona_id is not None
            assert first.persona_id == second.persona_id
            assert third.persona_id is None
            assert db_session.scalar(select(func.count()).select_from(User)) == 1
            assert db_session.scalar(select(func.count()).select_from(Persona)) == 1
    finally:
        engine.dispose()
