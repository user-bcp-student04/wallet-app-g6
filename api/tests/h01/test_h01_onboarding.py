# api/tests/h01/test_h01_onboarding.py
"""Tareas 2.3 y 2.6b (lado API): estado de wallet, pasos con bloqueo e integración."""
import pytest


def _estados(r):
    return [s["status"] for s in r["steps"]]


# ---------- Estado ----------
def test_estado_inicial_de_un_propietario_nuevo(api, data_dir):
    r = api.get("/onboarding")
    assert r.status_code == 200
    e = r.json()
    assert set(e) == {"wallet_status", "current_step", "steps", "low_amount_payments_enabled", "duration_seconds"}
    assert e["wallet_status"] == "NOT_STARTED"
    assert e["current_step"] == "registro"
    assert [s["id"] for s in e["steps"]] == ["registro", "kyc", "activacion"]
    assert [s["order"] for s in e["steps"]] == [1, 2, 3]
    assert _estados(e) == ["CURRENT", "LOCKED", "LOCKED"]
    assert e["low_amount_payments_enabled"] is False
    assert e["duration_seconds"] is None
    assert not data_dir.exists()  # leer no escribe


def test_estado_es_estable_entre_lecturas(api):
    api.registrar()
    primero = api.get("/onboarding").json()
    assert api.get("/onboarding").json() == primero


@pytest.mark.parametrize(
    "escenario,wallet",
    [("PENDING", "KYC_PENDING"), ("REJECTED", "KYC_FAILED"), ("EXPIRED", "KYC_FAILED"), ("APPROVED", "IN_PROGRESS")],
)
def test_wallet_status_segun_ultima_verificacion(api, escenario, wallet):
    api.registrar()
    api.crear(escenario)
    e = api.get("/onboarding").json()
    assert e["wallet_status"] == wallet
    assert e["low_amount_payments_enabled"] is False


# ---------- Bloqueo ----------
@pytest.mark.parametrize("paso,mencionado", [("kyc", "registro"), ("activacion", "kyc")])
def test_paso_bloqueado_sin_requisito_previo(api, data_dir, paso, mencionado):
    r = api.post(f"/onboarding/steps/{paso}")
    assert r.status_code == 409
    assert r.json()["code"] == "STEP_BLOCKED"
    assert mencionado in r.json()["message"]
    assert not data_dir.exists()  # un paso bloqueado no escribe nada


@pytest.mark.parametrize(
    "escenario,fragmento",
    [
        (None, "POST /kyc/verifications"),
        ("PENDING", "pendiente"),
        ("REJECTED", "no fue aprobada"),
        ("EXPIRED", "no fue aprobada"),
    ],
)
def test_kyc_bloqueado_segun_verificacion(api, leer_estado, escenario, fragmento):
    api.registrar()
    if escenario:
        api.crear(escenario)
    r = api.post("/onboarding/steps/kyc")
    assert r.status_code == 409
    assert r.json()["code"] == "STEP_BLOCKED"
    assert fragmento in r.json()["message"]
    estado = api.get("/onboarding").json()
    assert _estados(estado) == ["COMPLETED", "CURRENT", "LOCKED"]
    assert len(leer_estado(api.owner)["events"]) == 2  # solo inicio + registro


def test_verificacion_sin_registro_no_salta_el_bloqueo(api):
    api.crear("APPROVED")
    r = api.post("/onboarding/steps/kyc")
    assert r.status_code == 409
    assert r.json()["code"] == "STEP_BLOCKED"
    assert "registro" in r.json()["message"]
    e = api.get("/onboarding").json()
    assert e["wallet_status"] == "IN_PROGRESS"
    assert e["current_step"] == "registro"


# ---------- Registro y validación ----------
def test_registro_exige_documento(api):
    for kwargs in ({}, {"json": {}}):
        r = api.post("/onboarding/steps/registro", **kwargs)
        assert r.status_code == 422
        assert r.json()["code"] == "VALIDATION_ERROR"
        assert "TEST-" in r.json()["message"]


def test_registro_con_documento_no_test(api, data_dir):
    r = api.post("/onboarding/steps/registro", json={"document_number": "12345678"})
    assert r.status_code == 422
    assert r.json()["code"] == "DOCUMENT_NOT_TEST"
    assert "12345678" not in r.text
    assert not data_dir.exists()


def test_registro_completa_el_primer_paso(api):
    e = api.registrar()
    assert e["wallet_status"] == "IN_PROGRESS"
    assert e["current_step"] == "kyc"
    assert _estados(e) == ["COMPLETED", "CURRENT", "LOCKED"]


def test_registro_no_guarda_el_documento(api, state_file):
    api.registrar(doc="TEST-SOLO-REGISTRO")
    assert "TEST-SOLO-REGISTRO" not in state_file(api.owner).read_text(encoding="utf-8")


@pytest.mark.parametrize("paso", ["kyc", "activacion"])
def test_pasos_distintos_de_registro_rechazan_documento(api, paso):
    r = api.post(f"/onboarding/steps/{paso}", json={"document_number": "TEST-0001"})
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"


def test_paso_inexistente_404(api):
    r = api.post("/onboarding/steps/inexistente")
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"
    assert "registro" in r.json()["message"]


# ---------- Integración ----------
def test_pendiente_aprobada_permite_continuar(api):
    api.registrar()
    v = api.crear("PENDING")
    assert api.post("/onboarding/steps/kyc").status_code == 409
    assert api.post(f"/kyc/verifications/{v['verification_id']}/decision", json={"decision": "APPROVED"}).status_code == 200
    r = api.post("/onboarding/steps/kyc")
    assert r.status_code == 200
    assert r.json()["current_step"] == "activacion"
    assert _estados(r.json()) == ["COMPLETED", "COMPLETED", "CURRENT"]


def test_rechazada_y_nueva_aprobada(api):
    api.registrar()
    api.crear("REJECTED")
    assert api.get("/onboarding").json()["wallet_status"] == "KYC_FAILED"
    assert api.post("/onboarding/steps/kyc").status_code == 409
    api.crear("APPROVED")  # cuenta la última verificación
    assert api.post("/onboarding/steps/kyc").status_code == 200


def test_recorrido_completo_activa_la_wallet(api, clock):
    api.registrar()
    api.crear("APPROVED")
    assert api.post("/onboarding/steps/kyc").status_code == 200
    clock.advance(seconds=42, milliseconds=500)
    final = api.post("/onboarding/steps/activacion")
    assert final.status_code == 200
    e = final.json()
    assert e["wallet_status"] == "ACTIVE"
    assert e["current_step"] is None
    assert _estados(e) == ["COMPLETED", "COMPLETED", "COMPLETED"]
    assert e["low_amount_payments_enabled"] is True
    assert e["duration_seconds"] == 42.5
    assert api.get("/onboarding").json() == e


def test_pagos_de_bajo_monto_solo_con_wallet_activa(api):
    assert api.get("/onboarding").json()["low_amount_payments_enabled"] is False
    assert api.registrar()["low_amount_payments_enabled"] is False
    api.crear("APPROVED")
    assert api.post("/onboarding/steps/kyc").json()["low_amount_payments_enabled"] is False
    assert api.post("/onboarding/steps/activacion").json()["low_amount_payments_enabled"] is True
    assert api.post("/control/reset").status_code == 200
    assert api.get("/onboarding").json()["low_amount_payments_enabled"] is False


def test_repetir_un_paso_completado_es_idempotente(api, leer_estado):
    api.registrar()
    assert api.registrar() == api.get("/onboarding").json()
    api.crear("APPROVED")
    primero = api.post("/onboarding/steps/kyc")
    segundo = api.post("/onboarding/steps/kyc")
    assert primero.status_code == segundo.status_code == 200
    assert primero.json() == segundo.json()
    assert len(leer_estado(api.owner)["events"]) == 3  # inicio, registro, kyc: sin duplicados


def test_propietarios_aislados(api):
    api.completar_flujo(owner=api.owner)
    otro = api.get("/onboarding", owner=api.other).json()
    assert otro["wallet_status"] == "NOT_STARTED"
    assert otro["current_step"] == "registro"
