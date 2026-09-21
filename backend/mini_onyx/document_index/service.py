from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from mini_onyx.db.models import Document
from mini_onyx.db.repository import create_document
from mini_onyx.document_index.exceptions import (
    DocumentTooLargeError,
    DocumentValidationError,
)
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
