from abc import ABC, abstractmethod

from src.domain.entity.pago.pago import Pago
from src.interfaces.dtos.pago.pago_dto import (
    EventoPasarelaDtoResult,
    IntentoPasarelaDtoResult,
)


class PasarelaPagoPort(ABC):
    @abstractmethod
    async def crear_intento(self, pago: Pago) -> IntentoPasarelaDtoResult: ...

    @abstractmethod
    async def obtener_intento(self, id_transaccion: str) -> IntentoPasarelaDtoResult: ...

    @abstractmethod
    def validar_webhook(self, payload: bytes, firma: str) -> EventoPasarelaDtoResult: ...
