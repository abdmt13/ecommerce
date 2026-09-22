import { z } from "zod";
import { pagosEndpoint } from "./constants";
import type { IntentoPagoRequest, IntentoPagoResponse } from "./types";

const intentoPagoSchema = z.object({
  id_pago: z.uuid(),
  client_secret: z.string(),
  estado: z.enum(["pendiente", "procesando", "exitoso", "fallido", "cancelado"]),
  monto: z.string().regex(/^\d+(\.\d{1,2})?$/),
  moneda: z.enum(["mxn", "usd", "eur"]),
});

const errorApiSchema = z.object({ detail: z.string() });

export async function crearIntentoPago(
  datos: IntentoPagoRequest,
  signal?: AbortSignal,
): Promise<IntentoPagoResponse> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) throw new Error("El servicio de pagos no está configurado.");

  let response: Response;
  try {
    response = await fetch(apiUrl.replace(/\/$/, "") + pagosEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos),
      cache: "no-store",
      signal,
    });
  } catch (error: unknown) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new Error("No pudimos conectar con el servicio de pagos. Reintenta.");
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const apiError = errorApiSchema.safeParse(payload);
    throw new Error(
      apiError.success ? apiError.data.detail : "No fue posible preparar el pago.",
    );
  }
  const resultado = intentoPagoSchema.safeParse(payload);
  if (!resultado.success) throw new Error("La respuesta del servicio de pagos no es válida.");
  return resultado.data;
}
