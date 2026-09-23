from functools import lru_cache

from opensearchpy import OpenSearch

from mini_onyx.config import (
    get_embedding_settings,
    get_opensearch_settings,
    get_storage_settings,
)
from mini_onyx.document_index.embedder import Embedder, LiteLLMEmbedder
from mini_onyx.document_index.search_index import OpenSearchIndex, SearchIndex
from mini_onyx.document_index.storage import FileStore, S3FileStore


@lru_cache
def get_file_store() -> FileStore:
    return S3FileStore(get_storage_settings())


def get_embedder() -> Embedder:
    return LiteLLMEmbedder(model=get_embedding_settings().model)


@lru_cache
def _get_opensearch_client() -> OpenSearch:
    return OpenSearch(hosts=[get_opensearch_settings().url])


def get_search_index() -> SearchIndex:
    settings = get_opensearch_settings()
    return OpenSearchIndex(
        client=_get_opensearch_client(), index_name=settings.index_name
    )
