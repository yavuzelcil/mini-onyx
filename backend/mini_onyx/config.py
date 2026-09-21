import os
from dataclasses import dataclass

from mini_onyx.db.exceptions import DatabaseConfigurationError
from mini_onyx.llm.exceptions import LLMConfigurationError

DEFAULT_LLM_MODEL = "openai/gpt-5-mini"


@dataclass(frozen=True, slots=True)
class LLMSettings:
    model: str


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    url: str


def get_llm_settings() -> LLMSettings:
    model = os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL).strip()

    if not model:
        raise LLMConfigurationError("LLM_MODEL cannot be empty.")

    return LLMSettings(model=model)


def get_database_settings() -> DatabaseSettings:
    url = os.getenv("DATABASE_URL", "").strip()

    if not url:
        raise DatabaseConfigurationError("DATABASE_URL cannot be empty.")

    return DatabaseSettings(url=url)
