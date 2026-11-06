# api/tests/onboarding/conftest.py
"""Fixtures de H01.

Aislamiento:
- monkeypatch.chdir(tmp_path): cualquier escritura accidental con ruta relativa cae en tmp_path.
- monkeypatch.setattr(config, ...): fija las banderas del servidor, sin depender del entorno.
- El almacén en memoria se resetea directamente (no via POST /control/reset) antes y después.
"""
import sys
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parents[2]  # .../api
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from fastapi.testclient import TestClient  # noqa: E402

from app import config  # noqa: E402
from app.main import app  # noqa: E402
from app.repository import get_store  # noqa: E402


@pytest.fixture(autouse=True)
def entorno_aislado(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "ENFORCE_TEST_DOC_PREFIX", False)
    monkeypatch.setattr(config, "ENABLE_CONTROL_RESET", True)
    get_store().reset()
    yield
    get_store().reset()


@pytest.fixture
def store():
    return get_store()


@pytest.fixture
def client():
    # raise_server_exceptions=False: permite observar respuestas 500 (backend_spec §5).
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def crear(client):
    def _crear(scenario, documento="TEST-0001"):
        return client.post(
            "/kyc/verifications",
            json={"documentNumber": documento, "scenario": scenario},
        )

    return _crear


@pytest.fixture
def decidir(client):
    def _decidir(verification_id, decision):
        return client.post(
            f"/kyc/verifications/{verification_id}/decision",
            json={"decision": decision},
        )

    return _decidir


@pytest.fixture
def afirmar_error():
    """Comprueba el formato único de error {"code","message"} y devuelve el cuerpo."""

    def _afirmar(resp, status, code):
        assert resp.status_code == status, resp.text
        assert resp.headers["content-type"].startswith("application/json")
        cuerpo = resp.json()
        assert set(cuerpo) == {"code", "message"}
        assert cuerpo["code"] == code
        # Heurística de "accionable": texto no trivial. La revisión humana sigue siendo necesaria.
        assert isinstance(cuerpo["message"], str)
        assert len(cuerpo["message"].strip()) >= 20
        assert "Traceback" not in resp.text
        return cuerpo

    return _afirmar
