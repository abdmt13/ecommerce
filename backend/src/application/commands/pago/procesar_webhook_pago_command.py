from dataclasses import dataclass, field

from rmediator.decorators import request

from src.interfaces.dtos.pago.pago_dto import ProcesarWebhookDtoResult


@request(ProcesarWebhookDtoResult)
@dataclass(kw_only=True)
class ProcesarWebhookPagoCommand:
    payload: bytes = field(repr=False)
    firma: str = field(repr=False)
