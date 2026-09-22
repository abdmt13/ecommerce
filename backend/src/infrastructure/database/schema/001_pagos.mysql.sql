-- Aplicar explícitamente sobre MySQL 8.0.16+ (CHECK habilitado).
-- MySQL hace COMMIT implícito del DDL. Todas las fechas deben escribirse en UTC.
CREATE TABLE pagos (
    id CHAR(32) PRIMARY KEY,
    id_pedido CHAR(32) NOT NULL UNIQUE,
    id_transaccion_externa VARCHAR(255) UNIQUE,
    monto NUMERIC(10, 2) NOT NULL,
    moneda VARCHAR(3) NOT NULL,
    estado VARCHAR(20) NOT NULL,
    creado_en DATETIME(6) NOT NULL,
    token_checkout_hash VARCHAR(64) NOT NULL,
    expira_en DATETIME(6) NOT NULL,
    CONSTRAINT ck_pagos_monto CHECK (monto > 0 AND monto <= 999999.99),
    CONSTRAINT ck_pagos_moneda CHECK (moneda IN ('mxn', 'usd', 'eur')),
    CONSTRAINT ck_pagos_estado CHECK (
        estado IN ('pendiente', 'procesando', 'exitoso', 'fallido', 'cancelado')
    )
) ENGINE=InnoDB;
CREATE TABLE pago_eventos (
    id_evento VARCHAR(255) PRIMARY KEY,
    id_pago CHAR(32) NOT NULL,
    CONSTRAINT fk_pago_eventos_pago FOREIGN KEY (id_pago) REFERENCES pagos(id),
    INDEX ix_pago_eventos_id_pago (id_pago)
) ENGINE=InnoDB;

