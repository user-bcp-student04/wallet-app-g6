# api/tests/test_h01_body_limit.py
"""Límite de bytes del cuerpo (BodySizeLimitMiddleware).

Dos niveles: TestClient sobre una app local, y llamadas ASGI directas para los
casos que un cliente HTTP real no puede construir (Content-Length inválido).
"""
import asyncio
import json

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.errors import register_error_handlers
from app.middleware import BodySizeLimitMiddleware

MAX = 100
MSG_413 = {
    "code": "PAYLOAD_TOO_LARGE",
    "message": "El cuerpo excede el tamaño permitido.",
}


class Payload(BaseModel):
    text: str


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX)
    register_error_handlers(app)

    @app.post("/raw")
    async def raw(request: Request):
        data = await request.body()
        return {"size": len(data)}

    @app.post("/json")
    async def js(p: Payload):
        return {"len": len(p.text)}

    return app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return TestClient(_build_app(), raise_server_exceptions=False)


# ------------------------- Nivel TestClient -------------------------

def test_cuerpo_exacto_limite_es_aceptado(client):
    resp = client.post("/raw", content=b"x" * MAX)
    assert resp.status_code == 200
    assert resp.json() == {"size": MAX}


def test_cuerpo_vacio_es_aceptado(client):
    resp = client.post("/raw", content=b"")
    assert resp.status_code == 200
    assert resp.json() == {"size": 0}


def test_cuerpo_limite_mas_uno_413(client):
    resp = client.post("/raw", content=b"x" * (MAX + 1))
    assert resp.status_code == 413
    assert resp.json() == MSG_413
    assert resp.headers["content-type"].startswith("application/json")


def test_json_declarado_excede_limite_413(client):
    body = json.dumps({"text": "a" * 200}).encode("utf-8")
    resp = client.post(
        "/json", content=body, headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 413
    assert resp.json() == MSG_413


def test_raw_chunked_excede_limite_413(client):
    def chunks():
        yield b"x" * 60
        yield b"y" * 60

    resp = client.post("/raw", content=chunks())
    assert resp.status_code == 413
    assert resp.json() == MSG_413


def test_json_chunked_excede_limite_413(client):
    # RIESGO A OBSERVAR (hipótesis, no verificada): FastAPI podría envolver la
    # excepción interna del middleware como 400 al parsear un cuerpo JSON.
    # Un 400 aquí es un hallazgo para Backend, no un error de la prueba.
    body = json.dumps({"text": "a" * 200}).encode("utf-8")

    def chunks():
        yield body[:80]
        yield body[80:]

    resp = client.post(
        "/json", content=chunks(), headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 413
    assert resp.json() == MSG_413


# ------------------------- Nivel ASGI directo -------------------------

def _scope(headers=None, scope_type="http"):
    return {
        "type": scope_type,
        "method": "POST",
        "path": "/x",
        "headers": headers or [],
    }


async def _drive(mw, scope, chunks):
    sent = []
    queue = list(chunks)

    async def receive():
        if queue:
            body = queue.pop(0)
            return {"type": "http.request", "body": body, "more_body": bool(queue)}
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    await mw(scope, receive, send)
    return sent


def _reader_app(calls, start_first=False):
    async def app(scope, receive, send):
        calls.append(scope["type"])
        if scope["type"] != "http":
            return
        if start_first:
            await send({"type": "http.response.start", "status": 200, "headers": []})
        more = True
        while more:
            msg = await receive()
            more = msg.get("more_body", False)
        if not start_first:
            await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    return app


def _body_of(sent):
    return json.loads(sent[1]["body"].decode("utf-8"))


@pytest.mark.parametrize("raw", [b"abc", b"-1", b"1.5", b""])
def test_content_length_invalido_400_sin_invocar_app(raw):
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls), max_bytes=MAX)
    sent = asyncio.run(_drive(mw, _scope([(b"content-length", raw)]), []))
    assert sent[0]["status"] == 400
    assert _body_of(sent) == {
        "code": "BAD_REQUEST",
        "message": "Content-Length inválido.",
    }
    assert calls == []


def test_content_length_declarado_mayor_413_sin_invocar_app():
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls), max_bytes=MAX)
    sent = asyncio.run(
        _drive(mw, _scope([(b"content-length", str(MAX + 1).encode())]), [])
    )
    assert sent[0]["status"] == 413
    assert _body_of(sent) == MSG_413
    assert calls == []


def test_rechazo_incluye_content_length_y_connection_close():
    mw = BodySizeLimitMiddleware(_reader_app([]), max_bytes=MAX)
    sent = asyncio.run(
        _drive(mw, _scope([(b"content-length", b"9999")]), [])
    )
    headers = dict(sent[0]["headers"])
    assert headers[b"content-type"] == b"application/json"
    assert headers[b"connection"] == b"close"
    assert int(headers[b"content-length"]) == len(sent[1]["body"])


def test_declarado_igual_al_limite_con_cuerpo_exacto_pasa():
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls), max_bytes=MAX)
    sent = asyncio.run(
        _drive(mw, _scope([(b"content-length", str(MAX).encode())]), [b"x" * MAX])
    )
    assert sent[0]["status"] == 200
    assert calls == ["http"]


def test_acumulado_multiples_chunks_413():
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls), max_bytes=MAX)
    sent = asyncio.run(_drive(mw, _scope(), [b"x" * 60, b"x" * 60]))
    assert sent[0]["status"] == 413
    assert _body_of(sent) == MSG_413
    assert calls == ["http"]  # la app se invocó; el conteo real cortó


def test_content_length_falso_se_detecta_por_conteo_real():
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls), max_bytes=MAX)
    sent = asyncio.run(
        _drive(mw, _scope([(b"content-length", b"5")]), [b"x" * 200])
    )
    assert sent[0]["status"] == 413
    assert _body_of(sent) == MSG_413


def test_respuesta_ya_iniciada_no_se_duplica():
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls, start_first=True), max_bytes=MAX)
    sent = asyncio.run(_drive(mw, _scope(), [b"x" * 200]))
    starts = [m for m in sent if m["type"] == "http.response.start"]
    assert len(starts) == 1
    assert starts[0]["status"] == 200  # no se superpone un 413


def test_scope_no_http_se_delega_sin_tocar():
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls), max_bytes=MAX)
    sent = asyncio.run(_drive(mw, _scope(scope_type="lifespan"), []))
    assert calls == ["lifespan"]
    assert sent == []
