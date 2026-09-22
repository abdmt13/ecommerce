from rmediator.decorators import request_handler

from src.application.commands.pago.procesar_webhook_pago_command import ProcesarWebhookPagoCommand
from src.application.services.service_factory import ServiceFactory
from src.interfaces.dtos.pago.pago_dto import ProcesarWebhookDtoResult


@request_handler(ProcesarWebhookPagoCommand, ProcesarWebhookDtoResult)
class ProcesarWebhookPagoHandler:
    def __init__(self, service_factory: ServiceFactory) -> None:
        self._service_factory = service_factory

    async def handle(self, command: ProcesarWebhookPagoCommand) -> ProcesarWebhookDtoResult:
        async with self._service_factory.crear_pago_service() as service:
            return await service.procesar_webhook(command)
