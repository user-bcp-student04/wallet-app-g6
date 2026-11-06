# api/tests/test_h01_integration_main.py
"""Integración sobre app.main.app: middleware, handlers y ausencia de escrituras."""
import pytest
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import config
from app.main import app as main_app
from app.middleware import BodySizeLimitMiddleware


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Aísla cwd y HOME: cualquier escritura relativa o en HOME caería en tmp_path.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    return TestClient(main_app, raise_server_exceptions=False)


def test_middleware_registrado():
    assert any(m.cls is BodySizeLimitMiddleware for m in main_app.user_middleware)


def test_handlers_registrados():
    handlers = main_app.exception_handlers
    assert StarletteHTTPException in handlers
    assert RequestValidationError in handlers
    assert Exception in handlers


def test_404_formato_unico(client):
    resp = client.get("/ruta-inexistente")
    assert resp.status_code == 404
    assert resp.json() == {
        "code": "NOT_FOUND",
        "message": "Recurso no encontrado.",
    }


def test_413_antes_del_router(client):
    # El middleware actúa antes del enrutado: una ruta inexistente con cuerpo
    # excesivo debe dar 413 y no 404.
    resp = client.post(
        "/ruta-inexistente", content=b"x" * (config.MAX_BODY_BYTES + 1)
    )
    assert resp.status_code == 413
    assert resp.json() == {
        "code": "PAYLOAD_TOO_LARGE",
        "message": "El cuerpo excede el tamaño permitido.",
    }


def test_sin_escrituras_en_disco(client, tmp_path):
    client.get("/ruta-inexistente")
    client.post("/ruta-inexistente", content=b"x" * (config.MAX_BODY_BYTES + 1))
    client.post("/ruta-inexistente", content=b"{}")
    assert list(tmp_path.iterdir()) == []
