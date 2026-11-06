# api/tests/h01/test_h01_persistence.py
"""Contrato de persistencia: ruta, esquema, atomicidad, estados ilegibles y concurrencia."""
import hashlib
import json
import stat
from concurrent.futures import ThreadPoolExecutor

import pytest

from app import storage
from app.schemas import KycScenario
from app.storage import default_state

CLAVES = {"schema_version", "started_at", "closed_at", "steps_completed", "verifications", "events", "spend"}

ESTADOS_ILEGIBLES = {
    "no_json": "{esto no es json",
    "version_desconocida": json.dumps({**default_state(), "schema_version": 99}),
    "incompleto": json.dumps({"schema_version": 1, "started_at": None}),
    "no_objeto": "[]",
}


def _sembrar(state_file, owner, contenido):
    ruta = state_file(owner)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


# ---------- Ruta y esquema ----------
def test_estado_se_guarda_en_directorio_derivado_del_hash(api, data_dir):
    api.registrar()
    digest = hashlib.sha256(api.owner.encode("utf-8")).hexdigest()
    assert (data_dir / digest / "state.json").is_file()
    assert [p.name for p in data_dir.iterdir()] == [digest]


def test_el_estado_persistido_tiene_el_esquema_esperado(api, leer_estado):
    api.registrar()
    api.crear("PENDING")
    estado = leer_estado(api.owner)
    assert set(estado) == CLAVES
    assert estado["schema_version"] == 1
    assert estado["steps_completed"] == ["registro"]
    assert len(estado["verifications"]) == 1
    assert estado["closed_at"] is None
    assert estado["spend"] == []


def test_directorio_del_propietario_es_privado(api, state_file):  # POSIX (T-9)
    api.registrar()
    modo = stat.S_IMODE(state_file(api.owner).parent.stat().st_mode)
    assert modo & 0o077 == 0, oct(modo)


def test_no_quedan_temporales_tras_escribir(api, state_file):
    api.registrar()
    api.crear("PENDING")
    api.crear("APPROVED")
    nombres = sorted(p.name for p in state_file(api.owner).parent.iterdir())
    assert nombres == ["state.json"]


# ---------- Atomicidad ----------
def test_fallo_de_escritura_no_deja_estado_parcial(api, state_file, monkeypatch):
    def falla(*args, **kwargs):
        raise OSError("disco lleno simulado")

    with monkeypatch.context() as m:
        m.setattr(storage.os, "replace", falla)
        r = api.post("/kyc/verifications", json={"document_number": "TEST-0001", "scenario": "APPROVED"})
    assert r.status_code == 500
    assert r.json() == {
        "code": "INTERNAL_ERROR",
        "message": "Ocurrió un error interno. Inténtalo de nuevo más tarde.",
    }
    assert "disco lleno" not in r.text
    directorio = state_file(api.owner).parent
    assert not state_file(api.owner).exists()
    assert list(directorio.glob(".state-*")) == []
    assert api.get("/support/cases").json() == {"cases": []}


# ---------- Archivos preexistentes ----------
def test_archivo_preexistente_valido_se_reutiliza(api, state_file):
    previo = default_state()
    previo["started_at"] = "2026-01-01T00:00:00+00:00"
    previo["steps_completed"] = ["registro"]
    previo["events"] = [
        {"type": "ONBOARDING_STARTED", "step": None, "at": "2026-01-01T00:00:00+00:00"},
        {"type": "STEP_COMPLETED", "step": "registro", "at": "2026-01-01T00:00:00+00:00"},
    ]
    _sembrar(state_file, api.owner, json.dumps(previo))
    e = api.get("/onboarding").json()
    assert e["current_step"] == "kyc"
    assert e["wallet_status"] == "IN_PROGRESS"


@pytest.mark.parametrize("contenido", list(ESTADOS_ILEGIBLES.values()), ids=list(ESTADOS_ILEGIBLES))
def test_estado_corrupto_devuelve_500_y_no_se_sobrescribe(api, state_file, contenido):
    ruta = _sembrar(state_file, api.owner, contenido)
    lectura = api.get("/onboarding")
    assert lectura.status_code == 500
    assert lectura.json()["code"] == "INTERNAL_ERROR"
    escritura = api.post("/kyc/verifications", json={"document_number": "TEST-0001", "scenario": "APPROVED"})
    assert escritura.status_code == 500
    assert escritura.json()["code"] == "INTERNAL_ERROR"
    assert ruta.read_text(encoding="utf-8") == contenido  # no se sobrescribió


def test_error_500_no_filtra_rutas_ni_hash(api, state_file, data_dir):
    _sembrar(state_file, api.owner, "{corrupto")
    r = api.get("/onboarding")
    assert r.status_code == 500
    digest = hashlib.sha256(api.owner.encode("utf-8")).hexdigest()
    for prohibido in (str(data_dir), digest, api.owner, "state.json", "Traceback", "JSON"):
        assert prohibido not in r.text


def test_reset_repara_estado_corrupto(api, state_file):
    _sembrar(state_file, api.owner, "{corrupto")
    assert api.get("/onboarding").status_code == 500
    assert api.post("/control/reset").status_code == 200
    assert api.get("/onboarding").json()["wallet_status"] == "NOT_STARTED"


def test_temporal_huerfano_es_inofensivo(api, state_file):
    api.registrar()
    huerfano = state_file(api.owner).parent / ".state-huerfano.tmp"
    huerfano.write_text("basura", encoding="utf-8")
    assert api.get("/onboarding").json()["current_step"] == "kyc"
    api.crear("PENDING")
    assert api.get("/support/cases").status_code == 200
    assert huerfano.exists()  # no se lee ni se borra automáticamente


# ---------- Concurrencia (a nivel de servicio; T-12) ----------
def test_escrituras_concurrentes_del_mismo_propietario(service, state_file):
    total = 20
    with ThreadPoolExecutor(max_workers=10) as pool:
        resultados = list(
            pool.map(
                lambda i: service.create_verification("usuario-c", f"TEST-{i:04d}", KycScenario.PENDING),
                range(total),
            )
        )
    ids = {r.verification_id for r in resultados}
    assert len(ids) == total
    estado = json.loads(state_file("usuario-c").read_text(encoding="utf-8"))  # JSON válido
    assert {v["verification_id"] for v in estado["verifications"]} == ids
    assert len(estado["verifications"]) == total


def test_pasos_concurrentes_no_duplican_eventos(service, state_file):
    with ThreadPoolExecutor(max_workers=10) as pool:
        resultados = list(pool.map(lambda _: service.submit_step("usuario-c", "registro", "TEST-0001"), range(10)))
    assert all(r.current_step == "kyc" for r in resultados)
    estado = json.loads(state_file("usuario-c").read_text(encoding="utf-8"))
    assert estado["steps_completed"] == ["registro"]
    assert [(e["type"], e["step"]) for e in estado["events"]] == [
        ("ONBOARDING_STARTED", None),
        ("STEP_COMPLETED", "registro"),
    ]


def test_concurrencia_con_propietarios_distintos(service, state_file):
    propietarios = [f"u-{i}" for i in range(16)]

    def trabajo(owner):
        for n in range(3):
            service.create_verification(owner, f"TEST-{n}", KycScenario.PENDING)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(trabajo, propietarios))
    for owner in propietarios:
        estado = json.loads(state_file(owner).read_text(encoding="utf-8"))
        assert len(estado["verifications"]) == 3
