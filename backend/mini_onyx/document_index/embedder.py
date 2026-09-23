from typing import Protocol

import litellm
from litellm.exceptions import (
    APIConnectionError as LiteLLMAPIConnectionError,
)
from litellm.exceptions import APIError as LiteLLMAPIError
from litellm.exceptions import AuthenticationError as LiteLLMAuthenticationError
from litellm.exceptions import BadRequestError as LiteLLMBadRequestError
from litellm.exceptions import (
    InternalServerError as LiteLLMInternalServerError,
)
from litellm.exceptions import RateLimitError as LiteLLMRateLimitError
from litellm.exceptions import (
    ServiceUnavailableError as LiteLLMServiceUnavailableError,
)
from litellm.exceptions import Timeout as LiteLLMTimeout

from mini_onyx.llm.exceptions import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponseError,
)


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text, in the same order."""
        ...


class LiteLLMEmbedder:
    def __init__(self, *, model: str) -> None:
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = litellm.embedding(model=self._model, input=texts)
        except LiteLLMAuthenticationError as error:
            raise LLMAuthenticationError(
                "The LLM provider rejected the API credentials."
            ) from error
        except LiteLLMRateLimitError as error:
            raise LLMRateLimitError(
                "The LLM provider rate limit was exceeded."
            ) from error
        except (LiteLLMAPIConnectionError, LiteLLMTimeout) as error:
            raise LLMConnectionError(
                "The LLM provider could not be reached."
            ) from error
        except (
            LiteLLMAPIError,
            LiteLLMBadRequestError,
            LiteLLMInternalServerError,
            LiteLLMServiceUnavailableError,
        ) as error:
            raise LLMProviderError(
                "The LLM provider could not complete the request."
            ) from error

        vectors = [item["embedding"] for item in response.data]

        if len(vectors) != len(texts):
            raise LLMResponseError(
                "The LLM provider returned a mismatched embedding count."
            )

        return vectors
