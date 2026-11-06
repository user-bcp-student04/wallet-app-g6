# api/tests/onboarding/test_h01_support_cases.py
"""3.7 GET /support/cases."""
import re

CAMPOS = {"id", "type", "status", "verificationId", "createdAt"}
ID_CASO = re.compile(r"^case_[0-9a-f]{16}$")


def test_lista_vacia_sin_casos(client):
    r = client.get("/support/cases")
    assert r.status_code == 200
    assert r.json() == []


def test_caso_kyc_review_open_tras_manual_review(client, crear):
    v = crear("MANUAL_REVIEW").json()
    r = client.get("/support/cases")
    assert r.status_code == 200
    casos = r.json()
    assert len(casos) == 1
    caso = casos[0]
    assert set(caso) == CAMPOS
    assert caso["type"] == "KYC_REVIEW"
    assert caso["status"] == "OPEN"
    assert caso["verificationId"] == v["id"]
    assert ID_CASO.match(caso["id"])


def test_dos_revisiones_generan_dos_casos(client, crear):
    ids = {crear("MANUAL_REVIEW").json()["id"] for _ in range(2)}
    casos = client.get("/support/cases").json()
    assert len(casos) == 2
    assert {c["verificationId"] for c in casos} == ids
    assert all(c["status"] == "OPEN" for c in casos)


def test_caso_se_cierra_al_decidir(client, crear, decidir):
    v = crear("MANUAL_REVIEW").json()
    assert decidir(v["id"], "REJECTED").status_code == 200
    casos = client.get("/support/cases").json()
    assert len(casos) == 1
    assert casos[0]["status"] == "CLOSED"


def test_approved_rejected_y_503_no_generan_casos(client, crear):
    crear("APPROVED")
    crear("REJECTED")
    assert crear("KYC_UNAVAILABLE").status_code == 503
    assert client.get("/support/cases").json() == []


def test_support_cases_rechaza_post_con_405(client, afirmar_error):
    afirmar_error(client.post("/support/cases"), 405, "METHOD_NOT_ALLOWED")
