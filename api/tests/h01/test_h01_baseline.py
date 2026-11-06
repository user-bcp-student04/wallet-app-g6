# api/tests/h01/test_h01_baseline.py
"""FASE 1 (línea base): infraestructura que no depende de las reglas del cambio."""


def test_openapi_expone_las_rutas_del_contrato(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    esperadas = {
        "/health": {"get"},
        "/scenarios": {"get"},
        "/support/cases": {"get"},
        "/control/reset": {"post"},
        "/kyc/verifications": {"post"},
        "/kyc/verifications/{verification_id}": {"get"},
        "/kyc/verifications/{verification_id}/decision": {"post"},
        "/onboarding": {"get"},
        "/onboarding/steps/{step_id}": {"post"},
    }
    for ruta, metodos in esperadas.items():
        assert ruta in paths, f"falta {ruta}"
        assert metodos <= set(paths[ruta]), f"faltan métodos en {ruta}"


def test_health_responde_ok_sin_identidad(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ruta_inexistente_usa_formato_unico_404(client):
    r = client.get("/no-existe")
    assert r.status_code == 404
    cuerpo = r.json()
    assert set(cuerpo) == {"code", "message"}
    assert cuerpo["code"] == "NOT_FOUND"
    assert "detail" not in cuerpo


def test_metodo_no_permitido_usa_formato_unico_405(client):
    r = client.delete("/health")
    assert r.status_code == 405
    cuerpo = r.json()
    assert set(cuerpo) == {"code", "message"}
    assert cuerpo["code"] == "METHOD_NOT_ALLOWED"
    assert "GET" in r.headers["allow"]


def test_error_no_controlado_devuelve_500_generico(client):
    def explotar():
        raise RuntimeError("secreto-interno-no-debe-salir")

    client.app.add_api_route("/__boom", explotar, methods=["GET"])
    r = client.get("/__boom")
    assert r.status_code == 500
    cuerpo = r.json()
    assert set(cuerpo) == {"code", "message"}
    assert cuerpo["code"] == "INTERNAL_ERROR"
    assert "secreto-interno" not in r.text
    assert "Traceback" not in r.text


def test_las_solicitudes_de_solo_lectura_no_escriben_en_disco(client, data_dir):
    assert client.get("/health").status_code == 200
    assert client.get("/scenarios").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/no-existe").status_code == 404
    assert not data_dir.exists()
