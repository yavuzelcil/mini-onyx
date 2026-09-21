from mini_onyx.config import DatabaseSettings
from mini_onyx.db.engine import (
    check_database_connection,
    create_database_engine,
)
from mini_onyx.db.models import Base


def test_chat_models_register_expected_tables() -> None:
    assert set(Base.metadata.tables) == {
        "chat_sessions",
        "messages",
        "personas",
        "users",
    }


def test_database_engine_executes_health_query() -> None:
    settings = DatabaseSettings(
        url="sqlite+pysqlite:///:memory:",
    )
    engine = create_database_engine(settings)

    try:
        check_database_connection(engine)
    finally:
        engine.dispose()
