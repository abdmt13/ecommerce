from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.mappers.pago_mapper import mapear_pago, normalizar_utc
from src.domain.entity.pago.pago import Pago
from src.infrastructure.database.models.pago_model import PagoEventoModel, PagoModel
from src.interfaces.dtos.pago.pago_dto import (
    EventoRegistradoDtoResult,
    GuardarPagoDtoResult,
    ObtenerPagoDtoResult,
    RegistrarEventoDtoResult,
)
from src.interfaces.ports.pago.pago_repository import PagoRepository


class PagoRepositoryAdapter(PagoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def obtener_por_pedido(self, id_pedido: UUID) -> ObtenerPagoDtoResult:
        modelo = await self._session.scalar(
            select(PagoModel).where(PagoModel.id_pedido == id_pedido).with_for_update()
        )
        return self._mapear_resultado(modelo)

    async def obtener_por_id(self, id_pago: UUID) -> ObtenerPagoDtoResult:
        modelo = await self._session.scalar(
            select(PagoModel).where(PagoModel.id == id_pago).with_for_update()
        )
        return self._mapear_resultado(modelo)

    @staticmethod
    def _mapear_resultado(modelo: PagoModel | None) -> ObtenerPagoDtoResult:
        if modelo is None:
            return ObtenerPagoDtoResult(pago=None)
        return ObtenerPagoDtoResult(
            pago=mapear_pago(modelo),
            token_hash=modelo.token_checkout_hash,
            expira_en=normalizar_utc(modelo.expira_en),
        )

    async def guardar(self, pago: Pago) -> GuardarPagoDtoResult:
        modelo = await self._session.get(PagoModel, pago.id)
        if modelo is None:
            raise RuntimeError("El checkout debe persistir el pago antes de usar la pasarela.")
        modelo.id_transaccion_externa = pago.id_transaccion_externa
        modelo.estado = pago.estado.value
        await self._session.flush()
        return GuardarPagoDtoResult(pago=pago)

    async def existe_evento(self, id_evento: str) -> EventoRegistradoDtoResult:
        # Lectura actual también bajo REPEATABLE READ de MySQL.
        evento = await self._session.scalar(
            select(PagoEventoModel).where(PagoEventoModel.id_evento == id_evento).with_for_update()
        )
        return EventoRegistradoDtoResult(existe=evento is not None)

    async def registrar_evento(self, id_evento: str, id_pago: UUID) -> RegistrarEventoDtoResult:
        self._session.add(PagoEventoModel(id_evento=id_evento, id_pago=id_pago))
        await self._session.flush()
        return RegistrarEventoDtoResult()
