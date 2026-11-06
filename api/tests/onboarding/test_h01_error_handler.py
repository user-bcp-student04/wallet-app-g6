# api/tests/onboarding/test_h01_error_handler.py
"""3.9 Manejador de errores común: 400, 404, 409, 413, 429 y 503.

429: ningún endpoint real lo genera (A-6). Se prueba el handler con una app aislada,
sin modificar api/app/. 500: se provoca con una app aislada.
"""
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app import config
from app.errors import register_error_handlers


# ---------------- app real ----------------

def test_400_validacion_usa_formato_comun_y_nombra_campos(client, afirmar_error):
    r = client.post("/kyc/verifications", json={})
    cuerpo = afirmar_error(r, 400, "BAD_REQUEST")
    assert "documentNumber" in cuerpo["message"]
    assert "scenario" in cuerpo["message"]


@pytest.mark.parametrize(
    "metodo,ruta,json_cuerpo",
    [
        ("POST", "/kyc/verifications", {}),
        ("POST", "/kyc/verifications", {"documentNumber": "x y", "scenario": "APPROVED"}),
        ("GET", "/kyc/verifications/id.con.punto", None),
        ("GET", "/wallets/id.con.punto", None),
        ("POST", "/kyc/verifications/ver_0000000000000000/decision", {"decision": "NADA"}),
    ],
)
def test_validacion_nunca_responde_422(client, metodo, ruta, json_cuerpo):
    r = client.request(metodo, ruta, json=json_cuerpo)
    assert r.status_code == 400
    assert r.status_code != 422


def test_400_no_repite_valores_enviados(client):
    r = client.post(
        "/kyc/verifications",
        json={"documentNumber": "SECRETO valor!", "scenario": "APPROVED"},
    )
    assert r.status_code == 400
    assert "SECRETO" not in r.text


def test_404_ruta_inexistente(client, afirmar_error):
    afirmar_error(client.get("/no-existe"), 404, "NOT_FOUND")


def test_404_recurso_inexistente(client, afirmar_error):
    afirmar_error(client.get("/wallets/wlt_ffffffffffffffff"), 404, "NOT_FOUND")


def test_405_metodo_no_permitido(client, afirmar_error):
    afirmar_error(client.delete("/health"), 405, "METHOD_NOT_ALLOWED")


def test_409_conflicto_de_decision(client, crear, decidir, afirmar_error):
    v = crear("MANUAL_REVIEW").json()
    decidir(v["id"], "APPROVED")
    cuerpo = afirmar_error(decidir(v["id"], "APPROVED"), 409, "DECISION_CONFLICT")
    assert "ya fue decidida" in cuerpo["message"]


def test_413_cuerpo_demasiado_grande(client, afirmar_error):
    grande = '{"documentNumber":"TEST-1","scenario":"APPROVED","relleno":"' + "a" * config.MAX_BODY_BYTES + '"}'
    r = client.post(
        "/kyc/verifications",
        content=grande.encode(),
        headers={"Content-Type": "application/json"},
    )
    afirmar_error(r, 413, "PAYLOAD_TOO_LARGE")


def test_503_kyc_no_disponible(crear, afirmar_error):
    afirmar_error(crear("KYC_UNAVAILABLE"), 503, "KYC_UNAVAILABLE")


# ---------------- app aislada: handler de HTTPException y excepciones no controladas ----------------

def _app_aislada():
    mini = FastAPI()
    register_error_handlers(mini)

    @mini.get("/lanzar/{codigo}")
    def lanzar(codigo: int):
        cabeceras = {"Retry-After": "5"} if codigo == 429 else None
        raise HTTPException(
            status_code=codigo,
            detail="detalle-interno-no-publicar",
            headers=cabeceras,
        )

    @mini.get("/explotar")
    def explotar():
        raise RuntimeError("secreto-interno-xyz")

    return mini


@pytest.fixture
def cliente_aislado():
    with TestClient(_app_aislada(), raise_server_exceptions=False) as c:
        yield c


@pytest.mark.parametrize(
    "status,code",
    [
        (400, "BAD_REQUEST"),
        (401, "UNAUTHORIZED"),
        (403, "FORBIDDEN"),
        (404, "NOT_FOUND"),
        (405, "METHOD_NOT_ALLOWED"),
        (409, "CONFLICT"),
        (413, "PAYLOAD_TOO_LARGE"),
        (429, "RATE_LIMITED"),
        (503, "SERVICE_UNAVAILABLE"),
    ],
)
def test_codigos_http_generan_codigo_y_mensaje_comunes(cliente_aislado, afirmar_error, status, code):
    r = cliente_aislado.get(f"/lanzar/{status}")
    afirmar_error(r, status, code)
    assert "detalle-interno-no-publicar" not in r.text  # el detail interno no se filtra


def test_429_conserva_cabecera_retry_after(cliente_aislado):
    r = cliente_aislado.get("/lanzar/429")
    assert r.status_code == 429
    assert r.headers.get("retry-after") == "5"


def test_codigo_desconocido_usa_http_error(cliente_aislado):
    r = cliente_aislado.get("/lanzar/418")
    assert r.status_code == 418
    assert r.json() == {
        "code": "HTTP_ERROR",
        "message": "No se pudo completar la solicitud.",
    }


def test_500_no_filtra_detalles_internos(cliente_aislado):
    r = cliente_aislado.get("/explotar")
    assert r.status_code == 500
    cuerpo = r.json()
    assert set(cuerpo) == {"code", "message"}
    assert cuerpo["code"] == "INTERNAL_ERROR"
    assert "secreto-interno-xyz" not in r.text
    assert "RuntimeError" not in r.text
    assert "Traceback" not in r.text
