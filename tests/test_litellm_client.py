from unittest.mock import patch

import pytest
from litellm import ModelResponse, ModelResponseStream
from litellm.exceptions import AuthenticationError as LiteLLMAuthenticationError
from litellm.types.utils import Delta, StreamingChoices

from mini_onyx.llm.exceptions import (
    LLMAuthenticationError,
    LLMResponseError,
)
from mini_onyx.llm.litellm_client import LiteLLMClient


def test_litellm_client_sends_system_and_user_messages() -> None:
    response = ModelResponse(
        model="gpt-5-mini",
        choices=[
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "Merhaba!",
                },
            }
        ],
    )
    client = LiteLLMClient(model="openai/gpt-5-mini")

    with patch(
        "mini_onyx.llm.litellm_client.litellm.completion",
        return_value=response,
    ) as completion_mock:
        result = client.invoke(
            system_prompt="You are a helpful assistant.",
            user_message="Merhaba",
        )

    assert result == "Merhaba!"
    completion_mock.assert_called_once_with(
        model="openai/gpt-5-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": "Merhaba",
            },
        ],
        stream=False,
    )


def test_litellm_client_rejects_empty_response() -> None:
    response = ModelResponse(
        model="gpt-5-mini",
        choices=[
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "   ",
                },
            }
        ],
    )
    client = LiteLLMClient(model="openai/gpt-5-mini")

    with (
        patch(
            "mini_onyx.llm.litellm_client.litellm.completion",
            return_value=response,
        ),
        pytest.raises(LLMResponseError, match="empty response"),
    ):
        client.invoke(
            system_prompt="You are a helpful assistant.",
            user_message="Merhaba",
        )


def test_litellm_client_translates_authentication_error() -> None:
    provider_error = LiteLLMAuthenticationError(
        message="Invalid API key",
        llm_provider="openai",
        model="gpt-5-mini",
    )
    client = LiteLLMClient(model="openai/gpt-5-mini")

    with (
        patch(
            "mini_onyx.llm.litellm_client.litellm.completion",
            side_effect=provider_error,
        ),
        pytest.raises(
            LLMAuthenticationError,
            match="rejected the API credentials",
        ),
    ):
        client.invoke(
            system_prompt="You are a helpful assistant.",
            user_message="Merhaba",
        )


def test_litellm_client_streams_content_chunks() -> None:
    chunks = [
        ModelResponseStream(
            model="gpt-5-mini",
            choices=[
                StreamingChoices(
                    index=0,
                    finish_reason=None,
                    delta=Delta(role="assistant", content="Mer"),
                )
            ],
        ),
        ModelResponseStream(
            model="gpt-5-mini",
            choices=[
                StreamingChoices(
                    index=0,
                    finish_reason=None,
                    delta=Delta(content="haba!"),
                )
            ],
        ),
    ]
    client = LiteLLMClient(model="openai/gpt-5-mini")

    with patch(
        "mini_onyx.llm.litellm_client.litellm.completion",
        return_value=iter(chunks),
    ) as completion_mock:
        result = list(
            client.stream(
                system_prompt="You are a helpful assistant.",
                user_message="Merhaba",
            )
        )

    assert result == ["Mer", "haba!"]
    completion_mock.assert_called_once_with(
        model="openai/gpt-5-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": "Merhaba",
            },
        ],
        stream=True,
    )


def test_litellm_client_sends_chat_history_in_order() -> None:
    response = ModelResponse(
        model="gpt-5-mini",
        choices=[
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": "Adın Ayşe."},
            }
        ],
    )
    client = LiteLLMClient(model="openai/gpt-5-mini")

    with patch(
        "mini_onyx.llm.litellm_client.litellm.completion",
        return_value=response,
    ) as completion_mock:
        result = client.invoke(
            system_prompt="You are a helpful assistant.",
            history=[
                ("user", "Benim adım Ayşe"),
                ("assistant", "Memnun oldum Ayşe"),
            ],
            user_message="Benim adım ne?",
        )

    assert result == "Adın Ayşe."
    completion_mock.assert_called_once_with(
        model="openai/gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Benim adım Ayşe"},
            {"role": "assistant", "content": "Memnun oldum Ayşe"},
            {"role": "user", "content": "Benim adım ne?"},
        ],
        stream=False,
    )
