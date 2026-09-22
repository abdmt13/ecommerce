from dependency_injector import containers, providers
from rmediator import Mediator

from src.config.settings import Settings
from src.infrastructure.database.session import Database


class Container(containers.DeclarativeContainer):
    settings = providers.Singleton(Settings)
    database = providers.Singleton(Database, database_url=settings.provided.database_url)
    # Registrar handlers mediante DI al incorporar cada módulo de negocio.
    mediator = providers.Singleton(Mediator)
