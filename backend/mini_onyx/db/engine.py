from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from mini_onyx.config import DatabaseSettings
from mini_onyx.db.exceptions import DatabaseConnectionError


def create_database_engine(
    settings: DatabaseSettings,
) -> Engine:
    return create_engine(
        settings.url,
        pool_pre_ping=True,
    )


def check_database_connection(engine: Engine) -> None:
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError as error:
        raise DatabaseConnectionError(
            "The PostgreSQL database could not be reached."
        ) from error

    if result != 1:
        raise DatabaseConnectionError(
            "The PostgreSQL health query returned an unexpected result."
        )
