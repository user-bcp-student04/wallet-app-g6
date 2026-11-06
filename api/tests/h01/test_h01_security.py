# api/tests/h01/test_h01_security.py
"""Identidad, aislamiento, fugas y límite de cuerpo (controles de Seguridad visibles; supuesto T-3)."""
import asyncio
import hashlib
import json

import pytest

from app import config
from app.middleware import BodyLimitMiddleware

VALID_KYC = {"document_number": "TEST-0001", "scenario": "APPROVED"}
JSON_CT = {"Content-Type": "application/json"}

RUTAS_CON_IDENTIDAD = [
    ("GET", "/support/cases", None),
    ("POST", "/control/reset", None),
    ("GET", "/onboarding", None),
    ("POST", "/onboarding/steps/registro", {"document_number": "TEST-0001"}),
    ("POST", "/onboarding/steps/kyc", None),
    ("POST", "/kyc/verifications", VALID_KYC),
    ("GET", "/kyc/verifications/abc", None),
    ("POST", "/kyc/verifications/abc/decision", {"decision": "APPROVED"}),
]


# ---------- Identidad ----------
@pytest.mark.parametrize("metodo,ruta,cuerpo", RUTAS_CON_IDENTIDAD)
def test_endpoints_con_identidad_responden_401_sin_cabecera(client, data_dir, metodo, ruta, cuerpo):
    r = client.request(metodo, ruta, json=cuerpo)
    assert r.status_code == 401
    assert r.json() == {"code": "UNAUTHENTICATED", "message": "No se pudo identificar al usuario."}
    assert not data_dir.exists()


@pytest.mark.parametrize("valor", ["", "a b", "a/b", "../x", "a;b", "a" * 129])
def test_cabecera_invalida_responde_401(client, valor):
    r = client.get("/onboarding", headers={"X-Owner-Id": valor})
    assert r.status_code == 401
    assert r.json()["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize("owner", ["a" * 128, "A.b_c-9"])
def test_identificador_en_el_limite_es_valido(client, owner):
    assert client.get("/onboarding", headers={"X-Owner-Id": owner}).status_code == 200


def test_owner_en_cuerpo_se_rechaza(api, data_dir):
    r = api.post("/kyc/verifications", json={**VALID_KYC, "owner": "usuario-2"})
    assert r.status_code == 422
    assert not data_dir.exists()


def test_owner_en_query_se_ignora(api):
    api.registrar()
    propio = api.get("/onboarding?owner=usuario-2&owner_id=usuario-2").json()
    assert propio["current_step"] == "kyc"  # sigue siendo el estado de usuario-1
    assert api.get("/onboarding", owner=api.other).json()["wallet_status"] == "NOT_STARTED"


# ---------- Aislamiento y rutas hostiles ----------
def test_aislamiento_entre_propietarios_en_kyc(api):
    v = api.crear("PENDING", owner=api.owner)
    assert api.get(f"/kyc/verifications/{v['verification_id']}", owner=api.other).status_code == 404
    r = api.post(
        f"/kyc/verifications/{v['verification_id']}/decision", owner=api.other, json={"decision": "APPROVED"}
    )
    assert r.status_code == 404
    assert api.get(f"/kyc/verifications/{v['verification_id']}", owner=api.owner).json()["status"] == "PENDING"


@pytest.mark.parametrize("vid", ["....", "%00", "con%20espacios", "x" * 64, "%2e%2e"])
def test_identificadores_de_ruta_no_tocan_el_disco(api, data_dir, vid):
    r = api.get(f"/kyc/verifications/{vid}")
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"
    assert not data_dir.exists()


def test_verification_id_demasiado_largo_422(api):
    r = api.get("/kyc/verifications/" + "x" * 65)
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("paso", ["kyc2", "REGISTRO", "Kyc", "registro "])
def test_step_id_fuera_de_contrato(api, data_dir, paso):
    r = api.post(f"/onboarding/steps/{paso}")
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"
    assert not data_dir.exists()


def test_step_id_demasiado_largo_422(api):
    r = api.post("/onboarding/steps/" + "x" * 33)
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"


def test_directorio_usa_solo_el_hash(api, data_dir):
    api.completar_flujo()
    digest = hashlib.sha256(api.owner.encode("utf-8")).hexdigest()
    assert sorted(p.name for p in data_dir.rglob("*")) == sorted([digest, "state.json"])
    assert all(api.owner not in str(p) for p in data_dir.rglob("*"))


# ---------- Fugas ----------
def test_respuestas_no_exponen_owner_ni_hash(api):
    owner = "propietario-secreto-777"
    digest = hashlib.sha256(owner.encode("utf-8")).hexdigest()
    textos = []

    def reg(r):
        textos.append(r.text + json.dumps(dict(r.headers)))
        return r

    reg(api.post("/onboarding/steps/registro", owner=owner, json={"document_number": "TEST-0001"}))
    v = reg(api.post("/kyc/verifications", owner=owner, json=VALID_KYC)).json()
    reg(api.get(f"/kyc/verifications/{v['verification_id']}", owner=owner))
    reg(api.get("/support/cases", owner=owner))
    reg(api.get("/onboarding", owner=owner))
    reg(api.post(f"/kyc/verifications/{v['verification_id']}/decision", owner=owner, json={"decision": "APPROVED"}))  # 409
    reg(api.post("/onboarding/steps/activacion", owner=owner))  # 409
    reg(api.post("/control/reset", owner=owner))
    assert len(textos) == 8
    for t in textos:
        assert owner not in t
        assert digest not in t


# ---------- Límite de cuerpo (413) ----------
_BASE = '{"document_number":"TEST-%s","scenario":"APPROVED"}'


def _cuerpo_con_sufijo(n: int) -> bytes:
    return (_BASE % ("A" * n)).encode("utf-8")


def test_valor_por_defecto_del_limite():
    # T-8: requiere MAX_BODY_BYTES sin definir en el entorno.
    assert config.MAX_BODY_BYTES == 16384


def test_cuerpo_exacto_al_limite_pasa_y_un_byte_mas_se_rechaza(monkeypatch, build_client, state_file, leer_estado):
    limite = len(_cuerpo_con_sufijo(20))
    monkeypatch.setattr(config, "MAX_BODY_BYTES", limite)
    cliente = build_client()
    cabeceras = {"X-Owner-Id": "usuario-1", **JSON_CT}
    ok = cliente.post("/kyc/verifications", content=_cuerpo_con_sufijo(20), headers=cabeceras)
    assert ok.status_code == 201
    grande = cliente.post("/kyc/verifications", content=_cuerpo_con_sufijo(21), headers=cabeceras)
    assert grande.status_code == 413
    assert grande.json()["code"] == "PAYLOAD_TOO_LARGE"
    assert set(grande.json()) == {"code", "message"}
    assert len(leer_estado("usuario-1")["verifications"]) == 1  # el rechazado no se guardó


def test_limite_por_defecto_en_el_borde(client):
    limite = config.MAX_BODY_BYTES
    cabeceras = {"X-Owner-Id": "usuario-1", **JSON_CT}
    en_limite = client.post("/kyc/verifications", content=b"x" * limite, headers=cabeceras)
    assert en_limite.status_code == 422  # pasó el límite; falla por no ser JSON
    assert en_limite.json()["code"] == "VALIDATION_ERROR"
    excedido = client.post("/kyc/verifications", content=b"x" * (limite + 1), headers=cabeceras)
    assert excedido.status_code == 413
    assert excedido.json()["code"] == "PAYLOAD_TOO_LARGE"


def test_413_sin_identidad(client, data_dir):
    r = client.post("/kyc/verifications", content=b"x" * (config.MAX_BODY_BYTES + 1), headers=JSON_CT)
    assert r.status_code == 413  # el límite se aplica antes que la identidad
    assert r.json()["code"] == "PAYLOAD_TOO_LARGE"
    assert not data_dir.exists()


def test_413_con_cuerpo_por_trozos(client):
    limite = config.MAX_BODY_BYTES

    def trozos():
        yield b"{"
        yield b"a" * limite

    r = client.post("/kyc/verifications", content=trozos(), headers={"X-Owner-Id": "usuario-1", **JSON_CT})
    assert r.status_code == 413
    assert r.json()["code"] == "PAYLOAD_TOO_LARGE"


# ---------- Middleware ASGI directo (determinista; T-12) ----------
def _llamar(max_bytes, headers, trozos):
    llamadas, enviados = [], []
    cola = [{"type": "http.request", "body": t, "more_body": i < len(trozos) - 1} for i, t in enumerate(trozos)]

    async def recibir():
        return cola.pop(0)

    async def enviar(mensaje):
        enviados.append(mensaje)

    async def interna(scope, receive, send):
        llamadas.append(True)
        mas = True
        while mas:
            mas = (await receive()).get("more_body", False)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"{}"})

    scope = {"type": "http", "method": "POST", "path": "/", "headers": headers}
    asyncio.run(BodyLimitMiddleware(interna, max_bytes)(scope, recibir, enviar))
    estado = next(m["status"] for m in enviados if m["type"] == "http.response.start")
    cuerpo = b"".join(m.get("body", b"") for m in enviados if m["type"] == "http.response.body")
    return estado, json.loads(cuerpo), llamadas


@pytest.mark.parametrize("valor", [b"abc", b"-5", b"1.5", b"10 "])
def test_middleware_content_length_no_numerico(valor):
    estado, cuerpo, llamadas = _llamar(10, [(b"content-length", valor)], [b"x"])
    assert estado == 400
    assert cuerpo["code"] == "BAD_REQUEST"
    assert llamadas == []


def test_middleware_content_length_en_el_limite():
    estado, _, llamadas = _llamar(10, [(b"content-length", b"10")], [b"x" * 10])
    assert estado == 200
    assert llamadas == [True]


def test_413_no_llama_a_la_aplicacion():
    estado, cuerpo, llamadas = _llamar(10, [(b"content-length", b"11")], [b"x" * 11])
    assert estado == 413
    assert cuerpo["code"] == "PAYLOAD_TOO_LARGE"
    assert llamadas == []


def test_middleware_cuenta_bytes_sin_content_length():
    estado, cuerpo, _ = _llamar(10, [], [b"x" * 6, b"x" * 6])
    assert estado == 413
    assert cuerpo["code"] == "PAYLOAD_TOO_LARGE"


def test_middleware_cuerpo_por_trozos_dentro_del_limite():
    estado, _, llamadas = _llamar(10, [], [b"x" * 5, b"x" * 5])
    assert estado == 200
    assert llamadas == [True]
