import os
from dataclasses import dataclass

from mini_onyx.llm.exceptions import LLMConfigurationError

DEFAULT_LLM_MODEL = "openai/gpt-5-mini"


@dataclass(frozen=True, slots=True)
class LLMSettings:
    model: str


def get_llm_settings() -> LLMSettings:
    model = os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL).strip()

    if not model:
        raise LLMConfigurationError("LLM_MODEL cannot be empty.")

    return LLMSettings(model=model)
