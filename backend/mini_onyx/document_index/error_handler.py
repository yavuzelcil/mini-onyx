from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from mini_onyx.document_index.exceptions import (
    DocumentTooLargeError,
    DocumentValidationError,
)


def register_document_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(DocumentTooLargeError)
    async def handle_document_too_large(
        _request: Request,
        error: DocumentTooLargeError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            content={"detail": str(error)},
        )

    @application.exception_handler(DocumentValidationError)
    async def handle_document_validation_error(
        _request: Request,
        error: DocumentValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(error)},
        )
