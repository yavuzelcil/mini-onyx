from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from mini_onyx.db.dependencies import get_db_session
from mini_onyx.db.repository import list_document_chunks
from mini_onyx.document_index.dependencies import get_file_store
from mini_onyx.document_index.service import (
    MAX_TEXT_FILE_BYTES,
    chunk_and_store_document,
    get_document_or_raise,
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


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_document(
    file: Annotated[UploadFile, File()],
    db_session: DBSessionDependency,
    file_store: FileStoreDependency,
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

    return UploadedDocumentResponse(
        id=document.id,
        filename=document.filename,
        size_bytes=len(content),
        character_count=len(document.content),
        chunk_count=len(chunks),
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
        )
        for chunk in chunks
    ]
