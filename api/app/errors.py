# api/app/errors.py
"""Excepción de dominio y handlers que unifican el formato {"code","message"}."""
import logging
import re
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")

_HTTP_ERRORS: dict[int, tuple[str, str]] = {
    400: ("BAD_REQUEST", "La solicitud no es válida."),
    401: ("UNAUTHENTICATED", "No se pudo identificar al usuario."),
    403: ("FORBIDDEN", "No tienes permisos para realizar esta acción."),
    404: ("NOT_FOUND", "El recurso solicitado no existe."),
    405: ("METHOD_NOT_ALLOWED", "El método no está permitido para esta ruta."),
    409: ("CONFLICT", "La solicitud entra en conflicto con el estado actual."),
    413: ("PAYLOAD_TOO_LARGE", "El cuerpo de la solicitud supera el tamaño permitido."),
    422: ("VALIDATION_ERROR", "La solicitud no es válida."),
}

_UNSAFE_NAME_CHARS = re.compile(r"[^A-Za-z0-9_.\-]")


class ApiError(HTTPException):
    """Error de negocio con código estable. Hereda de HTTPException para que FastAPI lo propague tal cual."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message


def error_body(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _field_names(exc: RequestValidationError) -> list[str]:
    names: list[str] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        parts = [str(p) for p in loc[1:] if not isinstance(p, int)]
        if not parts:
            continue
        name = _UNSAFE_NAME_CHARS.sub("?", ".".join(parts))[:64]
        if name not in names:
            names.append(name)
    return names[:5]


async def _api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message),
        headers=exc.headers,
    )


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code, message = _HTTP_ERRORS.get(exc.status_code, ("HTTP_ERROR", "No se pudo procesar la solicitud."))
    headers: Optional[dict[str, str]] = getattr(exc, "headers", None)
    return JSONResponse(status_code=exc.status_code, content=error_body(code, message), headers=headers)


async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    names = _field_names(exc)
    if names:
        message = f"La solicitud no es válida. Corrige los campos: {', '.join(names)}."
    else:
        message = "El cuerpo de la solicitud no es válido o está vacío. Envía un JSON conforme al contrato."
    return JSONResponse(status_code=422, content=error_body("VALIDATION_ERROR", message))


async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    # La traza queda solo en el log del servidor; el cliente recibe un mensaje genérico.
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=error_body("INTERNAL_ERROR", "Ocurrió un error interno. Inténtalo de nuevo más tarde."),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(Exception, _unhandled_handler)
