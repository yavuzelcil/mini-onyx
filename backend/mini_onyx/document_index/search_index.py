from dataclasses import dataclass
from typing import Protocol

from opensearchpy import OpenSearch

EMBEDDING_DIMENSIONS = 1536


@dataclass(frozen=True, slots=True)
class SearchResult:
    chunk_id: int
    document_id: int
    content: str
    score: float


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

    def vector_search(
        self,
        *,
        embedding: list[float],
        limit: int = 5,
    ) -> list[SearchResult]:
        """Find chunks whose embeddings are closest to the query embedding."""
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

    def vector_search(
        self,
        *,
        embedding: list[float],
        limit: int = 5,
    ) -> list[SearchResult]:
        response = self._client.search(
            index=self._index_name,
            body={
                "size": limit,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": embedding,
                            "k": limit,
                        }
                    }
                },
            },
        )

        hits = response["hits"]["hits"]

        return [
            SearchResult(
                chunk_id=int(hit["_id"]),
                document_id=int(hit["_source"]["document_id"]),
                content=str(hit["_source"]["content"]),
                score=float(hit["_score"]),
            )
            for hit in hits
        ]
