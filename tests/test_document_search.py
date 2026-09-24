from unittest.mock import Mock

from mini_onyx.document_index.search_index import SearchResult
from mini_onyx.document_index.service import search_document_chunks


def test_search_document_chunks_embeds_query_and_searches_index() -> None:
    embedder = Mock()
    embedder.embed.return_value = [[0.1, 0.2]]

    expected_results = [
        SearchResult(
            chunk_id=7,
            document_id=3,
            content="Mini Onyx belge parçası",
            score=0.91,
        )
    ]

    search_index = Mock()
    search_index.vector_search.return_value = expected_results

    results = search_document_chunks(
        embedder,
        search_index,
        query="Mini Onyx nedir?",
        limit=4,
    )

    embedder.embed.assert_called_once_with(["Mini Onyx nedir?"])
    search_index.vector_search.assert_called_once_with(
        embedding=[0.1, 0.2],
        limit=4,
    )
    assert results == expected_results
