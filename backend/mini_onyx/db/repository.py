from sqlalchemy import select
from sqlalchemy.orm import Session

from mini_onyx.db.models import ChatSession, Message


def create_chat_session(
    db_session: Session,
    *,
    title: str,
) -> ChatSession:
    chat_session = ChatSession(title=title)
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
