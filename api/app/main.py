# api/app/main.py
"""Crea la app FastAPI, registra middleware, handlers de error y routers."""
from fastapi import FastAPI

from . import config
from .errors import register_error_handlers
from .middleware import BodySizeLimitMiddleware
from .routers import control, health, kyc, scenarios, support, wallets

app = FastAPI(title="Wallet onboarding API", version="0.1.0")

app.add_middleware(BodySizeLimitMiddleware, max_bytes=config.MAX_BODY_BYTES)
register_error_handlers(app)

app.include_router(health.router)
app.include_router(scenarios.router)
app.include_router(kyc.router)
app.include_router(wallets.router)
app.include_router(support.router)
app.include_router(control.router)
