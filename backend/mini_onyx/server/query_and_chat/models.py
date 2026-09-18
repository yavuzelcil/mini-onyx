from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(max_length=4_000)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("Message must not be blank")

        return stripped_value


class ChatResponse(BaseModel):
    reply: str


class ChatStreamDelta(BaseModel):
    type: Literal["content_delta"] = "content_delta"
    content: str


class ChatStreamDone(BaseModel):
    type: Literal["done"] = "done"


class ChatStreamError(BaseModel):
    type: Literal["error"] = "error"
    detail: str
