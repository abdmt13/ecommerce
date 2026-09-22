import hashlib
import hmac
from datetime import UTC, datetime, timedelta

from src.application.commands.pago.crear_intento_pago_command import CrearIntentoPagoCommand
from src.domain.exceptions.pago import PagoConflictoError, PagoNoEncontradoError
from src.interfaces.dtos.pago.pago_dto import CrearIntentoPagoDtoResult
from src.interfaces.ports.pago.pago_repository import PagoRepository
from src.interfaces.ports.pago.pasarela_pago_port import PasarelaPagoPort


class CrearIntentoPagoUseCase:
    def __init__(self, repositorio: PagoRepository, pasarela: PasarelaPagoPort) -> None:
        self._repositorio = repositorio
        self._pasarela = pasarela

    async def execute(self, command: CrearIntentoPagoCommand) -> CrearIntentoPagoDtoResult:
        resultado = await self._repositorio.obtener_por_pedido(command.id_pedido)
        pago = resultado.pago
        ahora = datetime.now(UTC)
        token_hash = hashlib.sha256(command.token_checkout.encode()).hexdigest()
        if (
            pago is None
            or resultado.token_hash is None
            or not hmac.compare_digest(token_hash, resultado.token_hash)
            or resultado.expira_en is None
            or resultado.expira_en <= ahora
        ):
            raise PagoNoEncontradoError("Checkout no disponible o expirado.")
        if pago.es_terminal:
            raise PagoConflictoError("El pago ya está finalizado.")
        if pago.id_transaccion_externa is None:
            # Stripe puede eliminar sus claves de idempotencia después de 24 horas.
            # No recrear un intento de resultado incierto una vez vencida esa ventana.
            if ahora - pago.creado_en >= timedelta(hours=23):
                raise PagoConflictoError("El pago requiere conciliación antes de reintentarlo.")
            intento = await self._pasarela.crear_intento(pago)
        else:
            intento = await self._pasarela.obtener_intento(pago.id_transaccion_externa)
        if (
            intento.id_pago != pago.id
            or intento.id_pedido != pago.id_pedido
            or intento.monto_centavos != pago.monto_centavos
            or intento.moneda != pago.moneda
        ):
            raise PagoConflictoError("El intento no coincide con el pedido.")
        pago.id_transaccion_externa = intento.id_transaccion
        # La confirmación del estado local ocurre exclusivamente mediante webhook.
        await self._repositorio.guardar(pago)
        return CrearIntentoPagoDtoResult(
            id_pago=pago.id,
            client_secret=intento.client_secret,
            estado=intento.estado,
            monto=str(pago.monto),
            moneda=pago.moneda,
        )
