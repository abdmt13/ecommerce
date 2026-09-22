from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class EstadoPago(StrEnum):
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    EXITOSO = "exitoso"
    FALLIDO = "fallido"
    CANCELADO = "cancelado"


@dataclass(kw_only=True)
class Pago:
    id: UUID
    id_pedido: UUID
    id_transaccion_externa: str | None
    monto: Decimal
    moneda: str
    estado: EstadoPago
    creado_en: datetime

    def __post_init__(self) -> None:
        if (
            not self.monto.is_finite()
            or self.monto <= 0
            or self.monto > Decimal("999999.99")
            or self.monto * 100 != (self.monto * 100).to_integral_value()
        ):
            raise ValueError("El monto debe ser positivo y tener como máximo dos decimales.")
        if self.moneda not in {"mxn", "usd", "eur"}:
            raise ValueError("Moneda no soportada.")

    @property
    def monto_centavos(self) -> int:
        # El contrato de este módulo admite exclusivamente monedas de dos decimales.
        return int(self.monto * 100)

    @property
    def es_terminal(self) -> bool:
        return self.estado in {EstadoPago.EXITOSO, EstadoPago.CANCELADO}
