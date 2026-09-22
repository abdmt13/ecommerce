"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Elements } from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";
import { LoaderCircle, X } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { mensajePagoEnVerificacion } from "../constants";
import { crearIntentoPago } from "../service";
import type { CheckoutPagoContenidoProps, CheckoutPagoEstado, CheckoutPagoProps } from "../types";
import { CheckoutPagoForm } from "./checkout-pago-form";

const publishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
const stripePromise = publishableKey ? loadStripe(publishableKey).catch(() => null) : null;

function CheckoutPagoContenido({ idPedido, tokenCheckout }: CheckoutPagoContenidoProps) {
  const { resolvedTheme } = useTheme();
  const [estado, setEstado] = useState<CheckoutPagoEstado>({
    intento: null, error: null, isLoading: true,
  });
  const [reintento, setReintento] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let isActivo = true;
    async function prepararPago() {
      try {
        if (!stripePromise || !(await stripePromise)) {
          throw new Error("El formulario de pagos no está disponible.");
        }
        const intento = await crearIntentoPago(
          { id_pedido: idPedido, token_checkout: tokenCheckout }, controller.signal,
        );
        if (isActivo) setEstado({ intento, error: null, isLoading: false });
      } catch (error: unknown) {
        if (isActivo && !controller.signal.aborted) {
          setEstado({
            intento: null,
            error: error instanceof Error ? error.message : "No fue posible preparar el pago.",
            isLoading: false,
          });
        }
      }
    }
    void prepararPago();
    return () => { isActivo = false; controller.abort(); };
  }, [idPedido, tokenCheckout, reintento]);

  if (estado.isLoading) return (
    <p role="status" className="flex items-center gap-2 py-8">
      <LoaderCircle aria-hidden="true" className="size-5 animate-spin" /> Preparando pago seguro…
    </p>
  );
  if (estado.error) return (
    <div className="space-y-4">
      <p role="alert" className="text-red-700 dark:text-red-300">{estado.error}</p>
      <button type="button" className="rounded border px-4 py-2" onClick={() => {
        setEstado({ intento: null, error: null, isLoading: true });
        setReintento((valor) => valor + 1);
      }}>Reintentar</button>
    </div>
  );
  const intento = estado.intento;
  if (!intento) return null;
  if (intento.estado === "exitoso" || intento.estado === "procesando") {
    return <p role="status">{mensajePagoEnVerificacion}</p>;
  }
  if (intento.estado === "cancelado") return <p role="status">Este pago fue cancelado.</p>;
  if (!intento.client_secret) return <p role="alert">No fue posible abrir el formulario de pago.</p>;

  return (
    <Elements
      stripe={stripePromise}
      options={{
        clientSecret: intento.client_secret,
        locale: "es",
        appearance: { theme: resolvedTheme === "dark" ? "night" : "stripe" },
      }}
    >
      <CheckoutPagoForm intento={intento} />
    </Elements>
  );
}

export function CheckoutPagoModal({ idPedido, tokenCheckout, isOpen, onOpenChange }: CheckoutPagoProps) {
  return (
    <Dialog.Root open={isOpen} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/60" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 max-h-[90dvh] w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 overflow-x-auto overflow-y-auto rounded-2xl border border-stone-200 bg-white p-6 text-stone-950 shadow-xl dark:border-stone-800 dark:bg-stone-950 dark:text-stone-50">
          <Dialog.Title className="pr-8 text-xl font-semibold">Completar pago</Dialog.Title>
          <Dialog.Description className="mb-6 mt-2 text-sm text-stone-600 dark:text-stone-400">
            Elige tu método de pago y confirma el importe de tu pedido.
          </Dialog.Description>
          <Dialog.Close aria-label="Cerrar pago" className="absolute right-4 top-4 rounded p-1 focus-visible:outline-2">
            <X aria-hidden="true" className="size-5" />
          </Dialog.Close>
          <CheckoutPagoContenido key={idPedido + tokenCheckout} idPedido={idPedido} tokenCheckout={tokenCheckout} />
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
