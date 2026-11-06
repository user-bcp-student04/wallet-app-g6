# api/tests/test_h01_support_logic.py
"""Línea base. Prueba la lógica de verificación de H01 con datos sintéticos.

Aislamiento: tmp_path (raíces de repositorio simuladas) y monkeypatch (variables de entorno).
Estas pruebas no leen el .env real ni el mock real.
"""
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

try:
    from h01_support import (
        BASELINE_PATH,
        check_baseline_text,
        check_health,
        check_spec_text,
        get_mock_url,
        parse_env_text,
        parse_tasks,
        read_env_problems,
        repo_root,
        url_in_environment_ts,
        validate_env,
    )
except ImportError:  # api/tests con __init__.py
    from tests.h01_support import (
        BASELINE_PATH,
        check_baseline_text,
        check_health,
        check_spec_text,
        get_mock_url,
        parse_env_text,
        parse_tasks,
        read_env_problems,
        repo_root,
        url_in_environment_ts,
        validate_env,
    )

VALID_ENV = "GITHUB_OWNER=user-bcp-student04\nPR_REPO=wallet-app-g6\nCREWAI_INCLUDE_DATA=true\n"
ALL_TOPICS = (
    "Frontera de eventos: decidido.\n"
    "KYC simulado: un solo paso.\n"
    "Persistencia de eventos: en memoria.\n"
    "CORS del mock: origen de desarrollo.\n"
    "Usuario activo: definido.\n"
    "Fuente de gasto de adquisición: semilla.\n"
)


def _problems(text: str) -> list[str]:
    values, duplicates = parse_env_text(text)
    return validate_env(values, duplicates)


# ------------------------------------------------------------- 1.1 (.env)
def test_env_valido_sin_problemas():  # T-02
    assert _problems(VALID_ENV) == []


def test_env_variable_ausente():  # T-03
    problems = _problems("GITHUB_OWNER=user-bcp-student04\nPR_REPO=wallet-app-g6\n")
    assert "falta CREWAI_INCLUDE_DATA" in problems


def test_env_valor_distinto():  # T-04
    problems = _problems(VALID_ENV.replace("PR_REPO=wallet-app-g6", "PR_REPO=otro-repo"))
    assert any(p.startswith("valor incorrecto en PR_REPO") for p in problems)


@pytest.mark.parametrize(
    "bad_line",
    ['CREWAI_INCLUDE_DATA="true"', "CREWAI_INCLUDE_DATA=true ", "CREWAI_INCLUDE_DATA=True"],
)
def test_env_comillas_y_espacios_finales_no_validos(bad_line):  # T-05
    text = "GITHUB_OWNER=user-bcp-student04\nPR_REPO=wallet-app-g6\n" + bad_line + "\n"
    problems = _problems(text)
    assert any("CREWAI_INCLUDE_DATA" in p for p in problems)


def test_env_crlf_comentarios_y_lineas_vacias():  # T-06
    text = (
        "# configuración local\r\n\r\n"
        "GITHUB_OWNER=user-bcp-student04\r\n"
        "PR_REPO=wallet-app-g6\r\n"
        "CREWAI_INCLUDE_DATA=true\r\n"
    )
    assert _problems(text) == []
    # una variable solo comentada no cuenta como definida
    commented = "GITHUB_OWNER=user-bcp-student04\nPR_REPO=wallet-app-g6\n# CREWAI_INCLUDE_DATA=true\n"
    assert "falta CREWAI_INCLUDE_DATA" in _problems(commented)


def test_env_duplicados_y_secretos():  # T-07
    problems = _problems(VALID_ENV + "PR_REPO=wallet-app-g6\nGITHUB_TOKEN=abc\n")
    assert "clave duplicada: PR_REPO" in problems
    assert "clave con aspecto de secreto: GITHUB_TOKEN" in problems


def test_env_valor_con_igual():  # T-08
    problems = _problems(VALID_ENV.replace("PR_REPO=wallet-app-g6", "PR_REPO=a=b"))
    assert any(p.startswith("valor incorrecto en PR_REPO") for p in problems)


def test_repo_root_respeta_override_y_lee_env_aislado(tmp_path, monkeypatch):  # T-09
    monkeypatch.setenv("H01_REPO_ROOT", str(tmp_path))
    assert repo_root() == tmp_path.resolve()
    assert read_env_problems(repo_root()) == [".env no existe"]
    (tmp_path / ".env").write_text(VALID_ENV, encoding="utf-8")
    assert read_env_problems(repo_root()) == []


# ----------------------------------------------------------- 1.2 (baseline)
FILLED_BASELINE = (
    "# Línea base H01\n\n"
    "- Fecha y hora de ejecución: 2026-11-06 14:00\n"
    "- Comando: python tools/verify.py\n"
    "- Código de salida: 0\n"
    "- Resultado (pasa / falla): pasa\n"
    "- Salida resumida o fallos preexistentes: ninguno\n"
    "- Ejecutado por: alguien\n"
)


def test_baseline_md_rellenado_es_valido(tmp_path):  # T-10
    path = tmp_path / BASELINE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(FILLED_BASELINE, encoding="utf-8")
    assert check_baseline_text(path.read_text(encoding="utf-8")) == []


def test_baseline_plantilla_sin_rellenar_se_rechaza():  # T-11
    template = (
        "- Fecha y hora de ejecución: <RELLENAR>\n"
        "- Código de salida: <RELLENAR>\n"
        "- Resultado (pasa / falla): <RELLENAR>\n"
    )
    problems = check_baseline_text(template)
    assert "quedan campos <RELLENAR>" in problems
    assert "falta código de salida numérico" in problems


def test_baseline_incoherente_o_sin_fecha():  # T-12
    assert any("incoherente" in p for p in check_baseline_text(
        FILLED_BASELINE.replace("Resultado (pasa / falla): pasa", "Resultado (pasa / falla): falla")))
    assert any("incoherente" in p for p in check_baseline_text(
        FILLED_BASELINE.replace("Código de salida: 0", "Código de salida: 1")))
    sin_fecha = FILLED_BASELINE.replace("2026-11-06 14:00", "ayer")
    assert "falta fecha AAAA-MM-DD" in check_baseline_text(sin_fecha)


# ------------------------------------------------------------ 1.3 (spec)
def test_spec_sin_marcadores_pendientes_y_con_los_seis_temas():  # T-13
    assert check_spec_text(ALL_TOPICS) == []


def test_spec_con_pendientes_o_tema_faltante():  # T-14
    problems = check_spec_text(ALL_TOPICS.replace("decidido.", "decidido. [PENDIENTE]"))
    assert "marcador pendiente: [PENDIENTE]" in problems
    sin_cors = ALL_TOPICS.replace("CORS del mock: origen de desarrollo.\n", "")
    assert "tema ausente en la spec: CORS del mock" in check_spec_text(sin_cors)


def test_tasks_parseo():  # T-15
    text = "- [ ] 1.1 a\n- [x] 1.2 b\n- [X] 1.3 c\n- [ ] 1.4 d\n"
    assert parse_tasks(text) == {"1.1": False, "1.2": True, "1.3": True, "1.4": False}


# ------------------------------------------------- 1.4 (environment.ts, health)
def test_environment_ts_coincidencia_exacta():  # T-32
    ts = "export const environment = {\n  production: false,\n  mockUrl: 'http://localhost:30001',\n};\n"
    assert url_in_environment_ts(ts, "http://localhost:30001")
    assert not url_in_environment_ts(ts, "http://localhost:3000")  # prefijo no basta
    assert url_in_environment_ts(ts, "http://localhost:30001/")  # barra final tolerada


def test_get_mock_url_exige_variable(monkeypatch):  # T-31
    monkeypatch.delenv("MOCK_W1_URL", raising=False)
    with pytest.raises(AssertionError):
        get_mock_url()
    monkeypatch.setenv("MOCK_W1_URL", "http://127.0.0.1:9999")
    assert get_mock_url() == "http://127.0.0.1:9999"


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_check_health_200_y_503():  # T-16
    assert check_health("http://mock.test", client=_client(lambda r: httpx.Response(200))) == 200
    assert check_health("http://mock.test", client=_client(lambda r: httpx.Response(503))) == 503


def test_check_health_url_con_barra_final_pide_health_exacto():  # T-16 (borde)
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        return httpx.Response(200)

    check_health("http://mock.test/", client=_client(handler))
    assert seen == ["/health"]


def test_check_health_propaga_errores_de_red():  # T-16 (negativo)
    def refuse(request):
        raise httpx.ConnectError("conexión rechazada", request=request)

    def slow(request):
        raise httpx.ConnectTimeout("timeout", request=request)

    with pytest.raises(httpx.ConnectError):
        check_health("http://mock.test", client=_client(refuse))
    with pytest.raises(httpx.ConnectTimeout):
        check_health("http://mock.test", client=_client(slow))


@pytest.fixture
def local_health_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                body = b'{"status":"ok"}'  # cuerpo propio de la prueba, no del mock W1
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()

        def log_message(self, *args):  # silencio
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_check_health_contra_servidor_local(local_health_server):  # T-19
    assert check_health(local_health_server) == 200


def test_url_con_ruta_base_incorrecta_da_404(local_health_server):  # T-19 (negativo)
    assert check_health(local_health_server + "/otra-ruta") == 404


def test_check_health_puerto_cerrado():  # T-20
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    # el socket ya está cerrado: nadie escucha en ese puerto
    with pytest.raises(httpx.ConnectError):
        check_health(f"http://127.0.0.1:{port}", timeout=2.0)
