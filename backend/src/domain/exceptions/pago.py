class PagoError(Exception):
    """Error conocido del flujo de pagos, independiente del transporte."""


class PagoNoEncontradoError(PagoError):
    pass


class PagoConflictoError(PagoError):
    pass


class WebhookInvalidoError(PagoError):
    pass


class PasarelaNoDisponibleError(PagoError):
    pass
