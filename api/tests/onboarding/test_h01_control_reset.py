# api/tests/onboarding/test_h01_control_reset.py
"""3.8 POST /control/reset (lado API) y persistencia en memoria.

"Limpia estado local" y "cancelar la confirmación no llama a la API" son del cliente (casos C-06 y C-07).
"""
from fastapi.testclient import TestClient

from app import config
from app.main import app


def test_reset_limpia_estado_200(client, crear):
    aprobada = crear("APPROVED").json()
    pendiente = crear("MANUAL_REVIEW").json()
    assert len(client.get("/support/cases").json()) == 1

    r = client.post("/control/reset")
    assert r.status_code == 200
    assert r.json() == {"status": "reset"}

    assert client.get("/support/cases").json() == []
    assert client.get(f"/wallets/{aprobada['walletId']}").status_code == 404
    assert client.get(f"/kyc/verifications/{aprobada['id']}").status_code == 404
    assert client.get(f"/kyc/verifications/{pendiente['id']}").status_code == 404


def test_reset_sobre_estado_vacio_es_idempotente(client):
    for _ in range(2):
        r = client.post("/control/reset")
        assert r.status_code == 200
        assert r.json() == {"status": "reset"}


def test_reset_permite_empezar_de_cero(client, crear):
    crear("MANUAL_REVIEW")
    assert client.post("/control/reset").status_code == 200
    assert crear("MANUAL_REVIEW").status_code == 201
    assert len(client.get("/support/cases").json()) == 1


def test_reset_deshabilitado_devuelve_404_y_conserva_estado(client, crear, monkeypatch, afirmar_error):
    v = crear("APPROVED").json()
    monkeypatch.setattr(config, "ENABLE_CONTROL_RESET", False)
    afirmar_error(client.post("/control/reset"), 404, "NOT_FOUND")
    assert client.get(f"/kyc/verifications/{v['id']}").status_code == 200


def test_reset_rechaza_get_con_405(client, afirmar_error):
    afirmar_error(client.get("/control/reset"), 405, "METHOD_NOT_ALLOWED")


def test_estado_persiste_entre_clientes_mientras_no_haya_reset(crear):
    v = crear("APPROVED").json()
    with TestClient(app, raise_server_exceptions=False) as otro:
        assert otro.get(f"/kyc/verifications/{v['id']}").status_code == 200
        assert otro.post("/control/reset").status_code == 200
    with TestClient(app, raise_server_exceptions=False) as tercero:
        assert tercero.get(f"/kyc/verifications/{v['id']}").status_code == 404


def test_el_flujo_completo_no_escribe_archivos_en_disco(client, crear, decidir, tmp_path):
    # El fixture autouse fijó el directorio de trabajo en tmp_path.
    v = crear("MANUAL_REVIEW").json()
    decidir(v["id"], "APPROVED")
    client.get("/support/cases")
    client.post("/control/reset")
    assert list(tmp_path.iterdir()) == []
