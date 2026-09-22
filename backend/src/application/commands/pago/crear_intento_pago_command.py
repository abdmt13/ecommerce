from dataclasses import dataclass, field
from uuid import UUID

from rmediator.decorators import request

from src.interfaces.dtos.pago.pago_dto import CrearIntentoPagoDtoResult


@request(CrearIntentoPagoDtoResult)
@dataclass(kw_only=True)
class CrearIntentoPagoCommand:
    id_pedido: UUID
    token_checkout: str = field(repr=False)
