# api/tests/onboarding/test_h01_wallets.py
"""3.6 GET /wallets/{id}."""
import pytest


def test_wallet_200_con_saldos_en_cero(client, crear):
    v = crear("APPROVED").json()
    r = client.get(f"/wallets/{v['walletId']}")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo == {"id": v["walletId"], "balances": {"available": 0, "pending": 0}}
    for saldo in cuerpo["balances"].values():
        assert type(saldo) is int  # entero, no bool ni float (A-10)


def test_wallet_inexistente_404(client, afirmar_error):
    afirmar_error(client.get("/wallets/wlt_ffffffffffffffff"), 404, "NOT_FOUND")


def test_wallet_id_en_el_limite_de_64_es_404(client, afirmar_error):
    afirmar_error(client.get("/wallets/" + "a" * 64), 404, "NOT_FOUND")


def test_wallet_id_invalido_400(client, afirmar_error):
    afirmar_error(client.get("/wallets/" + "a" * 65), 400, "BAD_REQUEST")
    afirmar_error(client.get("/wallets/id.con.punto"), 400, "BAD_REQUEST")


@pytest.mark.parametrize("scenario", ["REJECTED", "MANUAL_REVIEW"])
def test_no_hay_wallet_para_verificaciones_no_aprobadas(client, crear, store, afirmar_error, scenario):
    v = crear(scenario).json()
    assert v["walletId"] is None
    assert store.wallets == {}
    afirmar_error(client.get(f"/wallets/{v['id']}"), 404, "NOT_FOUND")
