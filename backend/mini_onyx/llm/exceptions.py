class LLMError(RuntimeError):
    """Base error for Mini Onyx LLM operations."""


class LLMConfigurationError(LLMError):
    """Raised when the LLM configuration is invalid."""


class LLMAuthenticationError(LLMError):
    """Raised when the provider rejects its credentials."""


class LLMRateLimitError(LLMError):
    """Raised when the provider rate limit is exceeded."""


class LLMConnectionError(LLMError):
    """Raised when the provider cannot be reached."""


class LLMProviderError(LLMError):
    """Raised when the provider rejects or fails a request."""


class LLMResponseError(LLMError):
    """Raised when the provider returns an unusable response."""
