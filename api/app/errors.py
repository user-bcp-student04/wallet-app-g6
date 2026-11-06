# api/app/errors.py
"""Formato único de error {"code", "message"} y handlers de excepciones."""
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")

_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    422: "INVALID_REQUEST",
}


def error_body(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def error_response(
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_body(code, message),
        headers=headers,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code = _CODES.get(exc.status_code, "ERROR")
    # Se usa un texto genérico por estado: no se reenvía detail arbitrario.
    messages: dict[int, str] = {
        400: "Solicitud incorrecta.",
        401: "Identidad no proporcionada.",
        403: "Acceso denegado.",
        404: "Recurso no encontrado.",
        405: "Método no permitido.",
        409: "Conflicto con el estado actual del recurso.",
        413: "El cuerpo excede el tamaño permitido.",
    }
    message = messages.get(exc.status_code, "Error en la solicitud.")
    headers: dict[str, str] | None = dict(exc.headers) if exc.headers else None
    return error_response(exc.status_code, code, message, headers)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Solo ubicaciones de campos: no se devuelven los valores recibidos.
    fields: list[str] = []
    errors: list[Any] = exc.errors()
    for err in errors:
        loc = ".".join(str(p) for p in err.get("loc", ()))
        if loc and loc not in fields:
            fields.append(loc)
    detail = f" Campos: {', '.join(fields)}." if fields else ""
    return error_response(
        422, "INVALID_REQUEST", "Entrada inválida." + detail
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    # Se registra solo el tipo de la excepción, sin trazas en la respuesta.
    logger.error("Error no controlado: %s", type(exc).__name__)
    return error_response(500, "INTERNAL_ERROR", "Error interno del servidor.")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
