import os
from dataclasses import dataclass

from mini_onyx.db.exceptions import DatabaseConfigurationError
from mini_onyx.document_index.exceptions import StorageConfigurationError
from mini_onyx.llm.exceptions import LLMConfigurationError

DEFAULT_LLM_MODEL = "openai/gpt-5-mini"


@dataclass(frozen=True, slots=True)
class LLMSettings:
    model: str


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    url: str


@dataclass(frozen=True, slots=True)
class StorageSettings:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str


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


def get_storage_settings() -> StorageSettings:
    values = {
        "endpoint": os.getenv("MINIO_ENDPOINT", "").strip(),
        "access_key": os.getenv("MINIO_ACCESS_KEY", "").strip(),
        "secret_key": os.getenv("MINIO_SECRET_KEY", "").strip(),
        "bucket": os.getenv("MINIO_BUCKET", "").strip(),
    }
    if not all(values.values()):
        raise StorageConfigurationError("MinIO settings cannot be empty.")

    return StorageSettings(
        endpoint=values["endpoint"],
        access_key=values["access_key"],
        secret_key=values["secret_key"],
        bucket=values["bucket"],
    )
