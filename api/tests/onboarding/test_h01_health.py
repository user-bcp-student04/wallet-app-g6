# api/tests/onboarding/test_h01_health.py
"""3.1 GET /health (lado API). La latencia inválida se bloquea en el cliente (A-7)."""


def test_health_responde_200_con_estado_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_ignora_parametro_de_latencia(client):
    r = client.get("/health", params={"latency": "abc"})
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_rechaza_metodo_post_con_405(client, afirmar_error):
    r = client.post("/health")
    afirmar_error(r, 405, "METHOD_NOT_ALLOWED")
