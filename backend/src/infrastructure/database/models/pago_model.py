from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.models.base import Base


class PagoModel(Base):
    __tablename__ = "pagos"
    __table_args__ = (
        CheckConstraint("monto > 0 AND monto <= 999999.99", name="ck_pagos_monto"),
        CheckConstraint("moneda IN ('mxn', 'usd', 'eur')", name="ck_pagos_moneda"),
        CheckConstraint(
            "estado IN ('pendiente', 'procesando', 'exitoso', 'fallido', 'cancelado')",
            name="ck_pagos_estado",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    id_pedido: Mapped[UUID] = mapped_column(Uuid, unique=True)
    id_transaccion_externa: Mapped[str | None] = mapped_column(String(255), unique=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    moneda: Mapped[str] = mapped_column(String(3))
    estado: Mapped[str] = mapped_column(String(20))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    token_checkout_hash: Mapped[str] = mapped_column(String(64))
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PagoEventoModel(Base):
    __tablename__ = "pago_eventos"

    id_evento: Mapped[str] = mapped_column(String(255), primary_key=True)
    id_pago: Mapped[UUID] = mapped_column(ForeignKey("pagos.id"), index=True)
