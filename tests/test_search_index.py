from unittest.mock import Mock

from mini_onyx.document_index.search_index import OpenSearchIndex, SearchResult


def test_ensure_index_exists_creates_index_when_missing() -> None:
    client = Mock()
    client.indices.exists.return_value = False
    index = OpenSearchIndex(client=client, index_name="test-index")

    index.ensure_index_exists()

    client.indices.exists.assert_called_once_with(index="test-index")
    client.indices.create.assert_called_once()
    _, kwargs = client.indices.create.call_args
    assert kwargs["index"] == "test-index"
    assert kwargs["body"]["settings"] == {"index": {"knn": True}}


def test_ensure_index_exists_skips_creation_when_present() -> None:
    client = Mock()
    client.indices.exists.return_value = True
    index = OpenSearchIndex(client=client, index_name="test-index")

    index.ensure_index_exists()

    client.indices.create.assert_not_called()


def test_index_chunk_sends_expected_document() -> None:
    client = Mock()
    index = OpenSearchIndex(client=client, index_name="test-index")

    index.index_chunk(
        chunk_id=7,
        document_id=3,
        content="merhaba",
        embedding=[0.1, 0.2],
    )

    client.index.assert_called_once_with(
        index="test-index",
        id="7",
        body={"document_id": 3, "content": "merhaba", "embedding": [0.1, 0.2]},
        refresh=True,
    )


def test_vector_search_sends_knn_query_and_parses_hits() -> None:
    client = Mock()
    client.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_id": "7",
                    "_score": 0.91,
                    "_source": {
                        "document_id": 3,
                        "content": "Mini Onyx belge parçası",
                    },
                }
            ]
        }
    }
    index = OpenSearchIndex(client=client, index_name="test-index")

    results = index.vector_search(
        embedding=[0.1, 0.2],
        limit=4,
    )

    client.search.assert_called_once_with(
        index="test-index",
        body={
            "size": 4,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": [0.1, 0.2],
                        "k": 4,
                    }
                }
            },
        },
    )
    assert results == [
        SearchResult(
            chunk_id=7,
            document_id=3,
            content="Mini Onyx belge parçası",
            score=0.91,
        )
    ]
