from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager

from src.application.services.pago.pago_service import PagoService


class ServiceFactory(ABC):
    @abstractmethod
    def crear_pago_service(self) -> AbstractAsyncContextManager[PagoService]:
        """Entrega un servicio dentro de una unidad de trabajo independiente."""
        ...
