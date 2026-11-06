# api/app/middleware.py
"""Middleware ASGI que limita los bytes del cuerpo antes de parsearlo."""
import json
from typing import Any, Awaitable, Callable, MutableMapping

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class BodyTooLarge(Exception):
    """Se lanza cuando el cuerpo recibido supera el límite."""


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 1) Content-Length declarado: rechazo inmediato.
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    await self._reject(
                        send, 400, "BAD_REQUEST", "Content-Length inválido."
                    )
                    return
                if declared < 0:
                    await self._reject(
                        send, 400, "BAD_REQUEST", "Content-Length inválido."
                    )
                    return
                if declared > self.max_bytes:
                    await self._reject(
                        send,
                        413,
                        "PAYLOAD_TOO_LARGE",
                        "El cuerpo excede el tamaño permitido.",
                    )
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
                    raise BodyTooLarge()
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except BodyTooLarge:
            if not response_started:
                await self._reject(
                    send,
                    413,
                    "PAYLOAD_TOO_LARGE",
                    "El cuerpo excede el tamaño permitido.",
                )

    @staticmethod
    async def _reject(send: Send, status: int, code: str, message: str) -> None:
        body = json.dumps({"code": code, "message": message}).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"connection", b"close"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
