from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest
from src.application.commands.pago.crear_intento_pago_command import CrearIntentoPagoCommand
from src.application.commands.pago.procesar_webhook_pago_command import ProcesarWebhookPagoCommand
from src.application.use_cases.pago.crear_intento_pago_use_case import CrearIntentoPagoUseCase
from src.application.use_cases.pago.procesar_webhook_pago_use_case import ProcesarWebhookPagoUseCase
from src.domain.entity.pago.pago import EstadoPago, Pago
from src.domain.exceptions.pago import (
    PagoConflictoError,
    PagoNoEncontradoError,
    PasarelaNoDisponibleError,
)
from src.interfaces.dtos.pago.pago_dto import (
    EventoPasarelaDtoResult,
    EventoRegistradoDtoResult,
    IntentoPasarelaDtoResult,
    ObtenerPagoDtoResult,
)
from src.interfaces.ports.pago.pago_repository import PagoRepository
from src.interfaces.ports.pago.pasarela_pago_port import PasarelaPagoPort


@pytest.fixture
def repositorio(pago, token_hash, expira_en):
    repositorio = AsyncMock(spec=PagoRepository)
    resultado = ObtenerPagoDtoResult(pago=pago, token_hash=token_hash, expira_en=expira_en)
    repositorio.obtener_por_pedido.return_value = resultado
    repositorio.obtener_por_id.return_value = resultado
    repositorio.existe_evento.return_value = EventoRegistradoDtoResult(existe=False)
    return repositorio


@pytest.fixture
def pasarela(pago):
    pasarela = Mock(spec=PasarelaPagoPort)
    intento = IntentoPasarelaDtoResult(
        id_transaccion="pi_test",
        client_secret="pi_test_secret_test",
        estado=EstadoPago.PENDIENTE,
        monto_centavos=24990,
        moneda="mxn",
        id_pago=pago.id,
        id_pedido=pago.id_pedido,
    )
    pasarela.crear_intento.return_value = intento
    pasarela.obtener_intento.return_value = intento
    pasarela.validar_webhook.return_value = EventoPasarelaDtoResult(
        id_evento="evt_test",
        tipo="payment_intent.succeeded",
        es_relevante=True,
        id_pago=pago.id,
        id_transaccion="pi_test",
    )
    return pasarela


async def test_crear_usa_importe_servidor_y_reutiliza_intento(
    pago, repositorio, pasarela, token_checkout
):
    caso = CrearIntentoPagoUseCase(repositorio, pasarela)
    command = CrearIntentoPagoCommand(id_pedido=pago.id_pedido, token_checkout=token_checkout)
    primero = await caso.execute(command)
    segundo = await caso.execute(command)
    assert primero.client_secret == segundo.client_secret
    assert primero.monto == "249.90"
    pasarela.crear_intento.assert_awaited_once()
    pasarela.obtener_intento.assert_awaited_once_with("pi_test")


@pytest.mark.parametrize("motivo", ["token", "expirado", "no_existe"])
async def test_checkout_inaccesible_no_contacta_stripe(
    motivo, pago, repositorio, pasarela, token_checkout
):
    if motivo == "token":
        token_checkout = "no-autorizado" * 4
    elif motivo == "expirado":
        repositorio.obtener_por_pedido.return_value.expira_en = datetime.now(UTC) - timedelta(
            seconds=1
        )
    else:
        repositorio.obtener_por_pedido.return_value.pago = None
    with pytest.raises(PagoNoEncontradoError):
        await CrearIntentoPagoUseCase(repositorio, pasarela).execute(
            CrearIntentoPagoCommand(id_pedido=pago.id_pedido, token_checkout=token_checkout)
        )
    pasarela.crear_intento.assert_not_called()
    pasarela.obtener_intento.assert_not_called()


async def test_no_recrea_despues_de_ventana_idempotencia(
    pago, repositorio, pasarela, token_checkout
):
    pago.creado_en = datetime.now(UTC) - timedelta(hours=24)
    with pytest.raises(PagoConflictoError):
        await CrearIntentoPagoUseCase(repositorio, pasarela).execute(
            CrearIntentoPagoCommand(id_pedido=pago.id_pedido, token_checkout=token_checkout)
        )
    pasarela.crear_intento.assert_not_called()


@pytest.mark.parametrize("estado", [EstadoPago.EXITOSO, EstadoPago.CANCELADO])
async def test_pago_terminal_no_crea_otro_intento(
    estado, pago, repositorio, pasarela, token_checkout
):
    pago.estado = estado
    with pytest.raises(PagoConflictoError):
        await CrearIntentoPagoUseCase(repositorio, pasarela).execute(
            CrearIntentoPagoCommand(id_pedido=pago.id_pedido, token_checkout=token_checkout)
        )
    pasarela.crear_intento.assert_not_called()


async def test_webhook_duplicado_no_vuelve_a_procesar(repositorio, pasarela):
    repositorio.existe_evento.return_value.existe = True
    resultado = await ProcesarWebhookPagoUseCase(repositorio, pasarela).execute(
        ProcesarWebhookPagoCommand(payload=b"{}", firma="test")
    )
    assert resultado.duplicado
    repositorio.guardar.assert_not_called()
    pasarela.obtener_intento.assert_not_called()


async def test_evento_viejo_usa_estado_actual_y_no_revierte_exito(pago, repositorio, pasarela):
    pasarela.validar_webhook.return_value.tipo = "payment_intent.payment_failed"
    pasarela.obtener_intento.return_value.estado = EstadoPago.EXITOSO
    caso = ProcesarWebhookPagoUseCase(repositorio, pasarela)
    command = ProcesarWebhookPagoCommand(payload=b"{}", firma="test")
    await caso.execute(command)
    assert pago.estado == EstadoPago.EXITOSO
    pasarela.obtener_intento.return_value.estado = EstadoPago.PROCESANDO
    await caso.execute(command)
    assert pago.estado == EstadoPago.EXITOSO


@pytest.mark.parametrize("campo,valor", [("monto_centavos", 1), ("moneda", "usd")])
async def test_webhook_no_acepta_importe_o_moneda_distintos(campo, valor, repositorio, pasarela):
    setattr(pasarela.obtener_intento.return_value, campo, valor)
    with pytest.raises(PagoConflictoError):
        await ProcesarWebhookPagoUseCase(repositorio, pasarela).execute(
            ProcesarWebhookPagoCommand(payload=b"{}", firma="test")
        )
    repositorio.guardar.assert_not_called()
    repositorio.registrar_evento.assert_not_called()


async def test_webhook_temprano_pide_reintento(repositorio, pasarela):
    repositorio.obtener_por_id.return_value.pago = None
    with pytest.raises(PasarelaNoDisponibleError):
        await ProcesarWebhookPagoUseCase(repositorio, pasarela).execute(
            ProcesarWebhookPagoCommand(payload=b"{}", firma="test")
        )


@pytest.mark.parametrize("monto", ["0", "-1", "1.001", "NaN", "1000000"])
def test_rechaza_importes_invalidos(monto, pago):
    with pytest.raises(ValueError):
        Pago(
            id=pago.id,
            id_pedido=pago.id_pedido,
            monto=Decimal(monto),
            moneda="mxn",
            estado=EstadoPago.PENDIENTE,
            creado_en=pago.creado_en,
            id_transaccion_externa=None,
        )
