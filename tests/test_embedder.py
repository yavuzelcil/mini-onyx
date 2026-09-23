from unittest.mock import patch

import pytest

from mini_onyx.document_index.embedder import LiteLLMEmbedder
from mini_onyx.llm.exceptions import LLMResponseError


def test_embed_returns_one_vector_per_text() -> None:
    fake_response = type(
        "FakeResponse",
        (),
        {"data": [{"embedding": [0.1, 0.2]}, {"embedding": [0.3, 0.4]}]},
    )()
    embedder = LiteLLMEmbedder(model="openai/text-embedding-3-small")

    with patch(
        "mini_onyx.document_index.embedder.litellm.embedding",
        return_value=fake_response,
    ) as embedding_mock:
        result = embedder.embed(["merhaba", "dunya"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    embedding_mock.assert_called_once_with(
        model="openai/text-embedding-3-small",
        input=["merhaba", "dunya"],
    )


def test_embed_rejects_mismatched_vector_count() -> None:
    fake_response = type("FakeResponse", (), {"data": [{"embedding": [0.1, 0.2]}]})()
    embedder = LiteLLMEmbedder(model="openai/text-embedding-3-small")

    with (
        patch(
            "mini_onyx.document_index.embedder.litellm.embedding",
            return_value=fake_response,
        ),
        pytest.raises(LLMResponseError, match="mismatched embedding count"),
    ):
        embedder.embed(["merhaba", "dunya"])
