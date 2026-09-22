from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request, Response
from rmediator import Mediator

from src.application.commands.pago.crear_intento_pago_command import CrearIntentoPagoCommand
from src.application.commands.pago.procesar_webhook_pago_command import ProcesarWebhookPagoCommand
from src.interfaces.dtos.pago.pago_dto import (
    CrearIntentoPagoDto,
    CrearIntentoPagoDtoResult,
    ProcesarWebhookDtoResult,
)

router = APIRouter(prefix="/api/v1/pagos", tags=["Pagos"])


@dataclass
class WebhookHeaders:
    stripe_signature: Annotated[str, Header(alias="stripe-signature", min_length=1)]


async def obtener_intento_dto(
    body: Annotated[CrearIntentoPagoDto, Body()],
) -> CrearIntentoPagoDto:
    return body


async def obtener_webhook_command(
    request: Request, headers: Annotated[WebhookHeaders, Depends()]
) -> ProcesarWebhookPagoCommand:
    payload = bytearray()
    async for fragmento in request.stream():
        payload.extend(fragmento)
        if len(payload) > 1_048_576:
            raise HTTPException(status_code=413, detail="Webhook demasiado grande.")
    return ProcesarWebhookPagoCommand(payload=bytes(payload), firma=headers.stripe_signature)


def obtener_mediator(request: Request) -> Mediator:
    return request.app.state.container.mediator()


@router.post("/intento", response_model=CrearIntentoPagoDtoResult)
async def crear_intento(
    datos: Annotated[CrearIntentoPagoDto, Depends(obtener_intento_dto)],
    mediator: Annotated[Mediator, Depends(obtener_mediator)],
    response: Response,
) -> CrearIntentoPagoDtoResult:
    response.headers["Cache-Control"] = "no-store"
    return await mediator.send(
        CrearIntentoPagoCommand(id_pedido=datos.id_pedido, token_checkout=datos.token_checkout)
    )


@router.post("/webhook", response_model=ProcesarWebhookDtoResult)
async def procesar_webhook(
    command: Annotated[ProcesarWebhookPagoCommand, Depends(obtener_webhook_command)],
    mediator: Annotated[Mediator, Depends(obtener_mediator)],
) -> ProcesarWebhookDtoResult:
    return await mediator.send(command)
