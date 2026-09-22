from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from src.domain.exceptions.pago import (
    PagoConflictoError,
    PagoError,
    PagoNoEncontradoError,
    PasarelaNoDisponibleError,
    WebhookInvalidoError,
)


async def manejar_pago_error(request: Request, error: PagoError) -> JSONResponse:
    codigos = {
        PagoNoEncontradoError: 404,
        PagoConflictoError: 409,
        WebhookInvalidoError: 400,
        PasarelaNoDisponibleError: 503,
    }
    return JSONResponse(
        status_code=codigos.get(type(error), 500),
        content={"detail": str(error)},
        headers={"Cache-Control": "no-store"},
    )


async def manejar_persistencia_error(request: Request, error: SQLAlchemyError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "No fue posible guardar el pago. Reintenta."},
        headers={"Cache-Control": "no-store", "Retry-After": "5"},
    )


def registrar_pago_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(PagoError, manejar_pago_error)
    app.add_exception_handler(SQLAlchemyError, manejar_persistencia_error)
