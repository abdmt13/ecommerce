from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.domain.entity.pago.pago import EstadoPago, Pago


class CrearIntentoPagoDto(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_pedido: UUID
    token_checkout: str = Field(min_length=32, max_length=256, repr=False)


class CrearIntentoPagoDtoResult(BaseModel):
    id_pago: UUID
    client_secret: str = Field(repr=False)
    estado: EstadoPago
    monto: str
    moneda: str


class ProcesarWebhookDtoResult(BaseModel):
    recibido: bool = True
    procesado: bool
    duplicado: bool = False


class ObtenerPagoDtoResult(BaseModel):
    pago: Pago | None
    token_hash: str | None = Field(default=None, repr=False)
    expira_en: datetime | None = None


class GuardarPagoDtoResult(BaseModel):
    pago: Pago


class IntentoPasarelaDtoResult(BaseModel):
    id_transaccion: str
    client_secret: str = Field(repr=False)
    estado: EstadoPago
    monto_centavos: int
    moneda: str
    id_pago: UUID
    id_pedido: UUID


class EventoPasarelaDtoResult(BaseModel):
    id_evento: str
    tipo: str
    id_pago: UUID | None = None
    id_transaccion: str | None = None
    es_relevante: bool


class EventoRegistradoDtoResult(BaseModel):
    existe: bool


class RegistrarEventoDtoResult(BaseModel):
    registrado: Literal[True] = True
