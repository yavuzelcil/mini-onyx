import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from mini_onyx.db.models import (
    ChatSession,
    Document,
    DocumentChunk,
    Message,
    Persona,
    User,
)


def create_chat_session(
    db_session: Session,
    *,
    title: str,
    user_id: int | None = None,
    persona_id: int | None = None,
) -> ChatSession:
    chat_session = ChatSession(
        title=title,
        user_id=user_id,
        persona_id=persona_id,
    )
    db_session.add(chat_session)
    db_session.flush()
    return chat_session


def create_message(
    db_session: Session,
    *,
    chat_session_id: int,
    role: str,
    content: str,
) -> Message:
    message = Message(
        session_id=chat_session_id,
        role=role,
        content=content,
    )
    db_session.add(message)
    db_session.flush()
    return message


def list_messages(
    db_session: Session,
    *,
    chat_session_id: int,
) -> list[Message]:
    statement = (
        select(Message)
        .where(Message.session_id == chat_session_id)
        .order_by(Message.id)
    )
    return list(db_session.scalars(statement))


def get_chat_session(
    db_session: Session,
    *,
    chat_session_id: int,
) -> ChatSession | None:
    return db_session.get(ChatSession, chat_session_id)


def get_or_create_persona(
    db_session: Session,
    *,
    name: str,
    system_prompt: str,
) -> Persona:
    persona = db_session.scalar(select(Persona).where(Persona.name == name))
    if persona is not None:
        return persona

    persona = Persona(name=name, system_prompt=system_prompt)
    db_session.add(persona)
    db_session.flush()
    return persona


def get_or_create_user(
    db_session: Session,
    *,
    email: str,
) -> User:
    user = db_session.scalar(select(User).where(User.email == email))
    if user is not None:
        return user

    user = User(email=email)
    db_session.add(user)
    db_session.flush()
    return user


def create_document(
    db_session: Session,
    *,
    filename: str,
    object_key: str,
    content: str,
) -> Document:
    document = Document(filename=filename, object_key=object_key, content=content)
    db_session.add(document)
    db_session.flush()
    return document


def get_document(
    db_session: Session,
    *,
    document_id: int,
) -> Document | None:
    return db_session.get(Document, document_id)


def create_document_chunks(
    db_session: Session,
    *,
    document_id: int,
    chunks: list[tuple[str, int]],
) -> list[DocumentChunk]:
    rows = [
        DocumentChunk(
            document_id=document_id,
            chunk_index=index,
            content=content,
            token_count=token_count,
        )
        for index, (content, token_count) in enumerate(chunks)
    ]
    db_session.add_all(rows)
    db_session.flush()
    return rows


def list_document_chunks(
    db_session: Session,
    *,
    document_id: int,
) -> list[DocumentChunk]:
    statement = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )
    return list(db_session.scalars(statement))


def update_chunk_embedding(
    db_session: Session,
    *,
    chunk_id: int,
    embedding: list[float],
) -> None:
    chunk = db_session.get_one(DocumentChunk, chunk_id)
    chunk.embedding = json.dumps(embedding)
