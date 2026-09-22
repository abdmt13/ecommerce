import hashlib
import hmac
import json
import time
from unittest.mock import AsyncMock

import pytest
import stripe
from src.domain.exceptions.pago import PasarelaNoDisponibleError, WebhookInvalidoError
from src.infrastructure.adapters.pago.stripe_adapter import StripePaymentAdapter

WEBHOOK_SECRET = "whsec_test_only"


def crear_evento_firmado(pago, *, tipo="payment_intent.succeeded", timestamp=None, modulo=None):
    contenido = {
        "id": "evt_test",
        "object": "event",
        "type": tipo,
        "livemode": False,
        "data": {
            "object": {
                "id": "pi_test",
                "object": "payment_intent",
                "metadata": {
                    "modulo": modulo or StripePaymentAdapter.MODULO,
                    "id_pago": str(pago.id),
                    "id_pedido": str(pago.id_pedido),
                },
            }
        },
    }
    payload = json.dumps(contenido).encode()
    timestamp = timestamp if timestamp is not None else int(time.time())
    firma = hmac.new(
        WEBHOOK_SECRET.encode(), str(timestamp).encode() + b"." + payload, hashlib.sha256
    ).hexdigest()
    return {"payload": payload, "firma": f"t={timestamp},v1={firma}"}


@pytest.fixture
async def adapter():
    adapter = StripePaymentAdapter("sk_test_fake", WEBHOOK_SECRET)
    yield adapter
    await adapter.close()


def crear_stripe_intent(pago, estado="requires_payment_method"):
    return stripe.PaymentIntent.construct_from(
        {
            "id": "pi_test",
            "object": "payment_intent",
            "client_secret": "pi_test_secret_test",
            "status": estado,
            "amount": pago.monto_centavos,
            "currency": pago.moneda,
            "livemode": False,
            "last_payment_error": None,
            "metadata": {
                "modulo": StripePaymentAdapter.MODULO,
                "id_pago": str(pago.id),
                "id_pedido": str(pago.id_pedido),
            },
        },
        "sk_test_fake",
    )


async def test_sdk_async_usa_idempotencia_estable(adapter, pago):
    adapter._client.v1.payment_intents.create_async = AsyncMock(
        return_value=crear_stripe_intent(pago)
    )
    resultado = await adapter.crear_intento(pago)
    argumentos = adapter._client.v1.payment_intents.create_async.call_args
    assert argumentos.args[0]["amount"] == 24990
    assert argumentos.kwargs["options"] == {"idempotency_key": f"pago:{pago.id}"}
    assert resultado.id_pago == pago.id


async def test_error_sdk_no_expone_detalles(adapter, pago):
    adapter._client.v1.payment_intents.create_async = AsyncMock(
        side_effect=stripe.APIConnectionError("secret-detail")
    )
    with pytest.raises(PasarelaNoDisponibleError, match="iniciar") as error:
        await adapter.crear_intento(pago)
    assert "secret-detail" not in str(error.value)


async def test_firma_criptografica_real(adapter, pago):
    evento = crear_evento_firmado(pago)
    resultado = adapter.validar_webhook(evento["payload"], evento["firma"])
    assert resultado.id_pago == pago.id
    assert resultado.es_relevante


@pytest.mark.parametrize("alteracion", ["payload", "firma", "vencida"])
async def test_rechaza_webhook_alterado_o_replay_vencido(alteracion, adapter, pago):
    evento = crear_evento_firmado(
        pago, timestamp=int(time.time()) - 600 if alteracion == "vencida" else None
    )
    if alteracion == "payload":
        evento["payload"] += b" "
    if alteracion == "firma":
        evento["firma"] = "t=1,v1=no-valida"
    with pytest.raises(WebhookInvalidoError):
        adapter.validar_webhook(evento["payload"], evento["firma"])


async def test_ignora_eventos_de_otro_modulo(adapter, pago):
    evento = crear_evento_firmado(pago, modulo="otro_checkout")
    assert not adapter.validar_webhook(evento["payload"], evento["firma"]).es_relevante


async def test_ignora_eventos_no_soportados(adapter, pago):
    evento = crear_evento_firmado(pago, tipo="customer.created")
    assert not adapter.validar_webhook(evento["payload"], evento["firma"]).es_relevante
