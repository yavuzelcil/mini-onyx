from collections.abc import Iterator

from mini_onyx.llm.interfaces import LLM

SYSTEM_PROMPT = (
    "You are Mini Onyx, a concise and helpful assistant. "
    "Answer in the same language as the user."
)


def generate_reply(
    message: str,
    *,
    llm: LLM,
) -> str:
    return llm.invoke(
        system_prompt=SYSTEM_PROMPT,
        user_message=message,
    )


def stream_reply(
    message: str,
    *,
    llm: LLM,
) -> Iterator[str]:
    yield from llm.stream(
        system_prompt=SYSTEM_PROMPT,
        user_message=message,
    )
