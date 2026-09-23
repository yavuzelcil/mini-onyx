from unittest.mock import Mock

from mini_onyx.document_index.search_index import OpenSearchIndex


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
