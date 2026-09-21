from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from mini_onyx.chat.exceptions import ChatSessionNotFoundError


def register_chat_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(ChatSessionNotFoundError)
    async def handle_chat_session_not_found(
        _request: Request,
        error: ChatSessionNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(error)},
        )
