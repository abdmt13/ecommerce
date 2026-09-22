import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
import stripe
from dependency_injector import providers
from sqlalchemy import func, select, text
from src.config.app import create_app
from src.config.container import Container
from src.config.settings import Settings
from src.infrastructure.adapters.pago.stripe_adapter import StripePaymentAdapter
from src.infrastructure.database.models.pago_model import PagoEventoModel, PagoModel
from src.infrastructure.database.session import Database
from tests.unit.test_stripe_adapter import WEBHOOK_SECRET, crear_evento_firmado, crear_stripe_intent


@pytest.fixture
async def database():
    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada.")
    if not url.startswith("postgresql+asyncpg://") or not url.endswith("/pagos_test"):
        pytest.fail("Usar exclusivamente una base PostgreSQL dedicada llamada pagos_test.")
    database = Database(database_url=url)
    schema = "test_pagos_" + uuid4().hex
    sql = Path("src/infrastructure/database/schema/001_pagos.postgresql.sql").read_text("utf-8")
    try:
        async with database.engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            for sentencia in sql.split(";"):
                sentencia = "\n".join(
                    linea for linea in sentencia.splitlines() if not linea.strip().startswith("--")
                ).strip()
                if sentencia and sentencia not in {"BEGIN", "COMMIT"}:
                    await connection.execute(text(sentencia))
        database.session_factory.configure(
            bind=database.engine.execution_options(schema_translate_map={None: schema})
        )
        yield database
    finally:
        async with database.engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await database.close()


@pytest.fixture
async def api(database, pago, token_hash, expira_en):
    async with database.session_factory() as session, session.begin():
        session.add(
            PagoModel(
                id=pago.id,
                id_pedido=pago.id_pedido,
                id_transaccion_externa=None,
                monto=pago.monto,
                moneda=pago.moneda,
                estado=pago.estado.value,
                creado_en=pago.creado_en,
                token_checkout_hash=token_hash,
                expira_en=expira_en,
            )
        )
    adapter = StripePaymentAdapter("sk_test_fake", WEBHOOK_SECRET)
    adapter._client.v1.payment_intents.create_async = AsyncMock(
        return_value=crear_stripe_intent(pago)
    )
    adapter._client.v1.payment_intents.retrieve_async = AsyncMock(
        return_value=crear_stripe_intent(pago)
    )
    container = Container()
    container.settings.override(providers.Object(Settings(_env_file=None)))
    container.database.override(providers.Object(database))
    container.pasarela_pago.override(providers.Object(adapter))
    app = create_app(container)
    try:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                yield {"client": client, "adapter": adapter}
    finally:
        await adapter.close()


async def test_intentos_concurrentes_crean_un_solo_payment_intent(
    api, pago, token_checkout, database
):
    body = {"id_pedido": str(pago.id_pedido), "token_checkout": token_checkout}
    respuestas = await asyncio.gather(
        api["client"].post("/api/v1/pagos/intento", json=body),
        api["client"].post("/api/v1/pagos/intento", json=body),
    )
    assert [respuesta.status_code for respuesta in respuestas] == [200, 200]
    assert respuestas[0].json()["client_secret"] == respuestas[1].json()["client_secret"]
    assert respuestas[0].headers["cache-control"] == "no-store"
    api["adapter"]._client.v1.payment_intents.create_async.assert_awaited_once()
    async with database.session_factory() as session:
        registro = await session.get(PagoModel, pago.id)
        assert registro.id_transaccion_externa == "pi_test"
        assert registro.estado == "pendiente"


async def test_webhooks_concurrentes_confirman_una_vez(api, pago, database):
    api["adapter"]._client.v1.payment_intents.retrieve_async.return_value = crear_stripe_intent(
        pago, "succeeded"
    )
    evento = crear_evento_firmado(pago)
    respuestas = await asyncio.gather(
        *[
            api["client"].post(
                "/api/v1/pagos/webhook",
                content=evento["payload"],
                headers={"stripe-signature": evento["firma"]},
            )
            for _ in range(2)
        ]
    )
    assert [respuesta.status_code for respuesta in respuestas] == [200, 200]
    assert sum(respuesta.json()["procesado"] for respuesta in respuestas) == 1
    assert sum(respuesta.json()["duplicado"] for respuesta in respuestas) == 1
    async with database.session_factory() as session:
        registro = await session.get(PagoModel, pago.id)
        assert registro.estado == "exitoso"
        assert registro.id_transaccion_externa == "pi_test"
        assert await session.scalar(select(func.count()).select_from(PagoEventoModel)) == 1


async def test_reintento_despues_de_fallo_stripe(api, pago, token_checkout, database):
    crear = api["adapter"]._client.v1.payment_intents.create_async
    crear.side_effect = stripe.APIConnectionError("no divulgar")
    body = {"id_pedido": str(pago.id_pedido), "token_checkout": token_checkout}
    respuesta = await api["client"].post("/api/v1/pagos/intento", json=body)
    assert respuesta.status_code == 503
    assert "no divulgar" not in respuesta.text
    async with database.session_factory() as session:
        assert (await session.get(PagoModel, pago.id)).id_transaccion_externa is None
    crear.side_effect = None
    respuesta = await api["client"].post("/api/v1/pagos/intento", json=body)
    assert respuesta.status_code == 200
    assert crear.call_args_list[0].kwargs == crear.call_args_list[1].kwargs


async def test_error_guardando_evento_revierte_estado(api, pago, database):
    # Provocar un fallo de persistencia posterior a guardar el estado en la misma transacción.
    async with database.engine.begin() as connection:
        schema = database.session_factory.kw["bind"].get_execution_options()[
            "schema_translate_map"
        ][None]
        await connection.execute(
            text(
                f'ALTER TABLE "{schema}".pago_eventos ADD CONSTRAINT rechazar_evento CHECK (false)'
            )
        )
    api["adapter"]._client.v1.payment_intents.retrieve_async.return_value = crear_stripe_intent(
        pago, "succeeded"
    )
    evento = crear_evento_firmado(pago)
    respuesta = await api["client"].post(
        "/api/v1/pagos/webhook",
        content=evento["payload"],
        headers={"stripe-signature": evento["firma"]},
    )
    assert respuesta.status_code == 503
    async with database.session_factory() as session:
        registro = await session.get(PagoModel, pago.id)
        assert registro.estado == "pendiente"
        assert registro.id_transaccion_externa is None


async def test_endpoint_rechaza_firma_invalida_sin_acceder_stripe(api, pago):
    evento = crear_evento_firmado(pago)
    respuesta = await api["client"].post(
        "/api/v1/pagos/webhook",
        content=evento["payload"] + b" ",
        headers={"stripe-signature": evento["firma"]},
    )
    assert respuesta.status_code == 400
    api["adapter"]._client.v1.payment_intents.retrieve_async.assert_not_called()


async def test_endpoint_rechaza_dinero_cliente_y_token_incorrecto(api, pago, token_checkout):
    respuesta = await api["client"].post(
        "/api/v1/pagos/intento",
        json={
            "id_pedido": str(pago.id_pedido),
            "token_checkout": token_checkout,
            "monto": "0.01",
        },
    )
    assert respuesta.status_code == 422
    respuesta = await api["client"].post(
        "/api/v1/pagos/intento",
        json={
            "id_pedido": str(pago.id_pedido),
            "token_checkout": "token_incorrecto_" * 4,
        },
    )
    assert respuesta.status_code == 404
    api["adapter"]._client.v1.payment_intents.create_async.assert_not_called()


async def test_endpoint_exige_firma(api):
    respuesta = await api["client"].post("/api/v1/pagos/webhook", content=b"{}")
    assert respuesta.status_code == 422


async def test_evento_no_soportado_no_modifica_pagos(api, pago, database):
    evento = crear_evento_firmado(pago, tipo="customer.created")
    respuesta = await api["client"].post(
        "/api/v1/pagos/webhook",
        content=evento["payload"],
        headers={"stripe-signature": evento["firma"]},
    )
    assert respuesta.status_code == 200
    assert not respuesta.json()["procesado"]
    async with database.session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(PagoEventoModel)) == 0


async def test_aplicaciones_tienen_registros_mediator_independientes():
    primera = Container()
    segunda = Container()
    assert primera.mediator() is not segunda.mediator()
