import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from mini_onyx.chat.service import SYSTEM_PROMPT
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
    ) -> str:
        assert system_prompt == SYSTEM_PROMPT
        return f"Fake LLM response: {user_message}"

    def stream(
        self,
        *,
        system_prompt: str,
        user_message: str,
    ) -> Iterator[str]:
        assert system_prompt == SYSTEM_PROMPT
        yield "Fake LLM "
        yield f"response: {user_message}"


class FailingLLM:
    def invoke(
        self,
        *,
        system_prompt: str,
        user_message: str,
    ) -> str:
        raise LLMConnectionError("The LLM provider could not be reached.")

    def stream(
        self,
        *,
        system_prompt: str,
        user_message: str,
    ) -> Iterator[str]:
        raise LLMConnectionError("The LLM provider could not be reached.")


def get_fake_llm() -> LLM:
    return FakeLLM()


def get_failing_llm() -> LLM:
    return FailingLLM()


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_llm] = get_fake_llm

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_chat_returns_generated_reply(client: TestClient) -> None:
    response = client.post(
        "/api/chat",
        json={"message": "Hello"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "Fake LLM response: Hello",
    }


def test_chat_rejects_blank_message(client: TestClient) -> None:
    response = client.post(
        "/api/chat",
        json={"message": "   "},
    )

    assert response.status_code == 422


def test_chat_returns_bad_gateway_when_llm_fails(
    client: TestClient,
) -> None:
    app.dependency_overrides[get_llm] = get_failing_llm

    response = client.post(
        "/api/chat",
        json={"message": "Hello"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "The LLM provider could not be reached.",
    }


def test_chat_stream_returns_ndjson_packets(client: TestClient) -> None:
    response = client.post(
        "/api/chat/stream",
        json={"message": "Hello"},
    )

    packets = [json.loads(line) for line in response.text.splitlines()]

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert packets == [
        {
            "type": "content_delta",
            "content": "Fake LLM ",
        },
        {
            "type": "content_delta",
            "content": "response: Hello",
        },
        {
            "type": "done",
        },
    ]


def test_chat_stream_returns_error_packet(
    client: TestClient,
) -> None:
    app.dependency_overrides[get_llm] = get_failing_llm

    response = client.post(
        "/api/chat/stream",
        json={"message": "Hello"},
    )

    packets = [json.loads(line) for line in response.text.splitlines()]

    assert response.status_code == 200
    assert packets == [
        {
            "type": "error",
            "detail": "The LLM provider could not be reached.",
        }
    ]
