# api/tests/onboarding/test_h01_scenarios.py
"""3.2 GET /scenarios (lado API). El error de red es del cliente."""
import pytest

ESCENARIOS = {"APPROVED", "REJECTED", "MANUAL_REVIEW", "KYC_UNAVAILABLE"}


def test_scenarios_devuelve_lista_para_el_selector(client):
    r = client.get("/scenarios")
    assert r.status_code == 200
    lista = r.json()
    assert isinstance(lista, list)
    assert {item["id"] for item in lista} == ESCENARIOS


def test_scenarios_ids_son_unicos_y_label_no_vacio(client):
    lista = client.get("/scenarios").json()
    ids = [item["id"] for item in lista]
    assert len(ids) == len(set(ids))
    for item in lista:
        assert set(item) == {"id", "label"}
        assert isinstance(item["label"], str) and item["label"].strip()


def test_scenarios_rechaza_post_con_405(client, afirmar_error):
    afirmar_error(client.post("/scenarios"), 405, "METHOD_NOT_ALLOWED")


@pytest.mark.parametrize(
    "scenario,esperado",
    [("APPROVED", 201), ("REJECTED", 201), ("MANUAL_REVIEW", 201), ("KYC_UNAVAILABLE", 503)],
)
def test_scenarios_son_aceptados_por_post_kyc(client, crear, scenario, esperado):
    ids = {item["id"] for item in client.get("/scenarios").json()}
    assert scenario in ids
    assert crear(scenario).status_code == esperado
