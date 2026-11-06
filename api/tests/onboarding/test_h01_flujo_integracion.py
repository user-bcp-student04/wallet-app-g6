# api/tests/onboarding/test_h01_flujo_integracion.py
"""Integración de extremo a extremo del API (3.3 a 3.8 y lado API de 3.10)."""
import pytest


def test_flujo_aprobado_directo(client, crear):
    v = crear("APPROVED")
    assert v.status_code == 201
    v = v.json()
    assert client.get(f"/kyc/verifications/{v['id']}").json() == v
    w = client.get(f"/wallets/{v['walletId']}")
    assert w.status_code == 200
    assert w.json()["balances"] == {"available": 0, "pending": 0}
    assert client.get("/support/cases").json() == []


def test_flujo_revision_manual_aprobada(client, crear, decidir, afirmar_error):
    v = crear("MANUAL_REVIEW").json()
    assert v["decisionStatus"] == "PENDING" and v["walletId"] is None

    casos = client.get("/support/cases").json()
    assert [(c["type"], c["status"], c["verificationId"]) for c in casos] == [
        ("KYC_REVIEW", "OPEN", v["id"])
    ]

    decidida = decidir(v["id"], "APPROVED")
    assert decidida.status_code == 200
    wid = decidida.json()["walletId"]
    assert client.get(f"/wallets/{wid}").json()["balances"] == {"available": 0, "pending": 0}
    assert client.get("/support/cases").json()[0]["status"] == "CLOSED"

    afirmar_error(decidir(v["id"], "REJECTED"), 409, "DECISION_CONFLICT")


def test_flujo_revision_manual_rechazada(client, crear, decidir, store):
    v = crear("MANUAL_REVIEW").json()
    decidida = decidir(v["id"], "REJECTED").json()
    assert decidida["status"] == "REJECTED"
    assert decidida["walletId"] is None
    assert store.wallets == {}
    assert client.get("/support/cases").json()[0]["status"] == "CLOSED"


def test_flujo_reset_tras_flujo_completo(client, crear, decidir):
    v = crear("MANUAL_REVIEW").json()
    decidir(v["id"], "APPROVED")
    assert client.post("/control/reset").status_code == 200
    assert client.get("/support/cases").json() == []
    assert client.get(f"/kyc/verifications/{v['id']}").status_code == 404


@pytest.mark.parametrize(
    "scenario,decision,activa",
    [
        pytest.param("APPROVED", None, True, id="aprobado-directo"),
        pytest.param("REJECTED", None, False, id="rechazado"),
        pytest.param("MANUAL_REVIEW", None, False, id="pending"),
        pytest.param("MANUAL_REVIEW", "APPROVED", True, id="pending-aprobado"),
        pytest.param("MANUAL_REVIEW", "REJECTED", False, id="pending-rechazado"),
    ],
)
def test_wallet_activa_solo_tras_aprobacion(client, crear, decidir, store, scenario, decision, activa):
    v = crear(scenario).json()
    if decision:
        v = decidir(v["id"], decision).json()
    if activa:
        assert v["walletId"] is not None
        w = client.get(f"/wallets/{v['walletId']}")
        assert w.status_code == 200
        assert w.json()["balances"] == {"available": 0, "pending": 0}
    else:
        assert v["walletId"] is None
        assert client.get(f"/wallets/{v['id']}").status_code == 404
        assert store.wallets == {}
