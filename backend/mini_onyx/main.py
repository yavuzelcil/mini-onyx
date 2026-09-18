from fastapi import FastAPI

from mini_onyx.llm.error_handler import register_llm_exception_handlers
from mini_onyx.server.query_and_chat.api import router as chat_router


def create_application() -> FastAPI:
    application = FastAPI(
        title="Mini Onyx Backend",
        version="0.1.0",
    )

    register_llm_exception_handlers(application)
    application.include_router(chat_router, prefix="/api")

    return application


app = create_application()
