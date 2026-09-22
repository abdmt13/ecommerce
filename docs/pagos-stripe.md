# Pagos con Stripe

El módulo implementa Payment Intents y confirmación mediante webhooks. El flujo es
Controller → rmediator Handler → ServiceFactory → PagoService → UseCase → Port → Adapter.
Los handlers no construyen infraestructura. Cada operación tiene su propia AsyncSession
y transacción; la respuesta del handler se devuelve únicamente después del commit.

## Configuración

1. Desde backend, ejecutar `uv sync --locked`.
2. Configurar `DATABASE_URL`, `STRIPE_SECRET_KEY` y `STRIPE_WEBHOOK_SECRET` en
   `backend/.env`. Las claves de prueba y producción deben pertenecer al mismo entorno
   que la clave pública. Las claves secretas nunca se exponen al frontend.
3. Aplicar **una sola vez y explícitamente** el script de la base elegida:
   - PostgreSQL: `backend/src/infrastructure/database/schema/001_pagos.postgresql.sql`.
   - MySQL 8.0.16+: `backend/src/infrastructure/database/schema/001_pagos.mysql.sql`.
     Instalar también `uv sync --locked --extra mysql`.
4. Configurar `NEXT_PUBLIC_API_URL=http://localhost:8000` y
   `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...` en `frontend/.env.local`.
5. Arrancar FastAPI y Next.js siguiendo el README. Cambiar las variables públicas exige
   recompilar el frontend desplegado.

No hay migraciones automáticas, DDL al arrancar ni modificaciones de una base existente
durante la instalación. PostgreSQL usa UUID/TIMESTAMPTZ; MySQL, CHAR(32)/DATETIME en UTC.
Las tablas son `pagos` y `pago_eventos`; el segundo registra eventos confirmados
dentro de la misma transacción que actualiza el pago.

## Contrato con pedidos y autorización de checkout

Esta base del proyecto todavía no implementa pedidos, autenticación ni una pantalla de
checkout. Por eso el módulo no inventa totales ni acepta importes enviados por el navegador.
Para abrir el formulario, un checkout de confianza debe haber persistido un registro
`pagos` con:

- `id`: UUID estable del pago; `id_pedido`: UUID del pedido, único.
- `monto`: total calculado en el servidor, Decimal positivo con dos decimales como máximo.
  El máximo del módulo es 999999.99. Stripe puede aplicar mínimos y restricciones adicionales.
- `moneda`: `mxn`, `usd` o `eur`, en minúsculas. Todas usan dos decimales;
  otras monedas requieren ampliar explícitamente el contrato y su conversión.
- `estado='pendiente'`, `id_transaccion_externa=NULL`, `creado_en` en UTC.
- `token_checkout_hash`: SHA-256 de un token opaco generado en el servidor con
  `secrets.token_urlsafe(32)`. Entregar el token original únicamente al comprador
  autorizado, por HTTPS, después de verificar su acceso al pedido.
- `expira_en`: vencimiento en UTC; se recomienda una hora.

El token es una credencial de acceso al pago: conservarlo solo en memoria del cliente,
no incluirlo en URLs, logs o localStorage. No debe generarlo el navegador.
El endpoint compara su hash en tiempo constante y devuelve el mismo 404 ante pedido
inexistente, token incorrecto o autorización expirada.

La reserva del pago debe hacerse junto con el pedido dentro de la unidad de trabajo del
checkout. El total y la moneda quedan inmutables una vez reservado el pago.
No se agregó una FK hacia pedidos porque esa tabla todavía no existe. Cuando se implemente,
versionar explícitamente esa relación. Tampoco se actualiza inventario ni se marca un
pedido como entregado: esas operaciones pertenecen al futuro módulo de pedidos.

## API

### POST /api/v1/pagos/intento

```json
{
  "id_pedido": "00000000-0000-4000-8000-000000000002",
  "token_checkout": "token-opaco-entregado-por-el-checkout"
}
```

Respuesta 200, con `Cache-Control: no-store`:

```json
{
  "id_pago": "00000000-0000-4000-8000-000000000001",
  "client_secret": "pi_..._secret_...",
  "estado": "pendiente",
  "monto": "249.90",
  "moneda": "mxn"
}
```

Se rechazan propiedades adicionales, incluidos monto y moneda. El primer intento usa
la clave de idempotencia estable `pago:{id_pago}`; solicitudes simultáneas se serializan
mediante bloqueo de fila. Reintentos posteriores recuperan el mismo PaymentIntent.
Si Stripe respondió pero falló el commit, el siguiente intento reutiliza esa clave.

Stripe puede eliminar claves de idempotencia después de 24 horas. Cuando todavía no hay
ID externo persistido, este módulo deja de crear intentos a las 23 horas desde la reserva:
requiere conciliación del operador antes de continuar, evitando un segundo cobro incierto.
No borrar la fila ni asignar otro UUID para forzar un reintento. Buscar el PaymentIntent
por la metadata `id_pago` en Stripe y conciliarlo mediante un webhook verificado.

Errores: 404 checkout no accesible; 409 pago finalizado o discrepancia; 422 entrada
inválida; 503 pasarela no disponible o error SQL. Los errores del SDK no se devuelven
en bruto al navegador.

### POST /api/v1/pagos/webhook

Recibe el JSON original de Stripe y el header `stripe-signature`.
La firma se verifica con `stripe.Webhook.construct_event` antes de consultar persistencia.
La tolerancia temporal del SDK es de 300 segundos; el cuerpo se limita a 1 MiB.

Suscribir estos eventos de PaymentIntent:

- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `payment_intent.processing`
- `payment_intent.canceled`
- `payment_intent.requires_action`

Los eventos ajenos al módulo o de tipos no soportados reciben 200 con
`procesado=false`. Un evento duplicado recibe 200 con `duplicado=true`.
Los pagos desconocidos del módulo reciben 503 para permitir reintentar después del commit
del checkout. Una firma inválida devuelve 400; header ausente, 422.

Para eventos relevantes se consulta el PaymentIntent **actual** en Stripe, bajo el bloqueo
del pago, y se validan ID de pago, pedido, transacción, monto, moneda y entorno.
Así, un evento viejo no puede revertir un éxito. Los estados exitoso y cancelado son
terminales; un fallo de método de pago permite reintentar sobre el mismo intento.
Solo el webhook cambia el estado persistido. La creación del intento y el regreso
del navegador no confirman el pago.

## Formulario reutilizable

`frontend/src/features/pagos/componentes/checkout-pago-modal.tsx` recibe el pedido y
el token emitidos por el checkout. Ejemplo dentro de su futuro componente cliente:

```tsx
<CheckoutPagoModal
  idPedido={pedido.id}
  tokenCheckout={pedido.tokenCheckout}
  isOpen={isPagoOpen}
  onOpenChange={setIsPagoOpen}
/>
```

El modal Radix es responsivo, gestiona foco/teclado y aplica tema claro u oscuro al
PaymentElement. Usa Elements con el clientSecret recibido. El formulario usa
react-hook-form y Zod para confirmar el importe, deshabilita el envío mientras Stripe
no esté listo y previene confirmaciones simultáneas. Los datos de tarjeta permanecen
en los campos alojados de Stripe.

Stripe.confirmPayment usa `redirect: "if_required"`. Los métodos con redirección
regresan a `/checkout/pago/resultado`, que muestra un mensaje de verificación sin
afirmar que el pedido está pagado, y limpia los parámetros secretos de la URL.
No existe todavía consulta visual del estado definitivo del pedido; debe integrarse
cuando se implemente pedidos. El modal queda listo para importarse desde ese checkout.

## Prueba manual en sandbox

```powershell
stripe listen --events payment_intent.succeeded,payment_intent.payment_failed,payment_intent.processing,payment_intent.canceled,payment_intent.requires_action --forward-to localhost:8000/api/v1/pagos/webhook
```

Copiar el `whsec_...` mostrado por Stripe CLI a STRIPE_WEBHOOK_SECRET y reiniciar
FastAPI. Configurar las claves test de la misma cuenta.

Para preparar **únicamente una base de desarrollo**, este ejemplo PostgreSQL crea una
reserva de prueba. El token público de este ejemplo es
`checkout-demo-local-01234567890123456789`; nunca usarlo fuera de desarrollo:

```sql
INSERT INTO pagos (
    id, id_pedido, id_transaccion_externa, monto, moneda, estado, creado_en,
    token_checkout_hash, expira_en
) VALUES (
    '00000000-0000-4000-8000-000000000001',
    '00000000-0000-4000-8000-000000000002',
    NULL, 249.90, 'mxn', 'pendiente', CURRENT_TIMESTAMP,
    encode(sha256(convert_to('checkout-demo-local-01234567890123456789', 'UTF8')), 'hex'),
    CURRENT_TIMESTAMP + INTERVAL '1 hour'
);
```

Pedir el intento con el UUID del pedido y el token de prueba; abrir el modal desde el
checkout con esos mismos datos. Usar las tarjetas de prueba de Stripe y revisar el
registro en pagos tras el webhook. Para probar 3DS, errores o redirecciones, consultar
la documentación de testing de Stripe.

`stripe trigger payment_intent.succeeded` sin las metadata de este módulo genera un
evento ajeno y se ignora intencionalmente. La prueba completa debe confirmar el
PaymentIntent que devolvió este endpoint.

## Verificación automatizada

```powershell
cd backend
uv run ruff check .
uv run ruff format --check .
uv run python -m compileall -q src
uv run pytest -q
```

Las pruebas unitarias usan objetos reales del SDK, HMAC real para firmas y transporte
Stripe simulado. No crean cargos ni requieren credenciales.

Las pruebas de integración aplican el SQL PostgreSQL versionado en un esquema temporal,
usan AsyncSession real y recorren Controller → Mediator → Factory → Service → UseCase
→ Adapter. Requieren una base **exclusiva** llamada pagos_test:

```powershell
docker run --detach --rm --name ecommerce-pagos-test --publish 127.0.0.1:55439:5432 --env POSTGRES_USER=pagos_test --env POSTGRES_PASSWORD=pagos_test --env POSTGRES_DB=pagos_test postgres:17-alpine
$env:TEST_DATABASE_URL = "postgresql+asyncpg://pagos_test:pagos_test@127.0.0.1:55439/pagos_test"
uv run pytest -q
docker stop ecommerce-pagos-test
```

Sin TEST_DATABASE_URL las pruebas de base de datos se omiten. La suite comprueba
autorización, importes, idempotencia, firma manipulada o vencida, concurrencia, duplicados,
rollback y estados terminales. MySQL tiene SQL equivalente pero esta suite de integración
se ejecuta sobre PostgreSQL.

```powershell
cd frontend
npm run lint
npm run typecheck
npm run build
```

## Referencias

- [Stripe: Payment Intents](https://docs.stripe.com/api/payment_intents)
- [Stripe: firmas, duplicados y entrega de webhooks](https://docs.stripe.com/webhooks)
- [Stripe Python: SDK y métodos asíncronos](https://github.com/stripe/stripe-python)
- [React Stripe.js con Elements](https://docs.stripe.com/sdks/stripejs-react.md?ui=elements)
- [Stripe: pruebas de pagos](https://docs.stripe.com/testing)

