# api/app/middleware.py
"""Middleware ASGI que limita el tamaño del cuerpo antes de que se parsee."""
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.errors import ApiError, error_body

_TOO_LARGE_MESSAGE = "El cuerpo de la solicitud supera el tamaño permitido. Envía menos datos."


class BodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 1) Comprobación temprana con Content-Length.
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                if not value.isdigit():
                    await self._respond(scope, receive, send, 400, "BAD_REQUEST", "La cabecera Content-Length no es válida.")
                    return
                if int(value) > self.max_bytes:
                    await self._respond(scope, receive, send, 413, "PAYLOAD_TOO_LARGE", _TOO_LARGE_MESSAGE)
                    return
                break

        # 2) Conteo real de bytes (cubre chunked o Content-Length falso).
        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise ApiError(413, "PAYLOAD_TOO_LARGE", _TOO_LARGE_MESSAGE)
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except ApiError as exc:
            if response_started:
                raise
            await self._respond(scope, receive, send, exc.status_code, exc.code, exc.message)

    @staticmethod
    async def _respond(scope: Scope, receive: Receive, send: Send, status: int, code: str, message: str) -> None:
        response = JSONResponse(status_code=status, content=error_body(code, message))
        await response(scope, receive, send)
