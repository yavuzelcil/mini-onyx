from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from mini_onyx.db.dependencies import get_db_session
from mini_onyx.db.models import Base, Document
from mini_onyx.document_index.dependencies import get_file_store
from mini_onyx.document_index.service import save_text_document
from mini_onyx.main import app


class FakeFileStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put(self, *, key: str, content: bytes) -> None:
        self.objects[key] = content

    def delete(self, *, key: str) -> None:
        self.objects.pop(key, None)


@pytest.fixture
def upload_client() -> Iterator[tuple[TestClient, FakeFileStore, Engine]]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    file_store = FakeFileStore()

    def get_test_db_session() -> Iterator[Session]:
        with Session(engine, expire_on_commit=False) as db_session:
            yield db_session

    def get_test_file_store() -> FakeFileStore:
        return file_store

    app.dependency_overrides[get_db_session] = get_test_db_session
    app.dependency_overrides[get_file_store] = get_test_file_store

    try:
        with TestClient(app) as client:
            yield client, file_store, engine
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_file_store, None)
        engine.dispose()


def test_upload_saves_raw_file_and_extracted_text(
    upload_client: tuple[TestClient, FakeFileStore, Engine],
) -> None:
    client, file_store, engine = upload_client
    content = b"Merhaba Mini Onyx"

    response = client.post(
        "/api/documents/upload",
        files={"file": ("notes.txt", content, "text/plain")},
    )

    assert response.status_code == 201
    assert response.json()["filename"] == "notes.txt"
    assert response.json()["size_bytes"] == len(content)
    assert list(file_store.objects.values()) == [content]

    with Session(engine) as db_session:
        document = db_session.scalar(select(Document))
        assert document is not None
        assert document.id == response.json()["id"]
        assert document.content == "Merhaba Mini Onyx"
        assert document.object_key in file_store.objects


def test_upload_creates_and_lists_chunks(
    upload_client: tuple[TestClient, FakeFileStore, Engine],
) -> None:
    client, _, _ = upload_client
    content = ("Birinci paragraf. " * 3 + "\n\n" + "Ikinci paragraf. " * 3).encode()

    uploaded = client.post(
        "/api/documents/upload",
        files={"file": ("notes.txt", content, "text/plain")},
    )
    document_id = uploaded.json()["id"]

    assert uploaded.json()["chunk_count"] >= 1

    chunks = client.get(f"/api/documents/{document_id}/chunks")

    assert chunks.status_code == 200
    assert len(chunks.json()) == uploaded.json()["chunk_count"]
    assert chunks.json()[0]["chunk_index"] == 0


def test_chunks_for_missing_document_return_404(
    upload_client: tuple[TestClient, FakeFileStore, Engine],
) -> None:
    client, _, _ = upload_client
    response = client.get("/api/documents/999/chunks")

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("filename", "content", "expected_status"),
    [
        ("notes.pdf", b"not a PDF", 400),
        ("notes.txt", b"\xff", 400),
        ("notes.txt", b" ", 400),
        ("notes.txt", b"x" * 1_000_001, 413),
    ],
    ids=["extension", "invalid_utf8", "blank", "too_large"],
)
def test_upload_rejects_unsupported_files(
    upload_client: tuple[TestClient, FakeFileStore, Engine],
    filename: str,
    content: bytes,
    expected_status: int,
) -> None:
    client, file_store, engine = upload_client

    response = client.post(
        "/api/documents/upload",
        files={"file": (filename, content, "application/octet-stream")},
    )

    assert response.status_code == expected_status
    assert file_store.objects == {}
    with Session(engine) as db_session:
        assert db_session.scalar(select(Document)) is None


def test_save_text_document_deletes_object_when_database_write_fails() -> None:
    engine = create_engine("sqlite+pysqlite://")
    # Intentionally do not create any tables, so the insert fails.
    file_store = FakeFileStore()

    with Session(engine) as db_session:
        with pytest.raises(SQLAlchemyError):
            save_text_document(
                db_session,
                file_store,
                filename="notes.txt",
                content=b"Hello",
            )

    assert file_store.objects == {}
