import type { PaymentIntent } from "@stripe/stripe-js";

export type EstadoPago = "pendiente" | "procesando" | "exitoso" | "fallido" | "cancelado";

export interface IntentoPagoRequest {
  id_pedido: string;
  token_checkout: string;
}

export interface IntentoPagoResponse {
  id_pago: string;
  client_secret: string;
  estado: EstadoPago;
  monto: string;
  moneda: "mxn" | "usd" | "eur";
}

export interface CheckoutPagoProps {
  idPedido: string;
  tokenCheckout: string;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

export interface CheckoutPagoFormProps {
  intento: IntentoPagoResponse;
}

export interface CheckoutPagoFields {
  aceptaPago: boolean;
}

export type EstadoConfirmacion = PaymentIntent.Status | null;

export interface CheckoutPagoContenidoProps {
  idPedido: string;
  tokenCheckout: string;
}

export interface CheckoutPagoEstado {
  intento: IntentoPagoResponse | null;
  error: string | null;
  isLoading: boolean;
}
