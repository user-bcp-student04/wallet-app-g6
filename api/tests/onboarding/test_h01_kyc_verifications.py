# api/tests/onboarding/test_h01_kyc_verifications.py
"""3.3 POST /kyc/verifications y 3.4 GET /kyc/verifications/{id}."""
import json
import re
from datetime import datetime

import pytest

from app import config

ID_VER = re.compile(r"^ver_[0-9a-f]{16}$")
ID_WLT = re.compile(r"^wlt_[0-9a-f]{16}$")
CAMPOS = {"id", "status", "decisionStatus", "walletId", "createdAt"}
JSON_HEADERS = {"Content-Type": "application/json"}

ESPERADO = {
    "APPROVED": ("NOT_REQUIRED", True),
    "REJECTED": ("NOT_REQUIRED", False),
    "MANUAL_REVIEW": ("PENDING", False),
}


def _cuerpo_de_tamano(n):
    """JSON compacto de exactamente n bytes (campo 'relleno' desconocido, ignorado por el API)."""
    base = {"documentNumber": "TEST-1", "scenario": "APPROVED", "relleno": ""}
    vacio = json.dumps(base, separators=(",", ":")).encode()
    cuerpo = dict(base, relleno="a" * (n - len(vacio)))
    texto = json.dumps(cuerpo, separators=(",", ":")).encode()
    assert len(texto) == n
    return texto


# ---------------- 3.3 positivos ----------------

@pytest.mark.parametrize("scenario", ["APPROVED", "REJECTED", "MANUAL_REVIEW"])
def test_post_crea_verificacion_201(crear, scenario):
    r = crear(scenario)
    assert r.status_code == 201
    cuerpo = r.json()
    assert set(cuerpo) == CAMPOS
    decision_status, con_wallet = ESPERADO[scenario]
    assert cuerpo["status"] == scenario
    assert cuerpo["decisionStatus"] == decision_status
    assert ID_VER.match(cuerpo["id"])
    if con_wallet:
        assert ID_WLT.match(cuerpo["walletId"])
    else:
        assert cuerpo["walletId"] is None
    creado = datetime.fromisoformat(cuerpo["createdAt"].replace("Z", "+00:00"))
    assert creado.tzinfo is not None


def test_post_ids_unicos(crear):
    ids = {crear("MANUAL_REVIEW").json()["id"] for _ in range(20)}
    assert len(ids) == 20


# ---------------- 3.3 503 ----------------

def test_post_kyc_no_disponible_503_sin_efectos(client, crear, store, afirmar_error):
    r = crear("KYC_UNAVAILABLE")
    afirmar_error(r, 503, "KYC_UNAVAILABLE")
    assert store.verifications == {}
    assert store.wallets == {}
    assert store.cases == {}
    assert client.get("/support/cases").json() == []


# ---------------- 3.3 documento sin TEST- (lado servidor, T-9) ----------------

def test_post_documento_sin_prefijo_test_es_aceptado_por_el_servidor_por_defecto(crear):
    assert crear("APPROVED", documento="DOC-123").status_code == 201


def test_post_con_prefijo_obligatorio_activado_rechaza_documento_sin_test(
    crear, monkeypatch, afirmar_error
):
    monkeypatch.setattr(config, "ENFORCE_TEST_DOC_PREFIX", True)
    afirmar_error(crear("APPROVED", documento="DOC-123"), 400, "BAD_REQUEST")


def test_post_con_prefijo_obligatorio_activado_acepta_test(crear, monkeypatch):
    monkeypatch.setattr(config, "ENFORCE_TEST_DOC_PREFIX", True)
    assert crear("APPROVED", documento="TEST-123").status_code == 201


# ---------------- 3.3 negativos ----------------

PAYLOADS_INVALIDOS = [
    pytest.param({}, id="vacio"),
    pytest.param({"scenario": "APPROVED"}, id="sin-documento"),
    pytest.param({"documentNumber": "TEST-1"}, id="sin-scenario"),
    pytest.param({"documentNumber": "TEST-1", "scenario": "INEXISTENTE"}, id="scenario-invalido"),
    pytest.param({"documentNumber": "TEST-1", "scenario": "approved"}, id="scenario-minusculas"),
    pytest.param({"documentNumber": "TEST-1", "scenario": None}, id="scenario-null"),
    pytest.param({"documentNumber": None, "scenario": "APPROVED"}, id="documento-null"),
    pytest.param({"documentNumber": "", "scenario": "APPROVED"}, id="documento-vacio"),
    pytest.param({"documentNumber": "   ", "scenario": "APPROVED"}, id="documento-espacios"),
    pytest.param({"documentNumber": "TEST 001", "scenario": "APPROVED"}, id="documento-con-espacio"),
    pytest.param({"documentNumber": "TEST-1'; DROP TABLE x;--", "scenario": "APPROVED"}, id="documento-inyeccion"),
    pytest.param({"documentNumber": "TEST-ñ", "scenario": "APPROVED"}, id="documento-unicode"),
    pytest.param({"documentNumber": "TEST-1\nX", "scenario": "APPROVED"}, id="documento-salto-de-linea"),
    pytest.param({"documentNumber": 12345, "scenario": "APPROVED"}, id="documento-numerico"),
    pytest.param({"documentNumber": "TEST-" + "A" * 28, "scenario": "APPROVED"}, id="documento-33-caracteres"),
]


@pytest.mark.parametrize("payload", PAYLOADS_INVALIDOS)
def test_post_payload_invalido_400(client, store, afirmar_error, payload):
    r = client.post("/kyc/verifications", json=payload)
    afirmar_error(r, 400, "BAD_REQUEST")
    assert store.verifications == {}


def test_post_json_malformado_400(client, afirmar_error):
    r = client.post("/kyc/verifications", content=b"{no-es-json", headers=JSON_HEADERS)
    afirmar_error(r, 400, "BAD_REQUEST")


def test_post_cuerpo_no_objeto_400(client, afirmar_error):
    afirmar_error(client.post("/kyc/verifications", json=[]), 400, "BAD_REQUEST")


def test_post_mensaje_400_no_repite_valores_enviados(client, afirmar_error):
    r = client.post(
        "/kyc/verifications",
        json={"documentNumber": "SECRETO valor!", "scenario": "APPROVED"},
    )
    cuerpo = afirmar_error(r, 400, "BAD_REQUEST")
    assert "SECRETO" not in cuerpo["message"]
    assert "documentNumber" in cuerpo["message"]


# ---------------- 3.3 bordes ----------------

@pytest.mark.parametrize(
    "documento,esperado",
    [("A", 201), ("TEST-" + "A" * 27, 201), ("TEST-" + "A" * 28, 400)],
    ids=["1-caracter", "32-caracteres", "33-caracteres"],
)
def test_post_longitud_documento_en_el_limite(crear, documento, esperado):
    assert crear("APPROVED", documento=documento).status_code == esperado


def test_post_recorta_espacios_del_documento(crear):
    assert crear("APPROVED", documento="  TEST-1  ").status_code == 201


def test_post_ignora_campos_desconocidos(client):
    r = client.post(
        "/kyc/verifications",
        json={"documentNumber": "TEST-1", "scenario": "APPROVED", "extra": 1},
    )
    assert r.status_code == 201
    assert "extra" not in r.json()


def test_post_cuerpo_en_el_limite_exacto_es_aceptado(client):
    cuerpo = _cuerpo_de_tamano(config.MAX_BODY_BYTES)
    r = client.post("/kyc/verifications", content=cuerpo, headers=JSON_HEADERS)
    assert r.status_code == 201


def test_post_cuerpo_sobre_el_limite_413(client, afirmar_error):
    cuerpo = _cuerpo_de_tamano(config.MAX_BODY_BYTES + 1)
    r = client.post("/kyc/verifications", content=cuerpo, headers=JSON_HEADERS)
    afirmar_error(r, 413, "PAYLOAD_TOO_LARGE")


def test_post_cuerpo_chunked_sobre_el_limite_413(client, afirmar_error):
    # Sin Content-Length (Transfer-Encoding: chunked): el middleware cuenta bytes recibidos (T-11).
    cuerpo = _cuerpo_de_tamano(config.MAX_BODY_BYTES + 1)

    def partes():
        yield cuerpo[:100]
        yield cuerpo[100:]

    r = client.post("/kyc/verifications", content=partes(), headers=JSON_HEADERS)
    afirmar_error(r, 413, "PAYLOAD_TOO_LARGE")


def test_post_content_length_invalido_400(client, afirmar_error):
    # Content-Length no numérico (T-11).
    r = client.post(
        "/kyc/verifications",
        content=b'{"documentNumber":"TEST-1","scenario":"APPROVED"}',
        headers={"Content-Type": "application/json", "Content-Length": "abc"},
    )
    afirmar_error(r, 400, "BAD_REQUEST")


# ---------------- 3.4 GET /kyc/verifications/{id} ----------------

def test_get_verificacion_200(client, crear):
    creada = crear("APPROVED").json()
    r = client.get(f"/kyc/verifications/{creada['id']}")
    assert r.status_code == 200
    assert r.json() == creada


def test_get_verificacion_pendiente_refleja_estado(client, crear):
    creada = crear("MANUAL_REVIEW").json()
    cuerpo = client.get(f"/kyc/verifications/{creada['id']}").json()
    assert cuerpo["status"] == "MANUAL_REVIEW"
    assert cuerpo["decisionStatus"] == "PENDING"


def test_get_verificacion_inexistente_404(client, afirmar_error):
    r = client.get("/kyc/verifications/ver_0000000000000000")
    afirmar_error(r, 404, "NOT_FOUND")


def test_get_verificacion_id_en_el_limite_de_64_es_404(client, afirmar_error):
    r = client.get("/kyc/verifications/" + "a" * 64)
    afirmar_error(r, 404, "NOT_FOUND")


def test_get_verificacion_id_invalido_400(client, afirmar_error):
    afirmar_error(client.get("/kyc/verifications/" + "a" * 65), 400, "BAD_REQUEST")
    afirmar_error(client.get("/kyc/verifications/id.con.punto"), 400, "BAD_REQUEST")


def test_get_verificacion_no_expone_campos_internos(client, crear):
    creada = crear("MANUAL_REVIEW").json()
    texto = client.get(f"/kyc/verifications/{creada['id']}").text
    for interno in ("decision_status", "wallet_id", "created_at", "lock"):
        assert interno not in texto
