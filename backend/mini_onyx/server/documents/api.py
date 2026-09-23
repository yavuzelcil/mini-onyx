from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from mini_onyx.db.dependencies import get_db_session
from mini_onyx.db.repository import list_document_chunks
from mini_onyx.document_index.dependencies import (
    get_embedder,
    get_file_store,
    get_search_index,
)
from mini_onyx.document_index.embedder import Embedder
from mini_onyx.document_index.search_index import SearchIndex
from mini_onyx.document_index.service import (
    MAX_TEXT_FILE_BYTES,
    chunk_and_store_document,
    embed_document_chunks,
    get_document_or_raise,
    index_document_chunks,
    save_text_document,
)
from mini_onyx.document_index.storage import FileStore
from mini_onyx.server.documents.models import (
    DocumentChunkResponse,
    UploadedDocumentResponse,
)

router = APIRouter(prefix="/documents", tags=["Documents"])

DBSessionDependency = Annotated[Session, Depends(get_db_session)]
FileStoreDependency = Annotated[FileStore, Depends(get_file_store)]
EmbedderDependency = Annotated[Embedder, Depends(get_embedder)]
SearchIndexDependency = Annotated[SearchIndex, Depends(get_search_index)]


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_document(
    file: Annotated[UploadFile, File()],
    db_session: DBSessionDependency,
    file_store: FileStoreDependency,
    embedder: EmbedderDependency,
    search_index: SearchIndexDependency,
) -> UploadedDocumentResponse:
    content = file.file.read(MAX_TEXT_FILE_BYTES + 1)
    document = save_text_document(
        db_session,
        file_store,
        filename=file.filename,
        content=content,
    )
    chunks = chunk_and_store_document(
        db_session,
        document_id=document.id,
        content=document.content,
    )
    embedding_dimensions = embed_document_chunks(
        db_session,
        embedder,
        document_id=document.id,
    )
    indexed_chunk_count = index_document_chunks(
        db_session,
        search_index,
        document_id=document.id,
    )

    return UploadedDocumentResponse(
        id=document.id,
        filename=document.filename,
        size_bytes=len(content),
        character_count=len(document.content),
        chunk_count=len(chunks),
        embedding_dimensions=embedding_dimensions,
        indexed_chunk_count=indexed_chunk_count,
    )


@router.get("/{document_id}/chunks")
def list_document_chunks_route(
    document_id: int,
    db_session: DBSessionDependency,
) -> list[DocumentChunkResponse]:
    document = get_document_or_raise(db_session, document_id=document_id)
    chunks = list_document_chunks(db_session, document_id=document.id)

    return [
        DocumentChunkResponse(
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            token_count=chunk.token_count,
            has_embedding=chunk.embedding is not None,
        )
        for chunk in chunks
    ]
