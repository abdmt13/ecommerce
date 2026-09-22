from src.application.commands.pago.crear_intento_pago_command import CrearIntentoPagoCommand
from src.application.commands.pago.procesar_webhook_pago_command import ProcesarWebhookPagoCommand
from src.application.use_cases.pago.crear_intento_pago_use_case import CrearIntentoPagoUseCase
from src.application.use_cases.pago.procesar_webhook_pago_use_case import ProcesarWebhookPagoUseCase
from src.interfaces.dtos.pago.pago_dto import CrearIntentoPagoDtoResult, ProcesarWebhookDtoResult


class PagoService:
    def __init__(
        self, crear_intento: CrearIntentoPagoUseCase, procesar_webhook: ProcesarWebhookPagoUseCase
    ) -> None:
        self._crear_intento = crear_intento
        self._procesar_webhook = procesar_webhook

    async def crear_intento(self, command: CrearIntentoPagoCommand) -> CrearIntentoPagoDtoResult:
        return await self._crear_intento.execute(command)

    async def procesar_webhook(
        self, command: ProcesarWebhookPagoCommand
    ) -> ProcesarWebhookDtoResult:
        return await self._procesar_webhook.execute(command)
