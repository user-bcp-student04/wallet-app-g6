# api/tests/h01/test_h01_kyc.py
"""Tareas 2.3c y 2.4: KYC con cuatro escenarios, consulta, decisión y documento TEST-."""
import re
from datetime import datetime

import pytest

ESCENARIOS = ["APPROVED", "REJECTED", "PENDING", "EXPIRED"]

DOCUMENTOS_INVALIDOS = [
    ("12345678", "DOCUMENT_NOT_TEST"),
    ("test-123", "DOCUMENT_NOT_TEST"),
    ("Test-123", "DOCUMENT_NOT_TEST"),
    (" TEST-123", "DOCUMENT_NOT_TEST"),
    ("TEST", "DOCUMENT_NOT_TEST"),
    ("TEST-", "VALIDATION_ERROR"),
    ("TEST-a b", "VALIDATION_ERROR"),
    ("TEST-ñandú", "VALIDATION_ERROR"),
    ("TEST-0001\n", "VALIDATION_ERROR"),
    ("TEST-../x", "VALIDATION_ERROR"),
    ("TEST-" + "A" * 60, "VALIDATION_ERROR"),  # 65 caracteres: lo corta el esquema
    ("", "VALIDATION_ERROR"),
]


def _iso(valor: str) -> datetime:
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def _post_kyc(api, cuerpo, owner=None):
    return api.post("/kyc/verifications", owner=owner, json=cuerpo)


# ---------- Positivos ----------
@pytest.mark.parametrize("escenario", ESCENARIOS)
def test_crear_verificacion_por_escenario(api, clock, escenario):
    r = _post_kyc(api, {"document_number": "TEST-0001", "scenario": escenario})
    assert r.status_code == 201
    v = r.json()
    assert set(v) == {"verification_id", "document_number", "scenario", "status", "created_at", "decided_at"}
    assert re.fullmatch(r"[0-9a-f]{32}", v["verification_id"])
    assert v["scenario"] == escenario
    assert v["status"] == escenario
    assert _iso(v["created_at"]) == clock.now
    if escenario == "PENDING":
        assert v["decided_at"] is None
    else:
        assert _iso(v["decided_at"]) == clock.now


def test_consultar_verificacion_creada(api):
    creada = api.crear("PENDING")
    r = api.get(f"/kyc/verifications/{creada['verification_id']}")
    assert r.status_code == 200
    assert r.json() == creada


@pytest.mark.parametrize("decision", ["APPROVED", "REJECTED"])
def test_decidir_pendiente(api, decision):
    creada = api.crear("PENDING")
    r = api.post(f"/kyc/verifications/{creada['verification_id']}/decision", json={"decision": decision})
    assert r.status_code == 200
    assert r.json()["status"] == decision
    assert r.json()["decided_at"] is not None
    consultada = api.get(f"/kyc/verifications/{creada['verification_id']}").json()
    assert consultada["status"] == decision


def test_decidir_registra_decided_at(api, clock):
    creada = api.crear("PENDING")
    clock.advance(minutes=5)
    r = api.post(f"/kyc/verifications/{creada['verification_id']}/decision", json={"decision": "APPROVED"})
    assert (_iso(r.json()["decided_at"]) - _iso(r.json()["created_at"])).total_seconds() == 300


def test_documento_valido_en_el_limite(api):
    doc = "TEST-" + "A" * 59  # 64 caracteres: máximo permitido
    r = _post_kyc(api, {"document_number": doc, "scenario": "APPROVED"})
    assert r.status_code == 201
    assert r.json()["document_number"] == doc


# ---------- Negativos ----------
def test_consultar_verificacion_inexistente_404(api):
    r = api.get("/kyc/verifications/" + "0" * 32)
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"


@pytest.mark.parametrize("escenario", ["APPROVED", "REJECTED", "EXPIRED"])
def test_decidir_sobre_no_pendiente_409(api, escenario):
    creada = api.crear(escenario)
    r = api.post(f"/kyc/verifications/{creada['verification_id']}/decision", json={"decision": "APPROVED"})
    assert r.status_code == 409
    assert r.json()["code"] == "VERIFICATION_NOT_PENDING"
    # El estado no cambió.
    assert api.get(f"/kyc/verifications/{creada['verification_id']}").json()["status"] == escenario


def test_decidir_dos_veces_409(api):
    creada = api.crear("PENDING")
    ruta = f"/kyc/verifications/{creada['verification_id']}/decision"
    assert api.post(ruta, json={"decision": "REJECTED"}).status_code == 200
    segunda = api.post(ruta, json={"decision": "APPROVED"})
    assert segunda.status_code == 409
    assert segunda.json()["code"] == "VERIFICATION_NOT_PENDING"
    assert api.get(f"/kyc/verifications/{creada['verification_id']}").json()["status"] == "REJECTED"


@pytest.mark.parametrize("decision", ["PENDING", "EXPIRED", "aprobar"])
def test_decision_invalida_422(api, decision):
    creada = api.crear("PENDING")
    r = api.post(f"/kyc/verifications/{creada['verification_id']}/decision", json={"decision": decision})
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"
    assert api.get(f"/kyc/verifications/{creada['verification_id']}").json()["status"] == "PENDING"


def test_decidir_inexistente_404(api):
    r = api.post("/kyc/verifications/" + "f" * 32 + "/decision", json={"decision": "APPROVED"})
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"


@pytest.mark.parametrize("documento,codigo", DOCUMENTOS_INVALIDOS)
def test_documento_rechazado(api, documento, codigo):
    r = _post_kyc(api, {"document_number": documento, "scenario": "APPROVED"})
    assert r.status_code == 422
    assert r.json()["code"] == codigo
    assert set(r.json()) == {"code", "message"}


@pytest.mark.parametrize("documento", ["12345678", "test-123", "TEST-a b", "TEST-ñandú", "999-SECRETO-999"])
def test_documento_rechazado_no_se_refleja_ni_toca_disco(api, data_dir, documento):
    r = _post_kyc(api, {"document_number": documento, "scenario": "APPROVED"})
    assert r.status_code == 422
    assert documento not in r.text
    assert not data_dir.exists()  # la validación ocurre antes de abrir archivos


@pytest.mark.parametrize("valor", [123, None, ["TEST-1"], {"a": 1}])
def test_documento_con_tipo_incorrecto(api, valor):
    r = _post_kyc(api, {"document_number": valor, "scenario": "APPROVED"})
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"document_number": "TEST-0001", "scenario": "APPROVE"},
        {"document_number": "TEST-0001", "scenario": "approved"},
        {"document_number": "TEST-0001"},
        {"scenario": "APPROVED"},
        {},
    ],
)
def test_escenario_invalido_o_ausente_422(api, cuerpo):
    r = _post_kyc(api, cuerpo)
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"


def test_campo_desconocido_rechazado(api, data_dir):
    r = _post_kyc(api, {"document_number": "TEST-0001", "scenario": "APPROVED", "owner": "otro"})
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"
    assert "owner" in r.json()["message"]  # solo el nombre del campo, no el valor
    assert "otro" not in r.json()["message"]
    assert not data_dir.exists()


def test_json_malformado_usa_formato_unico(client):
    r = client.post(
        "/kyc/verifications",
        content=b"{no es json",
        headers={"X-Owner-Id": "usuario-1", "Content-Type": "application/json"},
    )
    assert r.status_code == 422
    cuerpo = r.json()
    assert set(cuerpo) == {"code", "message"}
    assert cuerpo["code"] == "VALIDATION_ERROR"
    assert "detail" not in cuerpo


# ---------- Borde ----------
def test_limite_de_verificaciones_por_propietario(api, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "MAX_VERIFICATIONS_PER_OWNER", 3)
    for _ in range(3):
        api.crear("PENDING")
    r = _post_kyc(api, {"document_number": "TEST-0001", "scenario": "PENDING"})
    assert r.status_code == 409
    assert r.json()["code"] == "LIMIT_REACHED"
    assert "reset" in r.json()["message"]
    # No afecta a otro propietario.
    assert _post_kyc(api, {"document_number": "TEST-0001", "scenario": "PENDING"}, owner=api.other).status_code == 201


def test_reset_libera_el_limite(api, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "MAX_VERIFICATIONS_PER_OWNER", 2)
    api.crear("PENDING")
    api.crear("PENDING")
    assert _post_kyc(api, {"document_number": "TEST-0001", "scenario": "PENDING"}).status_code == 409
    assert api.post("/control/reset").status_code == 200
    assert _post_kyc(api, {"document_number": "TEST-0001", "scenario": "PENDING"}).status_code == 201
