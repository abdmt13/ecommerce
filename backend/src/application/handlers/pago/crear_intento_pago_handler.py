from rmediator.decorators import request_handler

from src.application.commands.pago.crear_intento_pago_command import CrearIntentoPagoCommand
from src.application.services.service_factory import ServiceFactory
from src.interfaces.dtos.pago.pago_dto import CrearIntentoPagoDtoResult


@request_handler(CrearIntentoPagoCommand, CrearIntentoPagoDtoResult)
class CrearIntentoPagoHandler:
    def __init__(self, service_factory: ServiceFactory) -> None:
        self._service_factory = service_factory

    async def handle(self, command: CrearIntentoPagoCommand) -> CrearIntentoPagoDtoResult:
        async with self._service_factory.crear_pago_service() as service:
            return await service.crear_intento(command)
