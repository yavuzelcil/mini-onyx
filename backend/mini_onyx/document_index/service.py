import json
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from mini_onyx.db.models import Document, DocumentChunk
from mini_onyx.db.repository import (
    create_document,
    create_document_chunks,
    get_document,
    list_document_chunks,
    update_chunk_embedding,
)
from mini_onyx.document_index.chunker import chunk_text
from mini_onyx.document_index.embedder import Embedder
from mini_onyx.document_index.exceptions import (
    DocumentNotFoundError,
    DocumentTooLargeError,
    DocumentValidationError,
)
from mini_onyx.document_index.search_index import SearchIndex, SearchResult
from mini_onyx.document_index.storage import FileStore

MAX_TEXT_FILE_BYTES = 1_000_000


def extract_text(filename: str | None, content: bytes) -> tuple[str, str]:
    safe_name = (filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    if not safe_name.lower().endswith(".txt") or len(safe_name) > 255:
        raise DocumentValidationError("Only named .txt files are supported.")
    if len(content) > MAX_TEXT_FILE_BYTES:
        raise DocumentTooLargeError("The file exceeds the 1 MB limit.")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise DocumentValidationError("The file must contain UTF-8 text.") from error

    if not text.strip():
        raise DocumentValidationError("The file contains no text.")
    return safe_name, text


def save_text_document(
    db_session: Session,
    file_store: FileStore,
    *,
    filename: str | None,
    content: bytes,
) -> Document:
    safe_name, text = extract_text(filename, content)
    object_key = f"{uuid4().hex}.txt"
    file_store.put(key=object_key, content=content)

    try:
        with db_session.begin():
            document = create_document(
                db_session,
                filename=safe_name,
                object_key=object_key,
                content=text,
            )
            document_id = document.id
    except SQLAlchemyError:
        file_store.delete(key=object_key)
        raise

    return db_session.get_one(Document, document_id)


def get_document_or_raise(
    db_session: Session,
    *,
    document_id: int,
) -> Document:
    document = get_document(db_session, document_id=document_id)
    if document is None:
        raise DocumentNotFoundError("Document not found.")
    return document


def chunk_and_store_document(
    db_session: Session,
    *,
    document_id: int,
    content: str,
) -> list[DocumentChunk]:

    chunks = chunk_text(content)
    with db_session.begin():
        return create_document_chunks(
            db_session,
            document_id=document_id,
            chunks=chunks,
        )


def embed_document_chunks(
    db_session: Session,
    embedder: Embedder,
    *,
    document_id: int,
) -> int:
    """Embed the document's chunks and return the vector dimension (0 if no chunks)."""
    with db_session.begin():
        chunks = list_document_chunks(db_session, document_id=document_id)
        contents = [chunk.content for chunk in chunks]
        chunk_ids = [chunk.id for chunk in chunks]

    vectors = embedder.embed(contents)

    with db_session.begin():
        for chunk_id, vector in zip(chunk_ids, vectors, strict=True):
            update_chunk_embedding(db_session, chunk_id=chunk_id, embedding=vector)

    return len(vectors[0]) if vectors else 0


def index_document_chunks(
    db_session: Session,
    search_index: SearchIndex,
    *,
    document_id: int,
) -> int:
    with db_session.begin():
        chunks = list_document_chunks(db_session, document_id=document_id)
        rows = [
            (chunk.id, chunk.content, json.loads(chunk.embedding))
            for chunk in chunks
            if chunk.embedding is not None
        ]

    search_index.ensure_index_exists()
    for chunk_id, content, embedding in rows:
        search_index.index_chunk(
            chunk_id=chunk_id,
            document_id=document_id,
            content=content,
            embedding=embedding,
        )

    return len(rows)


def search_document_chunks(
    embedder: Embedder,
    search_index: SearchIndex,
    *,
    query: str,
    limit: int = 5,
) -> list[SearchResult]:
    query_embedding = embedder.embed([query])[0]

    return search_index.vector_search(
        embedding=query_embedding,
        limit=limit,
    )


def format_search_results_as_context(results: list[SearchResult]) -> str:
    if not results:
        return "No relevant document context was found."

    return "\n\n".join(
        (f"[Document {result.document_id}, chunk {result.chunk_id}]\n{result.content}")
        for result in results
    )
