import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from mini_onyx.chat.personas import PERSONA_PRESETS
from mini_onyx.db.dependencies import get_db_session
from mini_onyx.db.models import Base
from mini_onyx.llm.dependencies import get_llm
from mini_onyx.llm.exceptions import LLMConnectionError
from mini_onyx.llm.interfaces import LLM
from mini_onyx.main import app


class FakeLLM:
    def invoke(
        self,
        *,
        system_prompt: str,
        user_message: str,
        history: list[tuple[str, str]] | None = None,
    ) -> str:
        return f"Fake yanıt: {user_message}"

    def stream(
        self,
        *,
        system_prompt: str,
        user_message: str,
        history: list[tuple[str, str]] | None = None,
    ) -> Iterator[str]:
        yield f"Fake yanıt: {user_message}"


class FailingLLM:
    def invoke(
        self,
        *,
        system_prompt: str,
        user_message: str,
        history: list[tuple[str, str]] | None = None,
    ) -> str:
        raise LLMConnectionError("Test için LLM hatası")

    def stream(
        self,
        *,
        system_prompt: str,
        user_message: str,
        history: list[tuple[str, str]] | None = None,
    ) -> Iterator[str]:
        raise LLMConnectionError("Test için LLM hatası")


def get_fake_llm() -> LLM:
    return FakeLLM()


def get_failing_llm() -> LLM:
    return FailingLLM()


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
    app.dependency_overrides[get_llm] = get_fake_llm

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_llm, None)
        engine.dispose()


def test_creates_and_reads_chat_session(client: TestClient) -> None:
    created = client.post(
        "/api/chat/sessions",
        json={"title": " Python "},
    )

    assert created.status_code == 201
    assert created.json()["title"] == "Python"
    assert created.json()["persona_name"] is None

    chat_session_id = created.json()["id"]
    fetched = client.get(f"/api/chat/sessions/{chat_session_id}")

    assert fetched.status_code == 200
    assert fetched.json() == created.json()


def test_missing_chat_session_returns_404(client: TestClient) -> None:
    response = client.get("/api/chat/sessions/999")

    assert response.status_code == 404


def test_selected_persona_is_returned_and_used_for_reply(client: TestClient) -> None:
    recorded_prompts: list[str] = []

    class RecordingLLM(FakeLLM):
        def invoke(
            self,
            *,
            system_prompt: str,
            user_message: str,
            history: list[tuple[str, str]] | None = None,
        ) -> str:
            recorded_prompts.append(system_prompt)
            return super().invoke(
                system_prompt=system_prompt,
                user_message=user_message,
                history=history,
            )

    def get_recording_llm() -> LLM:
        return RecordingLLM()

    app.dependency_overrides[get_llm] = get_recording_llm

    created = client.post(
        "/api/chat/sessions",
        json={"title": "Lessons", "persona_name": "teacher"},
    )

    assert created.status_code == 201
    assert created.json()["persona_name"] == "teacher"

    chat_session_id = created.json()["id"]
    fetched = client.get(f"/api/chat/sessions/{chat_session_id}")
    sent = client.post(
        f"/api/chat/sessions/{chat_session_id}/messages",
        json={"message": "Explain Python"},
    )

    assert fetched.status_code == 200
    assert fetched.json() == created.json()
    assert sent.status_code == 200
    assert recorded_prompts == [PERSONA_PRESETS["teacher"]]


def test_rejects_unknown_persona(client: TestClient) -> None:
    response = client.post(
        "/api/chat/sessions",
        json={"title": "Lessons", "persona_name": "unknown"},
    )

    assert response.status_code == 422


def test_sends_message_and_reads_history(client: TestClient) -> None:
    created = client.post(
        "/api/chat/sessions",
        json={"title": "Test sohbeti"},
    )
    chat_session_id = created.json()["id"]

    sent = client.post(
        f"/api/chat/sessions/{chat_session_id}/messages",
        json={"message": " Merhaba "},
    )

    assert sent.status_code == 200
    assert sent.json() == {"reply": "Fake yanıt: Merhaba"}

    history = client.get(f"/api/chat/sessions/{chat_session_id}/messages")

    assert history.status_code == 200
    assert [(message["role"], message["content"]) for message in history.json()] == [
        ("user", "Merhaba"),
        ("assistant", "Fake yanıt: Merhaba"),
    ]


def test_messages_for_missing_session_return_404(client: TestClient) -> None:
    sent = client.post(
        "/api/chat/sessions/999/messages",
        json={"message": "Merhaba"},
    )
    history = client.get("/api/chat/sessions/999/messages")

    assert sent.status_code == 404
    assert history.status_code == 404


def test_llm_failure_does_not_save_messages(client: TestClient) -> None:
    created = client.post(
        "/api/chat/sessions",
        json={"title": "Hata testi"},
    )
    chat_session_id = created.json()["id"]

    app.dependency_overrides[get_llm] = get_failing_llm

    sent = client.post(
        f"/api/chat/sessions/{chat_session_id}/messages",
        json={"message": "Merhaba"},
    )
    history = client.get(f"/api/chat/sessions/{chat_session_id}/messages")

    assert sent.status_code == 502
    assert history.status_code == 200
    assert history.json() == []


def test_session_stream_saves_reply_after_done(client: TestClient) -> None:
    created = client.post("/api/chat/sessions", json={"title": "Stream test"})
    chat_session_id = created.json()["id"]

    response = client.post(
        f"/api/chat/sessions/{chat_session_id}/messages/stream",
        json={"message": "Hello"},
    )

    packets = [json.loads(line) for line in response.text.splitlines()]
    history = client.get(f"/api/chat/sessions/{chat_session_id}/messages")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert packets == [
        {"type": "content_delta", "content": "Fake yanıt: Hello"},
        {"type": "done"},
    ]
    assert [(item["role"], item["content"]) for item in history.json()] == [
        ("user", "Hello"),
        ("assistant", "Fake yanıt: Hello"),
    ]


def test_failed_session_stream_does_not_save_messages(client: TestClient) -> None:
    created = client.post("/api/chat/sessions", json={"title": "Stream test"})
    chat_session_id = created.json()["id"]
    app.dependency_overrides[get_llm] = get_failing_llm

    response = client.post(
        f"/api/chat/sessions/{chat_session_id}/messages/stream",
        json={"message": "Hello"},
    )
    history = client.get(f"/api/chat/sessions/{chat_session_id}/messages")

    assert response.status_code == 200
    assert [json.loads(line)["type"] for line in response.text.splitlines()] == [
        "error"
    ]
    assert history.json() == []


def test_session_stream_returns_404_for_missing_session(client: TestClient) -> None:
    response = client.post(
        "/api/chat/sessions/999/messages/stream",
        json={"message": "Hello"},
    )

    assert response.status_code == 404
