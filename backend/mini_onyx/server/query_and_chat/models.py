from typing import Literal

from pydantic import BaseModel, Field, field_validator

from mini_onyx.chat.personas import PERSONA_PRESETS


class ChatRequest(BaseModel):
    message: str = Field(max_length=4_000)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("Message must not be blank")

        return stripped_value


class SessionChatRequest(ChatRequest):
    use_rag: bool = False


class ChatResponse(BaseModel):
    reply: str


class ChatSourceResponse(BaseModel):
    chunk_id: int
    document_id: int
    content: str
    score: float


class ChatStreamSources(BaseModel):
    type: Literal["sources"] = "sources"
    sources: list[ChatSourceResponse]


class ChatStreamDelta(BaseModel):
    type: Literal["content_delta"] = "content_delta"
    content: str


class ChatStreamDone(BaseModel):
    type: Literal["done"] = "done"


class ChatStreamError(BaseModel):
    type: Literal["error"] = "error"
    detail: str


class CreateChatSessionRequest(BaseModel):
    title: str = Field(max_length=200)
    persona_name: str | None = None

    @field_validator("persona_name")
    @classmethod
    def validate_persona_name(cls, value: str | None) -> str | None:
        if value is not None and value not in PERSONA_PRESETS:
            raise ValueError("Unknown persona")

        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        title = value.strip()

        if not title:
            raise ValueError("Title must not be blank")

        return title


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    persona_name: str | None


class StoredMessageResponse(BaseModel):
    id: int
    role: str
    content: str


class PersonaResponse(BaseModel):
    name: str
