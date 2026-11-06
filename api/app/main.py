# api/app/main.py
"""Crea la app FastAPI, registra el middleware y los handlers de error."""
from fastapi import FastAPI

from app.config import MAX_BODY_BYTES
from app.errors import register_error_handlers
from app.middleware import BodySizeLimitMiddleware

app = FastAPI(title="API")

app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_BODY_BYTES)
register_error_handlers(app)

# Los routers del contrato aprobado de wallet-onboarding se registrarían aquí
# con app.include_router(...). Este Issue no define endpoints.
