from src.application.commands.pago.procesar_webhook_pago_command import ProcesarWebhookPagoCommand
from src.domain.exceptions.pago import PagoConflictoError, PasarelaNoDisponibleError
from src.interfaces.dtos.pago.pago_dto import ProcesarWebhookDtoResult
from src.interfaces.ports.pago.pago_repository import PagoRepository
from src.interfaces.ports.pago.pasarela_pago_port import PasarelaPagoPort


class ProcesarWebhookPagoUseCase:
    def __init__(self, repositorio: PagoRepository, pasarela: PasarelaPagoPort) -> None:
        self._repositorio = repositorio
        self._pasarela = pasarela

    async def execute(self, command: ProcesarWebhookPagoCommand) -> ProcesarWebhookDtoResult:
        evento = self._pasarela.validar_webhook(command.payload, command.firma)
        if not evento.es_relevante or evento.id_pago is None or evento.id_transaccion is None:
            return ProcesarWebhookDtoResult(procesado=False)
        resultado = await self._repositorio.obtener_por_id(evento.id_pago)
        pago = resultado.pago
        if pago is None:
            # No reconocer como procesado un evento previo al commit del checkout.
            raise PasarelaNoDisponibleError("Pago aún no disponible; reintentar el webhook.")
        if (await self._repositorio.existe_evento(evento.id_evento)).existe:
            return ProcesarWebhookDtoResult(procesado=False, duplicado=True)
        # Leer el estado actual evita regresiones por eventos entregados fuera de orden.
        intento = await self._pasarela.obtener_intento(evento.id_transaccion)
        if (
            intento.id_pago != pago.id
            or intento.id_pedido != pago.id_pedido
            or intento.monto_centavos != pago.monto_centavos
            or intento.moneda != pago.moneda
            or pago.id_transaccion_externa not in {None, intento.id_transaccion}
        ):
            raise PagoConflictoError("El evento no corresponde al pago registrado.")
        pago.id_transaccion_externa = intento.id_transaccion
        if not pago.es_terminal:
            pago.estado = intento.estado
        await self._repositorio.guardar(pago)
        await self._repositorio.registrar_evento(evento.id_evento, pago.id)
        return ProcesarWebhookDtoResult(procesado=True)
