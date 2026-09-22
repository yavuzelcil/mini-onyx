import tiktoken

ENCODING_NAME = "cl100k_base"
CHUNK_TOKEN_LIMIT = 300

_encoding = tiktoken.get_encoding(ENCODING_NAME)


def count_tokens(text: str) -> int:
    return len(_encoding.encode(text))


def _split_into_paragraphs(text: str) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n")]
    return [paragraph for paragraph in paragraphs if paragraph]


def _split_by_tokens(text: str, *, token_limit: int) -> list[str]:
    tokens = _encoding.encode(text)
    return [
        _encoding.decode(tokens[start : start + token_limit])
        for start in range(0, len(tokens), token_limit)
    ]


def chunk_text(
    text: str,
    *,
    token_limit: int = CHUNK_TOKEN_LIMIT,
) -> list[tuple[str, int]]:
    """Split text into chunks, keeping paragraphs together where possible."""
    chunks: list[str] = []
    buffer = ""
    buffer_tokens = 0

    for paragraph in _split_into_paragraphs(text):
        paragraph_tokens = count_tokens(paragraph)

        if paragraph_tokens > token_limit:
            if buffer:
                chunks.append(buffer)
                buffer, buffer_tokens = "", 0
            chunks.extend(_split_by_tokens(paragraph, token_limit=token_limit))
            continue

        if buffer and buffer_tokens + paragraph_tokens > token_limit:
            chunks.append(buffer)
            buffer, buffer_tokens = paragraph, paragraph_tokens
        else:
            buffer = f"{buffer}\n\n{paragraph}" if buffer else paragraph
            buffer_tokens += paragraph_tokens

    if buffer:
        chunks.append(buffer)

    return [(chunk, count_tokens(chunk)) for chunk in chunks]
