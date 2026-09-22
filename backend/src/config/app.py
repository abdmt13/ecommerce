from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.container import Container
from src.presentation.controllers.pago_controller import router as pago_router
from src.presentation.pago_exception_handlers import registrar_pago_exception_handlers


def create_app(container: Container | None = None) -> FastAPI:
    container = container if container is not None else Container()
    settings = container.settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.container = container
        database = container.database() if settings.database_url else None
        try:
            yield
        finally:
            if settings.stripe_secret_key and settings.stripe_webhook_secret:
                await container.pasarela_pago().close()
            if database is not None:
                await database.close()
            container.unwire()

    application = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    application.include_router(pago_router)
    registrar_pago_exception_handlers(application)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    return application


app = create_app()
