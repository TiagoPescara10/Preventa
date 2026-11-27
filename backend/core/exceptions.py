"""Business-rule errors and the DRF exception handler that renders them.

Services raise ReglaDeNegocioError; the handler turns it into:
    400 / 409  {"codigo": "RN-xx", "detalle": "..."}
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class ReglaDeNegocioError(Exception):
    """Raised by services.py when a business rule (RN-xx) is violated.

    Use status 400 for invalid data and 409 for conflicts with the current state.
    """

    def __init__(self, codigo: str, detalle: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        if status_code not in (status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT):
            raise ValueError("ReglaDeNegocioError only supports 400 or 409")
        super().__init__(detalle)
        self.codigo = codigo
        self.detalle = detalle
        self.status_code = status_code


class ConflictoError(ReglaDeNegocioError):
    """Shortcut for a 409 Conflict."""

    def __init__(self, codigo: str, detalle: str):
        super().__init__(codigo, detalle, status.HTTP_409_CONFLICT)


def exception_handler(exc, context):
    if isinstance(exc, ReglaDeNegocioError):
        return Response({"codigo": exc.codigo, "detalle": exc.detalle}, status=exc.status_code)
    return drf_exception_handler(exc, context)
