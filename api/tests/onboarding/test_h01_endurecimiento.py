# api/tests/onboarding/test_h01_endurecimiento.py
"""Medidas defensivas visibles en backend_spec.md (T-8).

La entrega de Seguridad no estaba disponible: aquí solo se verifica lo documentado por Backend.
"""
from urllib.parse import quote

import pytest

IDS_PELIGROSOS = [
    "id.con.punto",
    "id con espacio",
    "x';DROP",
    "<script>",
    "a" * 65,
]


@pytest.mark.parametrize("valor", IDS_PELIGROSOS)
@pytest.mark.parametrize("prefijo", ["/kyc/verifications/", "/wallets/"])
def test_ids_con_formato_invalido_dan_400_sin_eco(client, afirmar_error, prefijo, valor):
    r = client.get(prefijo + quote(valor, safe=""))
    afirmar_error(r, 400, "BAD_REQUEST")
    assert valor not in r.text


@pytest.mark.parametrize("valor", IDS_PELIGROSOS)
def test_decision_con_id_peligroso_dan_400_sin_eco(client, afirmar_error, valor):
    r = client.post(
        f"/kyc/verifications/{quote(valor, safe='')}/decision",
        json={"decision": "APPROVED"},
    )
    afirmar_error(r, 400, "BAD_REQUEST")
    assert valor not in r.text


@pytest.mark.parametrize(
    "documento",
    ["<script>alert(1)</script>", "TEST-1'; DROP TABLE x;--", "TEST-１２３", "../../etc/passwd"],
)
def test_documento_con_contenido_peligroso_no_se_acepta_ni_se_refleja(client, store, documento):
    r = client.post("/kyc/verifications", json={"documentNumber": documento, "scenario": "APPROVED"})
    assert r.status_code == 400
    assert documento not in r.text
    assert store.verifications == {}


def test_respuestas_de_exito_no_exponen_estructuras_internas(client, crear):
    v = crear("MANUAL_REVIEW").json()
    textos = [
        client.get(f"/kyc/verifications/{v['id']}").text,
        client.get("/support/cases").text,
    ]
    for texto in textos:
        for interno in ("decision_status", "wallet_id", "verification_id", "created_at", "RLock"):
            assert interno not in texto
