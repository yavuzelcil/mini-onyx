from pydantic import BaseModel


class UploadedDocumentResponse(BaseModel):
    id: int
    filename: str
    size_bytes: int
    character_count: int
    chunk_count: int


class DocumentChunkResponse(BaseModel):
    chunk_index: int
    content: str
    token_count: int
