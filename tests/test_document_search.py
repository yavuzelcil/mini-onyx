from unittest.mock import Mock

import pytest

from mini_onyx.document_index.search_index import SearchResult
from mini_onyx.document_index.service import (
    reciprocal_rank_fusion,
    search_document_chunks,
)


def make_result(
    chunk_id: int,
    *,
    score: float,
) -> SearchResult:
    return SearchResult(
        chunk_id=chunk_id,
        document_id=1,
        content=f"Chunk {chunk_id}",
        score=score,
    )


def test_reciprocal_rank_fusion_rewards_results_found_by_both_searches() -> None:
    vector_results = [
        make_result(1, score=0.95),
        make_result(2, score=0.80),
    ]
    keyword_results = [
        make_result(2, score=4.2),
        make_result(3, score=3.1),
    ]

    results = reciprocal_rank_fusion(
        [vector_results, keyword_results],
        limit=3,
    )

    assert [result.chunk_id for result in results] == [2, 1, 3]
    assert results[0].score == pytest.approx(1 / 52 + 1 / 51)


def test_search_document_chunks_runs_vector_and_keyword_search() -> None:
    embedder = Mock()
    embedder.embed.return_value = [[0.1, 0.2]]

    shared_result = make_result(7, score=0.91)

    search_index = Mock()
    search_index.vector_search.return_value = [shared_result]
    search_index.keyword_search.return_value = [shared_result]

    results = search_document_chunks(
        embedder,
        search_index,
        query="Mini Onyx nedir?",
        limit=4,
    )

    embedder.embed.assert_called_once_with(["Mini Onyx nedir?"])
    search_index.vector_search.assert_called_once_with(
        embedding=[0.1, 0.2],
        limit=8,
    )
    search_index.keyword_search.assert_called_once_with(
        query="Mini Onyx nedir?",
        limit=8,
    )

    assert [result.chunk_id for result in results] == [7]
    assert results[0].score == pytest.approx(2 / 51)
