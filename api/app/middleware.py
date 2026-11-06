# api/app/middleware.py
"""Middleware ASGI que limita el tamaño del cuerpo antes de que se parsee."""
from fastapi import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .errors import STATUS_MESSAGES, error_response


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = None
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    declared = -1
                break

        if declared is not None and declared < 0:
            response = error_response(400, "BAD_REQUEST", STATUS_MESSAGES[400])
            await response(scope, receive, send)
            return
        if declared is not None and declared > self.max_bytes:
            response = error_response(413, "PAYLOAD_TOO_LARGE", STATUS_MESSAGES[413])
            await response(scope, receive, send)
            return

        received = 0
        max_bytes = self.max_bytes

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > max_bytes:
                    # HTTPException atraviesa el parseo de FastAPI y sale como 413 con el formato común.
                    raise HTTPException(status_code=413)
            return message

        await self.app(scope, limited_receive, send)
