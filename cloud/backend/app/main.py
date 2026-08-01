"""FastAPI application factory.

Entry point for uvicorn: `uvicorn app.main:app --reload`
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import close_db, init_db
from app.middleware.cors import add_cors
from app.middleware.error_handler import register_error_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.router import top_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup and shutdown lifecycle."""
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    application = FastAPI(
        title="Danke Parent Backend",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware (order matters: CORS outermost, request ID, then error handlers)
    add_cors(application)
    application.add_middleware(RequestIDMiddleware)
    register_error_handlers(application)

    application.include_router(top_router)

    return application


app = create_app()
