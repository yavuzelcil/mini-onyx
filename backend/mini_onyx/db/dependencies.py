from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from mini_onyx.config import get_database_settings
from mini_onyx.db.engine import create_database_engine


@lru_cache
def get_database_engine() -> Engine:
    return create_database_engine(get_database_settings())


def get_db_session() -> Iterator[Session]:
    with Session(get_database_engine(), expire_on_commit=False) as db_session:
        yield db_session
