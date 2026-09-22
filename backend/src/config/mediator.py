from rmediator import Mediator

from src.application.commands.pago.crear_intento_pago_command import CrearIntentoPagoCommand
from src.application.commands.pago.procesar_webhook_pago_command import ProcesarWebhookPagoCommand
from src.application.handlers.pago.crear_intento_pago_handler import CrearIntentoPagoHandler
from src.application.handlers.pago.procesar_webhook_pago_handler import ProcesarWebhookPagoHandler
from src.application.services.service_factory import ServiceFactory


def crear_mediator(service_factory: ServiceFactory) -> Mediator:
    # rmediator 0.2.7 es singleton por clase. Cada aplicación necesita su propio registro.
    class ApplicationMediator(Mediator):
        pass

    mediator = ApplicationMediator()
    mediator.register_handler(CrearIntentoPagoCommand, CrearIntentoPagoHandler(service_factory))
    mediator.register_handler(
        ProcesarWebhookPagoCommand, ProcesarWebhookPagoHandler(service_factory)
    )
    return mediator
