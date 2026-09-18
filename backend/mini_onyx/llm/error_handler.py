from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from mini_onyx.llm.exceptions import LLMError


def register_llm_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(LLMError)
    async def handle_llm_error(
        _request: Request,
        error: LLMError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": str(error)},
        )
