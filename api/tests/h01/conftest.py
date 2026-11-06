# api/tests/h01/conftest.py
"""Fixtures aisladas para las pruebas de H01.

- DATA_DIR se redirige a tmp_path con monkeypatch (nunca se escribe en api/data).
- El servicio (lru_cache) se limpia antes y después de cada prueba.
- El reloj es inyectable para fijar fechas y duraciones.
"""
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[2]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import config  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services import OnboardingService, get_onboarding_service  # noqa: E402
from app.storage import OwnerStore  # noqa: E402


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs) -> None:
        self.now += timedelta(**kwargs)


class Api:
    """Atajos sobre TestClient: siempre envían X-Owner-Id salvo que se use el cliente crudo."""

    owner = "usuario-1"
    other = "usuario-2"

    def __init__(self, client: TestClient) -> None:
        self.client = client

    def headers(self, owner=None) -> dict:
        return {"X-Owner-Id": owner or self.owner}

    def get(self, path, owner=None, **kw):
        return self.client.get(path, headers=self.headers(owner), **kw)

    def post(self, path, owner=None, **kw):
        return self.client.post(path, headers=self.headers(owner), **kw)

    def crear(self, scenario="APPROVED", doc="TEST-0001", owner=None) -> dict:
        r = self.post("/kyc/verifications", owner=owner, json={"document_number": doc, "scenario": scenario})
        assert r.status_code == 201, r.text
        return r.json()

    def registrar(self, owner=None, doc="TEST-0001") -> dict:
        r = self.post("/onboarding/steps/registro", owner=owner, json={"document_number": doc})
        assert r.status_code == 200, r.text
        return r.json()

    def completar_flujo(self, owner=None) -> dict:
        self.registrar(owner)
        self.crear("APPROVED", owner=owner)
        r = self.post("/onboarding/steps/kyc", owner=owner)
        assert r.status_code == 200, r.text
        r = self.post("/onboarding/steps/activacion", owner=owner)
        assert r.status_code == 200, r.text
        return r.json()


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    destino = tmp_path / "data"
    monkeypatch.setattr(config, "DATA_DIR", destino)
    get_onboarding_service.cache_clear()
    yield destino
    get_onboarding_service.cache_clear()


@pytest.fixture
def clock():
    return FakeClock(datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc))


@pytest.fixture
def store(data_dir):
    return OwnerStore(data_dir)


@pytest.fixture
def service(store, clock):
    return OnboardingService(store, clock)


@pytest.fixture
def build_client(service):
    """Crea una app NUEVA (lee config.MAX_BODY_BYTES en ese momento) con el servicio aislado."""

    def _build() -> TestClient:
        aplicacion = create_app()
        aplicacion.dependency_overrides[get_onboarding_service] = lambda: service
        return TestClient(aplicacion, raise_server_exceptions=False)

    return _build


@pytest.fixture
def client(build_client):
    return build_client()


@pytest.fixture
def api(client):
    return Api(client)


@pytest.fixture
def state_file(data_dir):
    def _ruta(owner_id: str) -> Path:
        return data_dir / hashlib.sha256(owner_id.encode("utf-8")).hexdigest() / "state.json"

    return _ruta


@pytest.fixture
def leer_estado(state_file):
    def _leer(owner_id: str) -> dict:
        return json.loads(state_file(owner_id).read_text(encoding="utf-8"))

    return _leer
