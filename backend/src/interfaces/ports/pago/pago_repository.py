from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entity.pago.pago import Pago
from src.interfaces.dtos.pago.pago_dto import (
    EventoRegistradoDtoResult,
    GuardarPagoDtoResult,
    ObtenerPagoDtoResult,
    RegistrarEventoDtoResult,
)


class PagoRepository(ABC):
    @abstractmethod
    async def obtener_por_pedido(self, id_pedido: UUID) -> ObtenerPagoDtoResult:
        """Bloquea el pago hasta terminar la unidad de trabajo."""
        ...

    @abstractmethod
    async def obtener_por_id(self, id_pago: UUID) -> ObtenerPagoDtoResult: ...

    @abstractmethod
    async def guardar(self, pago: Pago) -> GuardarPagoDtoResult: ...

    @abstractmethod
    async def existe_evento(self, id_evento: str) -> EventoRegistradoDtoResult: ...

    @abstractmethod
    async def registrar_evento(self, id_evento: str, id_pago: UUID) -> RegistrarEventoDtoResult: ...
