from typing import Protocol

from opensearchpy import OpenSearch

EMBEDDING_DIMENSIONS = 1536


class SearchIndex(Protocol):
    def ensure_index_exists(self) -> None:
        """Create the index if it does not exist yet."""
        ...

    def index_chunk(
        self,
        *,
        chunk_id: int,
        document_id: int,
        content: str,
        embedding: list[float],
    ) -> None:
        """Add or replace one chunk in the index."""
        ...


class OpenSearchIndex:
    def __init__(self, *, client: OpenSearch, index_name: str) -> None:
        self._client = client
        self._index_name = index_name

    def ensure_index_exists(self) -> None:
        if self._client.indices.exists(index=self._index_name):
            return

        self._client.indices.create(
            index=self._index_name,
            body={
                "mappings": {
                    "properties": {
                        "document_id": {"type": "integer"},
                        "content": {"type": "text"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": EMBEDDING_DIMENSIONS,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "lucene",
                            },
                        },
                    }
                },
                "settings": {"index": {"knn": True}},
            },
        )

    def index_chunk(
        self,
        *,
        chunk_id: int,
        document_id: int,
        content: str,
        embedding: list[float],
    ) -> None:
        self._client.index(
            index=self._index_name,
            id=str(chunk_id),
            body={
                "document_id": document_id,
                "content": content,
                "embedding": embedding,
            },
            refresh=True,
        )
