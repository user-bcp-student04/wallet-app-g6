# api/app/main.py
from fastapi import FastAPI

from app import config
from app.errors import register_exception_handlers
from app.middleware import BodyLimitMiddleware
from app.routers import console, kyc, onboarding


def create_app() -> FastAPI:
    application = FastAPI(title="Wallet Onboarding Mock API", version="0.1.0")
    application.add_middleware(BodyLimitMiddleware, max_bytes=config.MAX_BODY_BYTES)
    register_exception_handlers(application)
    application.include_router(console.router)
    application.include_router(kyc.router)
    application.include_router(onboarding.router)
    return application


app = create_app()
