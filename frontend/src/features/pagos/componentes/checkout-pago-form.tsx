"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { PaymentElement, useElements, useStripe } from "@stripe/react-stripe-js";
import { LoaderCircle } from "lucide-react";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { v4 as uuidv4 } from "uuid";
import { z } from "zod";
import { mensajePagoEnVerificacion, pagoReturnPath } from "../constants";
import type { CheckoutPagoFields, CheckoutPagoFormProps, EstadoConfirmacion } from "../types";

const pagoSchema = z.object({
  aceptaPago: z.boolean().refine((valor) => valor, "Confirma el importe antes de pagar."),
});

export function CheckoutPagoForm({ intento }: CheckoutPagoFormProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [formId] = useState(() => uuidv4());
  const [error, setError] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [estadoConfirmacion, setEstadoConfirmacion] = useState<EstadoConfirmacion>(null);
  const isConfirming = useRef(false);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<CheckoutPagoFields>({
    resolver: zodResolver(pagoSchema),
    defaultValues: { aceptaPago: false },
  });
  const isFinalizado = estadoConfirmacion === "succeeded" || estadoConfirmacion === "processing";
  const importe = new Intl.NumberFormat("es-MX", {
    style: "currency", currency: intento.moneda.toUpperCase(),
  }).format(Number(intento.monto));

  async function confirmarPago() {
    if (!stripe || !elements || isConfirming.current || isFinalizado) return;
    isConfirming.current = true;
    setError(null);
    try {
      const resultado = await stripe.confirmPayment({
        elements,
        confirmParams: { return_url: new URL(pagoReturnPath, window.location.origin).href },
        redirect: "if_required",
      });
      if (resultado.error) {
        setError(resultado.error.message ?? "No fue posible confirmar el pago.");
        return;
      }
      setEstadoConfirmacion(resultado.paymentIntent.status);
      if (!["succeeded", "processing"].includes(resultado.paymentIntent.status)) {
        setError("El pago todavía requiere atención. Revisa el método e inténtalo nuevamente.");
      }
    } catch {
      setError("No pudimos obtener la confirmación. Reintenta con este mismo pedido.");
    } finally {
      isConfirming.current = false;
    }
  }

  if (isFinalizado) {
    return <p role="status" className="rounded-lg bg-emerald-50 p-4 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-100">{mensajePagoEnVerificacion}</p>;
  }

  return (
    <form onSubmit={(event) => { void handleSubmit(confirmarPago)(event); }} className="space-y-5" aria-busy={isSubmitting}>
      <p className="text-lg font-semibold">Total: {importe}</p>
      <PaymentElement
        onReady={() => setIsReady(true)}
        onChange={(event) => setIsComplete(event.complete)}
        onLoadError={() => setError("No pudimos cargar el formulario seguro. Cierra y vuelve a abrir el pago.")}
        options={{ layout: "tabs" }}
      />
      <label htmlFor={formId} className="flex items-start gap-3 text-sm">
        <input
          id={formId}
          type="checkbox"
          {...register("aceptaPago")}
          disabled={isSubmitting}
          aria-describedby={errors.aceptaPago ? `${formId}-error` : undefined}
          className="mt-1 size-4"
        />
        Autorizo el pago de {importe}.
      </label>
      {errors.aceptaPago && <p id={`${formId}-error`} role="alert" className="text-sm text-red-700 dark:text-red-300">{errors.aceptaPago.message}</p>}
      {error && <p role="alert" className="text-sm text-red-700 dark:text-red-300">{error}</p>}
      <button
        type="submit"
        disabled={!stripe || !elements || !isReady || !isComplete || isSubmitting}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-stone-900 px-4 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50 dark:bg-stone-100 dark:text-stone-950"
      >
        {isSubmitting && <LoaderCircle aria-hidden="true" className="size-4 animate-spin" />}
        {isSubmitting ? "Confirmando…" : `Pagar ${importe}`}
      </button>
      <p className="text-xs text-stone-600 dark:text-stone-400">Stripe procesa tus datos de pago de forma segura.</p>
    </form>
  );
}
