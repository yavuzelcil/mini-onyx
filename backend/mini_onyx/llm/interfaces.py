from collections.abc import Iterator
from typing import Protocol


class LLM(Protocol):
    def invoke(
        self,
        *,
        system_prompt: str,
        user_message: str,
        history: list[tuple[str, str]] | None = None,
    ) -> str:
        """Generate one assistant response."""
        ...

    def stream(
        self,
        *,
        system_prompt: str,
        user_message: str,
        history: list[tuple[str, str]] | None = None,
    ) -> Iterator[str]:
        """Generate one assistant response as text chunks."""
        ...
