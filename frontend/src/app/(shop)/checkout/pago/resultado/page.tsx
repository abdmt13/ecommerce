"use client";

import Link from "next/link";
import { useEffect } from "react";
import { mensajePagoEnVerificacion } from "@/features/pagos/constants";

export default function ResultadoPagoPage() {
  useEffect(() => {
    // Stripe añade un client_secret a la URL de retorno; no conservarlo en el historial.
    window.history.replaceState(null, "", window.location.pathname);
  }, []);

  return (
    <main className="mx-auto max-w-lg space-y-5 px-6 py-16">
      <h1 className="text-2xl font-semibold">Verificación del pago</h1>
      <p role="status">{mensajePagoEnVerificacion}</p>
      <p className="text-stone-600 dark:text-stone-400">
        El regreso a esta página no confirma el cobro. La confirmación del pedido depende de la respuesta de la pasarela.
      </p>
      <Link href="/" className="inline-block rounded-lg border px-4 py-2">Volver a la tienda</Link>
    </main>
  );
}
