from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from src.application.services.pago.pago_service import PagoService
from src.application.services.service_factory import ServiceFactory
from src.application.use_cases.pago.crear_intento_pago_use_case import CrearIntentoPagoUseCase
from src.application.use_cases.pago.procesar_webhook_pago_use_case import ProcesarWebhookPagoUseCase
from src.infrastructure.adapters.pago.pago_repository_adapter import PagoRepositoryAdapter
from src.infrastructure.database.session import Database
from src.interfaces.ports.pago.pasarela_pago_port import PasarelaPagoPort


class PagoServiceFactory(ServiceFactory):
    def __init__(
        self,
        database_factory: Callable[[], Database],
        pasarela_factory: Callable[[], PasarelaPagoPort],
    ) -> None:
        self._database_factory = database_factory
        self._pasarela_factory = pasarela_factory

    @asynccontextmanager
    async def crear_pago_service(self) -> AsyncIterator[PagoService]:
        pasarela = self._pasarela_factory()
        async with self._database_factory().session_factory() as session, session.begin():
            repositorio = PagoRepositoryAdapter(session)
            yield PagoService(
                CrearIntentoPagoUseCase(repositorio, pasarela),
                ProcesarWebhookPagoUseCase(repositorio, pasarela),
            )
