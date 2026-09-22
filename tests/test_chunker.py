from mini_onyx.document_index.chunker import chunk_text, count_tokens


def test_chunk_text_keeps_short_paragraphs_together() -> None:
    text = "Bir. \n\nIki. \n\nUc."
    chunks = chunk_text(text, token_limit=50)

    assert len(chunks) == 1
    assert chunks[0][0] == "Bir.\n\nIki.\n\nUc."


def test_chunk_text_splits_when_token_limit_is_exceeded() -> None:
    paragraph = "kelime " * 5
    text = f"{paragraph}\n\n{paragraph}"

    limit = count_tokens(paragraph.strip()) + 1
    chunks = chunk_text(text, token_limit=limit)

    assert len(chunks) == 2
    assert chunks[0][0] == paragraph.strip()
    assert chunks[1][0] == paragraph.strip()


def test_chunk_text_hard_splits_a_single_long_paragraph() -> None:
    long_paragraph = "kelime " * 100
    chunks = chunk_text(long_paragraph, token_limit=20)

    assert len(chunks) > 1
    assert all(token_count <= 20 for _, token_count in chunks)


def test_chunk_text_reports_accurate_token_counts() -> None:
    chunks = chunk_text("Merhaba dunya.", token_limit=50)

    assert chunks[0][1] == count_tokens("Merhaba dunya.")
