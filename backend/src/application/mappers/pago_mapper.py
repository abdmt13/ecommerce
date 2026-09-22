from datetime import UTC, datetime

from src.domain.entity.pago.pago import EstadoPago, Pago
from src.infrastructure.database.models.pago_model import PagoModel


def normalizar_utc(fecha: datetime) -> datetime:
    # MySQL devuelve DATETIME sin tzinfo; el contrato de persistencia exige UTC.
    return fecha.replace(tzinfo=UTC) if fecha.tzinfo is None else fecha.astimezone(UTC)


def mapear_pago(modelo: PagoModel) -> Pago:
    return Pago(
        id=modelo.id,
        id_pedido=modelo.id_pedido,
        id_transaccion_externa=modelo.id_transaccion_externa,
        monto=modelo.monto,
        moneda=modelo.moneda,
        estado=EstadoPago(modelo.estado),
        creado_en=normalizar_utc(modelo.creado_en),
    )
