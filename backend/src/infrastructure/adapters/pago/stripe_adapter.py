from uuid import UUID

import stripe
from pydantic import ValidationError

from src.domain.entity.pago.pago import EstadoPago, Pago
from src.domain.exceptions.pago import PasarelaNoDisponibleError, WebhookInvalidoError
from src.interfaces.dtos.pago.pago_dto import EventoPasarelaDtoResult, IntentoPasarelaDtoResult
from src.interfaces.ports.pago.pasarela_pago_port import PasarelaPagoPort


class StripePaymentAdapter(PasarelaPagoPort):
    EVENTOS = {
        "payment_intent.succeeded",
        "payment_intent.payment_failed",
        "payment_intent.processing",
        "payment_intent.canceled",
        "payment_intent.requires_action",
    }
    MODULO = "ecommerce_pagos_v1"

    def __init__(self, secret_key: str, webhook_secret: str) -> None:
        if not secret_key or not webhook_secret:
            raise PasarelaNoDisponibleError("Stripe no está configurado.")
        self._webhook_secret = webhook_secret
        self._livemode = secret_key.startswith(("sk_live_", "rk_live_"))
        self._http_client = stripe.HTTPXClient(timeout=15)
        self._client = stripe.StripeClient(
            secret_key, http_client=self._http_client, max_network_retries=2
        )

    async def close(self) -> None:
        await self._http_client.close_async()

    async def crear_intento(self, pago: Pago) -> IntentoPasarelaDtoResult:
        try:
            intento = await self._client.v1.payment_intents.create_async(
                {
                    "amount": pago.monto_centavos,
                    "currency": pago.moneda,
                    "automatic_payment_methods": {"enabled": True},
                    "metadata": {
                        "modulo": self.MODULO,
                        "id_pago": str(pago.id),
                        "id_pedido": str(pago.id_pedido),
                    },
                },
                options={"idempotency_key": f"pago:{pago.id}"},
            )
            return self._mapear_intento(intento)
        except stripe.StripeError as exc:
            raise PasarelaNoDisponibleError("No fue posible iniciar el pago. Reintenta.") from exc

    async def obtener_intento(self, id_transaccion: str) -> IntentoPasarelaDtoResult:
        try:
            intento = await self._client.v1.payment_intents.retrieve_async(id_transaccion)
            return self._mapear_intento(intento)
        except stripe.StripeError as exc:
            raise PasarelaNoDisponibleError("No fue posible consultar el pago. Reintenta.") from exc

    def _mapear_intento(self, intento: stripe.PaymentIntent) -> IntentoPasarelaDtoResult:
        estados = {
            "requires_payment_method": EstadoPago.PENDIENTE,
            "requires_confirmation": EstadoPago.PENDIENTE,
            "requires_action": EstadoPago.PENDIENTE,
            "processing": EstadoPago.PROCESANDO,
            "requires_capture": EstadoPago.PROCESANDO,
            "succeeded": EstadoPago.EXITOSO,
            "canceled": EstadoPago.CANCELADO,
        }
        try:
            if (
                intento.livemode != self._livemode
                or intento.metadata.to_dict().get("modulo") != self.MODULO
            ):
                raise ValueError("Entorno o módulo incorrecto.")
            estado = estados[intento.status]
            if intento.status == "requires_payment_method" and intento.last_payment_error:
                estado = EstadoPago.FALLIDO
            return IntentoPasarelaDtoResult(
                id_transaccion=intento.id,
                client_secret=intento.client_secret or "",
                estado=estado,
                monto_centavos=intento.amount,
                moneda=intento.currency,
                id_pago=UUID(intento.metadata["id_pago"]),
                id_pedido=UUID(intento.metadata["id_pedido"]),
            )
        except (KeyError, ValueError, TypeError, AttributeError, ValidationError) as exc:
            raise PasarelaNoDisponibleError("Respuesta de Stripe no válida.") from exc

    def validar_webhook(self, payload: bytes, firma: str) -> EventoPasarelaDtoResult:
        try:
            evento = stripe.Webhook.construct_event(payload, firma, self._webhook_secret)
            if evento.livemode != self._livemode:
                raise ValueError("El evento corresponde a otro entorno.")
            if evento.type not in self.EVENTOS:
                return EventoPasarelaDtoResult(
                    id_evento=evento.id, tipo=evento.type, es_relevante=False
                )
            objeto = evento.data.object
            if objeto.metadata.to_dict().get("modulo") != self.MODULO:
                return EventoPasarelaDtoResult(
                    id_evento=evento.id, tipo=evento.type, es_relevante=False
                )
            return EventoPasarelaDtoResult(
                id_evento=evento.id,
                tipo=evento.type,
                es_relevante=True,
                id_pago=UUID(objeto.metadata["id_pago"]),
                id_transaccion=objeto.id,
            )
        except (
            stripe.SignatureVerificationError,
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
        ) as exc:
            raise WebhookInvalidoError("Firma o contenido de webhook no válido.") from exc
