from collections.abc import Iterator

import litellm
from litellm import ModelResponse, ModelResponseStream
from litellm.exceptions import (
    APIConnectionError as LiteLLMAPIConnectionError,
)
from litellm.exceptions import APIError as LiteLLMAPIError
from litellm.exceptions import (
    AuthenticationError as LiteLLMAuthenticationError,
)
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


class LiteLLMClient:
    def __init__(self, *, model: str) -> None:
        self._model = model

    def invoke(
        self,
        *,
        system_prompt: str,
        user_message: str,
        history: list[tuple[str, str]] | None = None,
    ) -> str:
        messages = [{"role": "system", "content": system_prompt}]

        for role, content in history or []:
            messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        try:
            response = litellm.completion(
                model=self._model,
                messages=messages,
                stream=False,
            )
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

        if not isinstance(response, ModelResponse):
            raise LLMResponseError(
                "The LLM provider returned an unexpected response type."
            )

        if not response.choices:
            raise LLMResponseError("The LLM provider returned no response choices.")

        content = response.choices[0].message.content

        if not isinstance(content, str) or not content.strip():
            raise LLMResponseError("The LLM provider returned an empty response.")

        return content.strip()

    def stream(
        self,
        *,
        system_prompt: str,
        user_message: str,
        history: list[tuple[str, str]] | None = None,
    ) -> Iterator[str]:
        messages = [{"role": "system", "content": system_prompt}]

        for role, content in history or []:
            messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        try:
            response = litellm.completion(
                model=self._model,
                messages=messages,
                stream=True,
            )

            if isinstance(response, ModelResponse):
                raise LLMResponseError("The LLM provider did not return a stream.")

            for chunk in response:
                if not isinstance(chunk, ModelResponseStream):
                    raise LLMResponseError(
                        "The LLM provider returned an unexpected stream chunk."
                    )

                if not chunk.choices:
                    continue

                content = chunk.choices[0].delta.content

                if isinstance(content, str) and content:
                    yield content

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
