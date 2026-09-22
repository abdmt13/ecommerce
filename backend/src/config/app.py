from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.container import Container


def create_app() -> FastAPI:
    container = Container()
    settings = container.settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.container = container
        database = container.database() if settings.database_url else None
        try:
            yield
        finally:
            if database is not None:
                await database.close()
            container.unwire()

    application = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    return application


app = create_app()
