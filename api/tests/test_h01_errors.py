# api/tests/test_h01_errors.py
"""Contrato de errores {"code","message"} (catálogo base de Arquitectura/Backend).

Usa una app FastAPI local con rutas de prueba (el Issue no define endpoints).
"""
import logging

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.errors import register_error_handlers


class Item(BaseModel):
    name: str
    qty: int


def _build_app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/raise/{status}")
    def raise_status(status: int):
        raise HTTPException(status_code=status, detail="detalle-interno-secreto")

    @app.get("/raise-401-header")
    def raise_401_header():
        raise HTTPException(
            status_code=401,
            detail="detalle-interno-secreto",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.get("/boom")
    def boom():
        raise RuntimeError("detalle-secreto /etc/passwd")

    @app.get("/q")
    def q(limit: int = 1):
        return {"limit": limit}

    @app.post("/items")
    def items(item: Item):
        return {"name": item.name, "qty": item.qty}

    return app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Aislamiento: ninguna prueba debe depender ni escribir en el cwd real.
    monkeypatch.chdir(tmp_path)
    return TestClient(_build_app(), raise_server_exceptions=False)


def _assert_error_shape(resp, status, code):
    assert resp.status_code == status
    body = resp.json()
    assert set(body.keys()) == {"code", "message"}
    assert body["code"] == code
    assert isinstance(body["message"], str) and body["message"]


def test_ruta_ok_no_se_ve_afectada(client):
    resp = client.get("/ok")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@pytest.mark.parametrize(
    "status,code,message",
    [
        (400, "BAD_REQUEST", "Solicitud incorrecta."),
        (401, "UNAUTHENTICATED", "Identidad no proporcionada."),
        (403, "FORBIDDEN", "Acceso denegado."),
        (404, "NOT_FOUND", "Recurso no encontrado."),
        (409, "CONFLICT", "Conflicto con el estado actual del recurso."),
        (413, "PAYLOAD_TOO_LARGE", "El cuerpo excede el tamaño permitido."),
    ],
)
def test_http_exception_catalogo(client, status, code, message):
    resp = client.get(f"/raise/{status}")
    _assert_error_shape(resp, status, code)
    assert resp.json()["message"] == message
    # El detail arbitrario de la excepción no se reenvía al cliente.
    assert "detalle-interno-secreto" not in resp.text


def test_status_sin_mapeo(client):
    resp = client.get("/raise/418")
    _assert_error_shape(resp, 418, "ERROR")
    assert resp.json()["message"] == "Error en la solicitud."
    assert "detalle-interno-secreto" not in resp.text


def test_405_conserva_allow(client):
    resp = client.post("/ok")
    _assert_error_shape(resp, 405, "METHOD_NOT_ALLOWED")
    assert resp.json()["message"] == "Método no permitido."
    assert "GET" in resp.headers.get("allow", "")


def test_401_conserva_www_authenticate(client):
    resp = client.get("/raise-401-header")
    _assert_error_shape(resp, 401, "UNAUTHENTICATED")
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_validacion_422_no_filtra_valor(client):
    resp = client.post(
        "/items", json={"name": "x", "qty": "valor-sensible-no-numerico"}
    )
    _assert_error_shape(resp, 422, "INVALID_REQUEST")
    assert "body.qty" in resp.json()["message"]
    assert "valor-sensible-no-numerico" not in resp.text


def test_validacion_422_campos_faltantes(client):
    resp = client.post("/items", json={})
    _assert_error_shape(resp, 422, "INVALID_REQUEST")
    message = resp.json()["message"]
    assert "body.name" in message
    assert "body.qty" in message


def test_validacion_422_query(client):
    resp = client.get("/q", params={"limit": "abc"})
    _assert_error_shape(resp, 422, "INVALID_REQUEST")
    assert "query.limit" in resp.json()["message"]
    assert "abc" not in resp.json()["message"]


def test_validacion_422_json_invalido(client):
    resp = client.post(
        "/items",
        content="esto-no-es-json",
        headers={"Content-Type": "application/json"},
    )
    _assert_error_shape(resp, 422, "INVALID_REQUEST")
    assert "esto-no-es-json" not in resp.text


def test_500_generico_sin_fuga(client):
    resp = client.get("/boom")
    assert resp.status_code == 500
    assert resp.json() == {
        "code": "INTERNAL_ERROR",
        "message": "Error interno del servidor.",
    }
    assert "Traceback" not in resp.text
    assert "secreto" not in resp.text
    assert "/etc/passwd" not in resp.text


def test_500_log_solo_tipo(client, caplog):
    caplog.set_level(logging.ERROR, logger="app.errors")
    client.get("/boom")
    messages = [r.getMessage() for r in caplog.records if r.name == "app.errors"]
    assert any("RuntimeError" in m for m in messages)
    assert not any("secreto" in m for m in messages)
