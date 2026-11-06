# api/tests/h01_support.py
"""Utilidades de verificación para H01 (no es un archivo de pruebas).

Supuestos S1 a S12 del testing_report.md.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import httpx

EXPECTED_ENV = {
    "GITHUB_OWNER": "user-bcp-student04",
    "PR_REPO": "wallet-app-g6",
    "CREWAI_INCLUDE_DATA": "true",
}
SECRET_KEY_RE = re.compile(r"(TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|PRIVATE)", re.IGNORECASE)

CHANGE_DIR = "openspec/changes/registro-activacion-wallet"
BASELINE_PATH = f"{CHANGE_DIR}/baseline.md"
SPEC_PATH = f"{CHANGE_DIR}/specs/wallet-onboarding/spec.md"
TASKS_PATH = f"{CHANGE_DIR}/tasks.md"
ENVIRONMENT_TS_PATH = "src/environments/environment.ts"

# S5: marcadores de pregunta abierta (ajustar si la spec usa otros)
PENDING_MARKERS = re.compile(
    r"\[PENDIENTE\]|\[ABIERTA\]|NEEDS CLARIFICATION|\bTBD\b|\bTODO\b|PREGUNTA ABIERTA",
    re.IGNORECASE,
)

SPEC_TOPICS = {
    "frontera de eventos": re.compile(r"frontera\s+de\s+eventos", re.IGNORECASE),
    "pasos adicionales al KYC simulado": re.compile(r"KYC", re.IGNORECASE),
    "persistencia de eventos": re.compile(r"persistencia\s+de\s+eventos", re.IGNORECASE),
    "CORS del mock": re.compile(r"CORS", re.IGNORECASE),
    "usuario activo": re.compile(r"usuario\s+activo", re.IGNORECASE),
    "fuente de gasto de adquisición": re.compile(
        r"gasto\s+de\s+adquisici[oó]n", re.IGNORECASE
    ),
}


# ---------------------------------------------------------------- raíz y git
def repo_root() -> Path:
    override = os.environ.get("H01_REPO_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[2]


def base_ref() -> str:
    return os.environ.get("H01_BASE_REF", "HEAD")


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


# ---------------------------------------------------------------------- .env
def parse_env_text(text: str) -> tuple[dict[str, str], list[str]]:
    """Parseo estricto: no recorta el valor ni quita comillas (igual que grep ^...$)."""
    values: dict[str, str] = {}
    duplicates: list[str] = []
    for raw in text.splitlines():
        line = raw.lstrip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key in values:
            duplicates.append(key)
        values[key] = value
    return values, duplicates


def validate_env(values: dict[str, str], duplicates: list[str]) -> list[str]:
    problems: list[str] = []
    for key, expected in EXPECTED_ENV.items():
        if key not in values:
            problems.append(f"falta {key}")
        elif values[key] != expected:
            problems.append(f"valor incorrecto en {key}: {values[key]!r} != {expected!r}")
    for key in duplicates:
        problems.append(f"clave duplicada: {key}")
    for key in values:
        if SECRET_KEY_RE.search(key):
            problems.append(f"clave con aspecto de secreto: {key}")
    return problems


def read_env_problems(root: Path) -> list[str]:
    path = root / ".env"
    if not path.is_file():
        return [".env no existe"]
    values, duplicates = parse_env_text(path.read_text(encoding="utf-8"))
    return validate_env(values, duplicates)


# ------------------------------------------------------------------ baseline
def check_baseline_text(text: str) -> list[str]:
    problems: list[str] = []
    if "<RELLENAR>" in text:
        problems.append("quedan campos <RELLENAR>")
    if not re.search(r"Fecha[^:\n]*:\s*\d{4}-\d{2}-\d{2}", text):
        problems.append("falta fecha AAAA-MM-DD")
    code_match = re.search(r"^\W*C[oó]digo de salida\s*:\s*(-?\d+)\s*$", text, re.IGNORECASE | re.MULTILINE)
    result_match = re.search(
        r"^\W*Resultado[^:\n]*:\s*(pasa|falla)\s*$", text, re.IGNORECASE | re.MULTILINE
    )
    if not code_match:
        problems.append("falta código de salida numérico")
    if not result_match:
        problems.append("falta resultado (pasa/falla)")
    if code_match and result_match:
        code = int(code_match.group(1))
        result = result_match.group(1).lower()
        if (code == 0) != (result == "pasa"):
            problems.append(f"incoherente: código {code} con resultado {result}")
    return problems


# ---------------------------------------------------------------------- spec
def check_spec_text(text: str) -> list[str]:
    problems = [f"marcador pendiente: {m.group(0)}" for m in PENDING_MARKERS.finditer(text)]
    for name, pattern in SPEC_TOPICS.items():
        if not pattern.search(text):
            problems.append(f"tema ausente en la spec: {name}")
    return problems


def parse_tasks(text: str) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for m in re.finditer(r"^\s*-\s*\[( |x|X)\]\s+(\d+\.\d+)\b", text, re.MULTILINE):
        result[m.group(2)] = m.group(1).lower() == "x"
    return result


# -------------------------------------------------------------- environment.ts
def url_in_environment_ts(text: str, url: str) -> bool:
    wanted = url.rstrip("/")
    literals = re.findall(r"""['"`](https?://[^'"`\s]+)['"`]""", text)
    return any(lit.rstrip("/") == wanted for lit in literals)


# --------------------------------------------------------------------- health
def get_mock_url() -> str:
    url = os.environ.get("MOCK_W1_URL", "").strip()
    assert url, (
        "MOCK_W1_URL es obligatoria (URL local o del grupo del mock W1, sin /health). "
        "Defínela antes de ejecutar; esta prueba no se omite."
    )
    return url


def check_health(base_url: str, client: httpx.Client | None = None, timeout: float = 5.0) -> int:
    """Devuelve el código HTTP de GET {base_url}/health. Los errores de red se propagan."""
    url = base_url.rstrip("/") + "/health"
    own_client = client is None
    client = client or httpx.Client(timeout=timeout)
    try:
        return client.get(url).status_code
    finally:
        if own_client:
            client.close()
