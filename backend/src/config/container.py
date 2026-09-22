from dependency_injector import containers, providers

from src.config.mediator import crear_mediator
from src.config.settings import Settings
from src.infrastructure.adapters.pago.pago_service_factory import PagoServiceFactory
from src.infrastructure.adapters.pago.stripe_adapter import StripePaymentAdapter
from src.infrastructure.database.session import Database


class Container(containers.DeclarativeContainer):
    settings = providers.Singleton(Settings)
    database = providers.Singleton(Database, database_url=settings.provided.database_url)
    pasarela_pago = providers.Singleton(
        StripePaymentAdapter,
        secret_key=settings.provided.stripe_secret_key,
        webhook_secret=settings.provided.stripe_webhook_secret,
    )
    service_factory = providers.Singleton(
        PagoServiceFactory,
        database_factory=database.provider,
        pasarela_factory=pasarela_pago.provider,
    )
    mediator = providers.Singleton(crear_mediator, service_factory=service_factory)
