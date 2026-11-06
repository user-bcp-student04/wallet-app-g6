# api/tests/h01/test_h01_events_analytics.py
"""Tareas 2.5 (eventos y duración) y 2.8 (analítica mensual)."""
from datetime import datetime

from app.services import compute_duration_seconds
from app.storage import default_state


# ---------- Duración ----------
def test_duracion_sin_cierre_o_sin_inicio_es_none():
    assert compute_duration_seconds(None, None) is None
    assert compute_duration_seconds("2026-03-15T12:00:00+00:00", None) is None
    assert compute_duration_seconds(None, "2026-03-15T12:00:00+00:00") is None


def test_duracion_con_milisegundos():
    assert compute_duration_seconds("2026-03-15T12:00:00+00:00", "2026-03-15T12:01:30.123000+00:00") == 90.123
    assert compute_duration_seconds("2026-03-15T12:00:00+00:00", "2026-03-15T12:00:00+00:00") == 0.0


def test_duracion_expuesta_en_onboarding(api, clock):
    api.registrar()
    api.crear("APPROVED")
    assert api.post("/onboarding/steps/kyc").status_code == 200
    assert api.get("/onboarding").json()["duration_seconds"] is None  # sin cierre
    clock.advance(seconds=90, milliseconds=123)
    final = api.post("/onboarding/steps/activacion").json()
    assert final["duration_seconds"] == 90.123
    assert api.get("/onboarding").json()["duration_seconds"] == 90.123


# ---------- Eventos ----------
def test_eventos_del_flujo_completo_en_orden(api, clock, leer_estado):
    api.registrar()
    clock.advance(seconds=1)
    api.crear("APPROVED")
    api.post("/onboarding/steps/kyc")
    clock.advance(seconds=1)
    api.post("/onboarding/steps/activacion")
    estado = leer_estado(api.owner)
    assert [(e["type"], e["step"]) for e in estado["events"]] == [
        ("ONBOARDING_STARTED", None),
        ("STEP_COMPLETED", "registro"),
        ("STEP_COMPLETED", "kyc"),
        ("STEP_COMPLETED", "activacion"),
        ("ONBOARDING_CLOSED", None),
    ]
    instantes = [datetime.fromisoformat(e["at"]) for e in estado["events"]]
    assert instantes == sorted(instantes)
    assert estado["started_at"] == estado["events"][0]["at"]
    assert estado["closed_at"] == estado["events"][-1]["at"]


def test_eventos_no_se_duplican_al_repetir_pasos(api, leer_estado):
    api.registrar()
    api.registrar()
    api.crear("APPROVED")
    api.post("/onboarding/steps/kyc")
    api.post("/onboarding/steps/kyc")
    assert len(leer_estado(api.owner)["events"]) == 3


def test_pasos_bloqueados_no_registran_eventos(api, leer_estado, state_file):
    assert api.post("/onboarding/steps/kyc").status_code == 409
    assert not state_file(api.owner).exists()
    api.registrar()
    assert api.post("/onboarding/steps/activacion").status_code == 409
    assert len(leer_estado(api.owner)["events"]) == 2


def test_eventos_no_tienen_endpoint_publico(api):
    for ruta in ("/events", "/onboarding/events", "/analytics", "/analytics/monthly"):
        r = api.get(ruta)
        assert r.status_code == 404
        assert r.json()["code"] == "NOT_FOUND"
    assert "events" not in api.get("/onboarding").json()


# ---------- Analítica mensual (2.8) ----------
def _estado_cerrado(closed_at, gasto=()):
    s = default_state()
    s["started_at"] = "2026-01-01T00:00:00+00:00"
    s["closed_at"] = closed_at
    s["steps_completed"] = ["registro", "kyc", "activacion"]
    s["spend"] = [{"amount_cents": c} for c in gasto]
    return s


def test_analitica_sin_estados_devuelve_lista_vacia(service):
    assert service.monthly_analytics() == []


def test_analitica_agrupa_por_mes_utc(service, store):
    store.write("u1", _estado_cerrado("2026-01-10T10:00:00+00:00", gasto=(500, 250)))
    store.write("u2", _estado_cerrado("2026-01-31T23:59:59+00:00", gasto=(100,)))
    store.write("u3", _estado_cerrado("2026-02-01T00:00:00+00:00"))
    sin_cerrar = _estado_cerrado(None, gasto=(999,))
    sin_cerrar["steps_completed"] = ["registro"]
    store.write("u4", sin_cerrar)  # no cerró: no cuenta ni su gasto
    filas = [f.model_dump() for f in service.monthly_analytics()]
    assert filas == [
        {"month": "2026-01", "new_active_users": 2, "attributed_spend_cents": 850},
        {"month": "2026-02", "new_active_users": 1, "attributed_spend_cents": 0},
    ]


def test_analitica_borde_de_zona_horaria(service, store):
    store.write("a", _estado_cerrado("2026-02-28T23:30:00-05:00"))  # = 2026-03-01 04:30 UTC
    store.write("b", _estado_cerrado("2026-01-31T19:00:00-05:00"))  # = 2026-02-01 00:00 UTC
    filas = [f.model_dump() for f in service.monthly_analytics()]
    assert [(f["month"], f["new_active_users"]) for f in filas] == [("2026-02", 1), ("2026-03", 1)]


def test_analitica_ignora_estados_ilegibles(service, store, data_dir):
    store.write("ok", _estado_cerrado("2026-01-10T10:00:00+00:00", gasto=(300,)))
    corrupto = data_dir / "zz-corrupto"
    corrupto.mkdir()
    (corrupto / "state.json").write_text("{no es json", encoding="utf-8")
    (data_dir / "notas.txt").write_text("archivo suelto", encoding="utf-8")
    filas = [f.model_dump() for f in service.monthly_analytics()]
    assert filas == [{"month": "2026-01", "new_active_users": 1, "attributed_spend_cents": 300}]


def test_analitica_integrada_con_el_flujo_http(api, service):
    api.completar_flujo(owner=api.owner)
    api.completar_flujo(owner=api.other)
    api.registrar(owner="usuario-3")  # no cierra
    filas = [f.model_dump() for f in service.monthly_analytics()]
    # Ningún endpoint escribe `spend`: el gasto atribuido es 0 hasta que exista origen de pagos (T-10).
    assert filas == [{"month": "2026-03", "new_active_users": 2, "attributed_spend_cents": 0}]


def test_analitica_no_expone_propietarios(service, store):
    store.write("propietario-secreto-777", _estado_cerrado("2026-01-10T10:00:00+00:00"))
    for fila in service.monthly_analytics():
        assert set(fila.model_dump()) == {"month", "new_active_users", "attributed_spend_cents"}
        assert "propietario-secreto-777" not in fila.model_dump_json()
