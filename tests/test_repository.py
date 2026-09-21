from sqlalchemy.orm import Session

from mini_onyx.config import DatabaseSettings
from mini_onyx.db.engine import create_database_engine
from mini_onyx.db.models import Base
from mini_onyx.db.repository import (
    create_chat_session,
    create_message,
    list_messages,
)


def test_repository_persists_chat_and_messages() -> None:
    engine = create_database_engine(DatabaseSettings(url="sqlite+pysqlite:///:memory:"))
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db_session:
            with db_session.begin():
                chat_session = create_chat_session(
                    db_session,
                    title="Python",
                )
                chat_session_id = chat_session.id
                create_message(
                    db_session,
                    chat_session_id=chat_session_id,
                    role="user",
                    content="Generator nedir?",
                )
                create_message(
                    db_session,
                    chat_session_id=chat_session_id,
                    role="assistant",
                    content="Değerleri sırayla üretir.",
                )

        with Session(engine) as db_session:
            messages = list_messages(
                db_session,
                chat_session_id=chat_session_id,
            )

        assert [message.role for message in messages] == [
            "user",
            "assistant",
        ]
        assert [message.content for message in messages] == [
            "Generator nedir?",
            "Değerleri sırayla üretir.",
        ]
    finally:
        engine.dispose()
