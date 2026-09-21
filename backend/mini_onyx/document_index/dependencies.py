from functools import lru_cache

from mini_onyx.config import get_storage_settings
from mini_onyx.document_index.storage import FileStore, S3FileStore


@lru_cache
def get_file_store() -> FileStore:
    return S3FileStore(get_storage_settings())
