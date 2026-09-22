import hashlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from src.domain.entity.pago.pago import EstadoPago, Pago


@pytest.fixture
def token_checkout():
    return "token-de-checkout-solo-para-pruebas-123456789"


@pytest.fixture
def token_hash(token_checkout):
    return hashlib.sha256(token_checkout.encode()).hexdigest()


@pytest.fixture
def pago():
    return Pago(
        id=uuid4(),
        id_pedido=uuid4(),
        id_transaccion_externa=None,
        monto=Decimal("249.90"),
        moneda="mxn",
        estado=EstadoPago.PENDIENTE,
        creado_en=datetime.now(UTC),
    )


@pytest.fixture
def expira_en():
    return datetime.now(UTC) + timedelta(hours=1)
