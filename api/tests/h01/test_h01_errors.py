# api/tests/h01/test_h01_errors.py
"""Formato único de error {"code","message"} y mensajes accionables (CA-2.3d, 2.7b)."""
import re

import pytest

VERBOS_ACCION = re.compile(r"\b(Completa|Crea|Espera|Usa|Registra|Corrige|Envía|Ingresa|Revisa)\b")

CASOS = [
    # (método, ruta, json, con_identidad, status, code)
    ("GET", "/onboarding", None, False, 401, "UNAUTHENTICATED"),
    ("GET", "/kyc/verifications/nada", None, True, 404, "NOT_FOUND"),
    ("POST", "/onboarding/steps/foo", None, True, 404, "NOT_FOUND"),
    ("DELETE", "/onboarding", None, True, 405, "METHOD_NOT_ALLOWED"),
    ("POST", "/onboarding/steps/kyc", None, True, 409, "STEP_BLOCKED"),
    ("POST", "/kyc/verifications", {"document_number": "12345678", "scenario": "APPROVED"}, True, 422, "DOCUMENT_NOT_TEST"),
    ("POST", "/kyc/verifications", {"document_number": "TEST-1", "scenario": "NADA"}, True, 422, "VALIDATION_ERROR"),
    ("POST", "/onboarding/steps/registro", None, True, 422, "VALIDATION_ERROR"),
]


@pytest.mark.parametrize("metodo,ruta,cuerpo,con_id,status,code", CASOS)
def test_todos_los_errores_usan_solo_code_y_message(client, metodo, ruta, cuerpo, con_id, status, code):
    cabeceras = {"X-Owner-Id": "usuario-1"} if con_id else {}
    r = client.request(metodo, ruta, json=cuerpo, headers=cabeceras)
    assert r.status_code == status
    b = r.json()
    assert set(b) == {"code", "message"}
    assert b["code"] == code
    assert isinstance(b["message"], str) and b["message"].strip()
    assert "detail" not in b


@pytest.mark.parametrize("escenario", [None, "PENDING", "REJECTED", "EXPIRED"])
def test_mensajes_de_bloqueo_indican_la_accion(api, escenario):
    api.registrar()
    if escenario:
        api.crear(escenario)
    r = api.post("/onboarding/steps/kyc")
    assert r.status_code == 409
    assert VERBOS_ACCION.search(r.json()["message"]), r.json()["message"]


def test_mensaje_de_paso_previo_indica_la_accion(api):
    for paso in ("kyc", "activacion"):
        r = api.post(f"/onboarding/steps/{paso}")
        assert VERBOS_ACCION.search(r.json()["message"]), r.json()["message"]


def test_mensaje_de_documento_indica_el_prefijo(api):
    r = api.post("/kyc/verifications", json={"document_number": "12345678", "scenario": "APPROVED"})
    assert "TEST-" in r.json()["message"]
