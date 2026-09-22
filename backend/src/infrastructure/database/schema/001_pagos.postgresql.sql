-- Aplicar explícitamente sobre PostgreSQL. No se ejecuta durante el arranque.
BEGIN;
CREATE TABLE pagos (
    id UUID PRIMARY KEY,
    id_pedido UUID NOT NULL UNIQUE,
    id_transaccion_externa VARCHAR(255) UNIQUE,
    monto NUMERIC(10, 2) NOT NULL,
    moneda VARCHAR(3) NOT NULL,
    estado VARCHAR(20) NOT NULL,
    creado_en TIMESTAMPTZ NOT NULL,
    token_checkout_hash VARCHAR(64) NOT NULL,
    expira_en TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_pagos_monto CHECK (monto > 0 AND monto <= 999999.99),
    CONSTRAINT ck_pagos_moneda CHECK (moneda IN ('mxn', 'usd', 'eur')),
    CONSTRAINT ck_pagos_estado CHECK (
        estado IN ('pendiente', 'procesando', 'exitoso', 'fallido', 'cancelado')
    )
);
CREATE TABLE pago_eventos (
    id_evento VARCHAR(255) PRIMARY KEY,
    id_pago UUID NOT NULL REFERENCES pagos(id)
);
CREATE INDEX ix_pago_eventos_id_pago ON pago_eventos(id_pago);
COMMIT;

