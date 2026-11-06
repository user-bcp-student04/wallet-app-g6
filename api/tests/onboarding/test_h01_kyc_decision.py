# api/tests/onboarding/test_h01_kyc_decision.py
"""3.5 POST /kyc/verifications/{id}/decision."""
import threading

import pytest

from app import services
from app.errors import ApiError


def _pendiente(crear):
    r = crear("MANUAL_REVIEW")
    assert r.status_code == 201
    return r.json()


def test_decision_aprobada_sobre_pending_200_y_abre_wallet(crear, decidir, client):
    v = _pendiente(crear)
    r = decidir(v["id"], "APPROVED")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["id"] == v["id"]
    assert cuerpo["status"] == "APPROVED"
    assert cuerpo["decisionStatus"] == "DECIDED"
    assert cuerpo["walletId"] is not None
    w = client.get(f"/wallets/{cuerpo['walletId']}")
    assert w.status_code == 200
    assert w.json()["balances"] == {"available": 0, "pending": 0}


def test_decision_rechazada_sobre_pending_200_sin_wallet(crear, decidir, store):
    v = _pendiente(crear)
    r = decidir(v["id"], "REJECTED")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["status"] == "REJECTED"
    assert cuerpo["decisionStatus"] == "DECIDED"
    assert cuerpo["walletId"] is None
    assert store.wallets == {}


def test_segunda_decision_409_decision_conflict(client, crear, decidir, afirmar_error):
    v = _pendiente(crear)
    assert decidir(v["id"], "APPROVED").status_code == 200
    r = decidir(v["id"], "REJECTED")
    afirmar_error(r, 409, "DECISION_CONFLICT")
    # El estado no cambió por el intento fallido
    actual = client.get(f"/kyc/verifications/{v['id']}").json()
    assert actual["status"] == "APPROVED"
    assert actual["decisionStatus"] == "DECIDED"


@pytest.mark.parametrize("scenario", ["APPROVED", "REJECTED"])
def test_decision_sobre_verificacion_no_pending_409(crear, decidir, afirmar_error, scenario):
    v = crear(scenario).json()
    assert v["decisionStatus"] == "NOT_REQUIRED"
    afirmar_error(decidir(v["id"], "APPROVED"), 409, "DECISION_CONFLICT")


def test_decision_inexistente_404(decidir, afirmar_error):
    afirmar_error(decidir("ver_0000000000000000", "APPROVED"), 404, "NOT_FOUND")


@pytest.mark.parametrize(
    "cuerpo",
    [
        pytest.param({"decision": "MANUAL_REVIEW"}, id="manual-review"),
        pytest.param({"decision": "PENDING"}, id="pending"),
        pytest.param({"decision": "approved"}, id="minusculas"),
        pytest.param({"decision": None}, id="null"),
        pytest.param({}, id="ausente"),
    ],
)
def test_decision_invalida_400(client, crear, afirmar_error, cuerpo):
    v = _pendiente(crear)
    r = client.post(f"/kyc/verifications/{v['id']}/decision", json=cuerpo)
    afirmar_error(r, 400, "BAD_REQUEST")


def test_decision_con_id_invalido_400(decidir, afirmar_error):
    afirmar_error(decidir("id.con.punto", "APPROVED"), 400, "BAD_REQUEST")
    afirmar_error(decidir("a" * 65, "APPROVED"), 400, "BAD_REQUEST")


def test_decision_invalida_no_altera_el_estado(client, crear, decidir):
    v = _pendiente(crear)
    client.post(f"/kyc/verifications/{v['id']}/decision", json={"decision": "PENDING"})
    actual = client.get(f"/kyc/verifications/{v['id']}").json()
    assert actual["decisionStatus"] == "PENDING"
    assert decidir(v["id"], "APPROVED").status_code == 200


def test_decision_cuerpo_sobre_el_limite_413(client, crear, afirmar_error):
    from app import config

    v = _pendiente(crear)
    grande = '{"decision":"APPROVED","relleno":"' + "a" * config.MAX_BODY_BYTES + '"}'
    r = client.post(
        f"/kyc/verifications/{v['id']}/decision",
        content=grande.encode(),
        headers={"Content-Type": "application/json"},
    )
    afirmar_error(r, 413, "PAYLOAD_TOO_LARGE")


def test_dos_decisiones_simultaneas_un_exito_un_conflicto(crear, store):
    # Concurrencia a nivel de servicio (atomicidad bajo el lock del almacén).
    v = _pendiente(crear)
    barrera = threading.Barrier(2)
    resultados = []

    def trabajador():
        barrera.wait(timeout=5)
        try:
            services.decide_verification(store, v["id"], "APPROVED")
            resultados.append("ok")
        except ApiError as exc:
            resultados.append(exc.code)

    hilos = [threading.Thread(target=trabajador) for _ in range(2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=10)
    assert not any(h.is_alive() for h in hilos)
    assert sorted(resultados) == ["DECISION_CONFLICT", "ok"]
    assert len(store.wallets) == 1
