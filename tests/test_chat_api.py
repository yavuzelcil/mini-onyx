from fastapi.testclient import TestClient

from mini_onyx.main import app


def test_chat_returns_generated_reply() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"message": "Hello"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "Mini Onyx received: Hello",
    }


def test_chat_rejects_blank_message() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"message": "   "},
        )

    assert response.status_code == 422
