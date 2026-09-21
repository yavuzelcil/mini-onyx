from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from mini_onyx.db.dependencies import get_db_session
from mini_onyx.db.models import Base
from mini_onyx.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def get_test_db_session() -> Iterator[Session]:
        with Session(engine) as db_session:
            yield db_session

    app.dependency_overrides[get_db_session] = get_test_db_session

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        engine.dispose()


def test_creates_and_reads_chat_session(client: TestClient) -> None:
    created = client.post(
        "/api/chat/sessions",
        json={"title": " Python "},
    )

    assert created.status_code == 201
    assert created.json()["title"] == "Python"

    chat_session_id = created.json()["id"]
    fetched = client.get(f"/api/chat/sessions/{chat_session_id}")

    assert fetched.status_code == 200
    assert fetched.json() == created.json()


def test_missing_chat_session_returns_404(client: TestClient) -> None:
    response = client.get("/api/chat/sessions/999")

    assert response.status_code == 404
