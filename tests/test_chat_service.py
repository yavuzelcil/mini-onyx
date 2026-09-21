import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from mini_onyx.chat.exceptions import ChatSessionNotFoundError
from mini_onyx.chat.service import get_session_or_raise
from mini_onyx.db.models import Base
from mini_onyx.db.repository import create_chat_session


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
