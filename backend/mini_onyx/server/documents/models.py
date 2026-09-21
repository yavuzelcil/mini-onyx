from pydantic import BaseModel


class UploadedDocumentResponse(BaseModel):
    id: int
    filename: str
    size_bytes: int
    character_count: int
