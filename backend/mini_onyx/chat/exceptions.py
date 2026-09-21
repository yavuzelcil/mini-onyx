class ChatError(RuntimeError):
    """Base error for Mini Onyx chat operations."""


class ChatSessionNotFoundError(ChatError):
    """Raised when a chat session does not exist."""
