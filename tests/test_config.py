import pytest

from mini_onyx.config import (
    DEFAULT_LLM_MODEL,
    get_database_settings,
    get_llm_settings,
)
from mini_onyx.db.exceptions import DatabaseConfigurationError
from mini_onyx.llm.exceptions import LLMConfigurationError


def test_llm_settings_uses_default_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LLM_MODEL", raising=False)

    settings = get_llm_settings()

    assert settings.model == DEFAULT_LLM_MODEL


def test_llm_settings_reads_model_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_MODEL", "openai/example-model")

    settings = get_llm_settings()

    assert settings.model == "openai/example-model"


def test_llm_settings_rejects_empty_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_MODEL", "   ")

    with pytest.raises(LLMConfigurationError, match="LLM_MODEL"):
        get_llm_settings()


def test_database_settings_reads_url_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = "postgresql+psycopg2://user:password@localhost:5433/database"
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = get_database_settings()

    assert settings.url == database_url


def test_database_settings_rejects_missing_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(
        DatabaseConfigurationError,
        match="DATABASE_URL",
    ):
        get_database_settings()
