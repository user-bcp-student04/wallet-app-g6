# api/tests/h01/test_h01_console.py
"""Tarea 2.7 (lado API): /scenarios, /support/cases y /control/reset."""


def test_scenarios_publica_los_cuatro_escenarios_sin_identidad(client):
    r = client.get("/scenarios")
    assert r.status_code == 200
    items = r.json()["scenarios"]
    assert len(items) == 4
    assert {i["name"] for i in items} == {"APPROVED", "REJECTED", "PENDING", "EXPIRED"}
    assert all(set(i) == {"name", "description"} and i["description"].strip() for i in items)


def test_support_cases_vacio_para_propietario_nuevo(api, data_dir):
    r = api.get("/support/cases")
    assert r.status_code == 200
    assert r.json() == {"cases": []}
    assert not data_dir.exists()


def test_support_cases_lista_solo_las_no_aprobadas(api):
    ids = {s: api.crear(s)["verification_id"] for s in ("APPROVED", "REJECTED", "PENDING", "EXPIRED")}
    casos = api.get("/support/cases").json()["cases"]
    assert {c["verification_id"]: c["status"] for c in casos} == {
        ids["REJECTED"]: "REJECTED",
        ids["PENDING"]: "PENDING",
        ids["EXPIRED"]: "EXPIRED",
    }
    assert all(set(c) == {"verification_id", "status", "message"} and c["message"].strip() for c in casos)


def test_support_cases_no_mezcla_propietarios(api):
    api.crear("PENDING", owner=api.owner)
    assert api.get("/support/cases", owner=api.other).json() == {"cases": []}


def test_reset_devuelve_el_estado_inicial(api, state_file):
    api.registrar()
    api.crear("PENDING")
    assert state_file(api.owner).exists()
    r = api.post("/control/reset")
    assert r.status_code == 200
    assert r.json() == {"status": "reset"}
    assert not state_file(api.owner).exists()
    estado = api.get("/onboarding").json()
    assert estado["wallet_status"] == "NOT_STARTED"
    assert estado["current_step"] == "registro"
    assert api.get("/support/cases").json() == {"cases": []}


def test_reset_es_idempotente(api):
    assert api.post("/control/reset").status_code == 200  # sin estado previo
    api.registrar()
    assert api.post("/control/reset").status_code == 200
    assert api.post("/control/reset").status_code == 200


def test_reset_solo_afecta_al_propietario_autenticado(api, state_file):
    api.registrar(owner=api.owner)
    api.registrar(owner=api.other)
    assert api.post("/control/reset", owner=api.owner).status_code == 200
    assert not state_file(api.owner).exists()
    assert state_file(api.other).exists()
    assert api.get("/onboarding", owner=api.other).json()["current_step"] == "kyc"
