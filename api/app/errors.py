# api/app/errors.py
"""Formato único de error {"code","message"} y handlers de excepciones."""
import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")

STATUS_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    429: "RATE_LIMITED",
    503: "SERVICE_UNAVAILABLE",
}

STATUS_MESSAGES: dict[int, str] = {
    400: "La solicitud no es válida. Revise los datos enviados e intente de nuevo.",
    401: "Se requiere autenticación para esta operación.",
    403: "No tiene permisos para esta operación.",
    404: "El recurso solicitado no existe.",
    405: "El método no está permitido para esta ruta.",
    409: "La operación entra en conflicto con el estado actual del recurso.",
    413: "El cuerpo de la solicitud es demasiado grande. Reduzca su tamaño e intente de nuevo.",
    429: "Demasiadas solicitudes. Espere unos segundos e intente de nuevo.",
    503: "El servicio no está disponible. Intente de nuevo más tarde.",
}


class ApiError(Exception):
    """Error de negocio con código HTTP y código de error del contrato."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def error_response(
    status_code: int,
    code: str,
    message: str,
    headers: Optional[dict[str, str]] = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message},
        headers=headers,
    )


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    # Se ignora exc.detail para no filtrar texto interno; el mensaje es fijo por código HTTP.
    code = STATUS_CODES.get(exc.status_code, "HTTP_ERROR")
    message = STATUS_MESSAGES.get(
        exc.status_code, "No se pudo completar la solicitud."
    )
    headers = dict(exc.headers) if exc.headers else None
    return error_response(exc.status_code, code, message, headers)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    fields: set[str] = set()
    for error in exc.errors():
        parts = [str(p) for p in error.get("loc", ()) if p not in ("body", "query", "path")]
        if parts:
            fields.add(".".join(parts))
    detail = f" Campos: {', '.join(sorted(fields))}." if fields else ""
    return error_response(
        400,
        "BAD_REQUEST",
        "La solicitud no es válida. Revise los datos enviados e intente de nuevo." + detail,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # La traza solo va al log del servidor, nunca al cliente.
    logger.error(
        "Error no controlado en %s %s", request.method, request.url.path, exc_info=exc
    )
    return error_response(
        500,
        "INTERNAL_ERROR",
        "Ocurrió un error interno. Intente de nuevo más tarde.",
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, api_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
