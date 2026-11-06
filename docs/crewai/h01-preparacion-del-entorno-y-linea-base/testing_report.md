# testing_report.md

**Feature:** [H01] Preparación del entorno y línea base
**Rol:** Ingeniero de pruebas
**Fecha:** 2026-11-06

> **Estado global: NO EJECUTADO.** No he ejecutado ningún comando ni prueba. Todos los resultados de este informe son esperados, no observados. La persona que ejecute debe adjuntar la salida real de cada comando. No afirmo cobertura ni porcentaje alguno.

---

## 1. Alcance y supuestos declarados

H01 es preparación de entorno. No cambia `api/app/`, no añade endpoints ni persistencia, y el frontend solo cambia el valor de la URL del mock W1 en `environment.ts`. Por eso las pruebas verifican artefactos (`.env`, línea base, spec, `environment.ts`), la disponibilidad del mock y que el API no haya cambiado.

**Supuestos (cada prueba que depende de uno lo cita):**

| # | Supuesto |
|---|---|
| S1 | Las pruebas viven en `api/tests/` y se ejecutan con `python tools/lab.py test api` o con `pytest` desde `api/`. La raíz del repositorio es `Path(__file__).parents[2]`, y puede sobrescribirse con `H01_REPO_ROOT`. |
| S2 | `.env` está en la raíz de `wallet-app-g6`, no se versiona y está en `.gitignore` (S1 del Arquitecto). |
| S3 | `environment.ts` está en `src/environments/environment.ts`. Se desconoce el nombre de su propiedad, por lo que la prueba busca la URL como literal entre comillas en cualquier propiedad. |
| S4 | La línea base se registra en `openspec/changes/registro-activacion-wallet/baseline.md` con la plantilla del Backend (campos "Fecha y hora de ejecución", "Código de salida" y "Resultado (pasa / falla)"). |
| S5 | Las preguntas abiertas de la spec se marcan con alguno de estos tokens: `[PENDIENTE]`, `[ABIERTA]`, `NEEDS CLARIFICATION`, `TBD`, `TODO` o `PREGUNTA ABIERTA`. Cerrar una pregunta significa que el token desaparece y el tema sigue tratado. **No he visto la spec.** Si usa otro marcador, hay que ajustar `PENDING_MARKERS` en `h01_support.py`. |
| S6 | `GET /health` del mock devuelve `200` sin autenticación. El cuerpo es desconocido y no se verifica. |
| S7 | La URL del mock es desconocida. Se entrega como variable obligatoria `MOCK_W1_URL`. Si falta, la prueba **falla**, no se omite. |
| S8 | `app.main:app` existe y es importable con el directorio actual `api/` (nombres de `backend_spec.md`). |
| S9 | `httpx` está instalado, porque `TestClient` de Starlette lo requiere. No he consultado versiones ni vulnerabilidades. H01 no actualiza dependencias. |
| S10 | No hay entrega de Seguridad en el contexto. No verifico "correcciones propuestas por Seguridad" como tales. Cubro solo lo derivable del Arquitecto: `.env` sin secretos y no versionado. La comprobación de CORS queda como complemento manual (sección 6). |
| S11 | No hay subidas de archivos en H01. El aislamiento con `tmp_path`/`monkeypatch` se usa para las raíces de repositorio simuladas, `H01_REPO_ROOT`, `MOCK_W1_URL` y el directorio actual. No invento un nombre de variable para el directorio de subidas. |
| S12 | `python tools/verify.py` **no** se invoca desde pytest. Su contenido es desconocido y podría ejecutar pytest de nuevo, lo que causaría recursión. Se ejecuta como comando manual y se registra (criterio 1.2). |
| S13 | No se modifican pruebas existentes. Todo lo nuevo son archivos nuevos: `h01_support.py`, `test_h01_support_logic.py`, `test_h01_guardrails.py` y `test_h01_change_state.py`. |

**Contratos de API y persistencia:**
- H01 no define contrato nuevo.
- El único endpoint es `GET /health` del mock (T-19 a T-21).
- Persistencia: no hay SQL ni migración. La guarda T-25 comprueba que no aparezcan archivos `.sql` o de migración nuevos.
- Los cambios en `schemas.py` y `services.py` quedan cubiertos por el diff de `api/app` (T-23).

---

## 2. Orden de ejecución y regla de línea base

**Fase 1: línea base** (versión actual, antes de aplicar el cambio). Se ejecuta la suite completa existente más las pruebas nuevas.

- Las pruebas de `test_h01_support_logic.py` y `test_h01_guardrails.py` deben pasar en la línea base. Si una falla, se corrige la prueba o se descarta, y **no se atribuye al cambio**.
- Las pruebas de `test_h01_change_state.py` verifican artefactos que aún pueden no existir en la línea base: `.env`, `baseline.md` rellenado, spec cerrada, URL fijada. Si fallan por ese motivo, se registran como "pendiente de aplicar el cambio". No son regresión ni defecto de la prueba.
- Cualquier fallo de la suite existente en la línea base se documenta como preexistente en `baseline.md` y no se corrige en H01.
- Un resultado `skipped` cuenta como NO cumplido. Las pruebas no usan `skip`, `xfail` ni variables opcionales: si falta un dato (`MOCK_W1_URL`), fallan.

**Fase 2: pruebas del cambio.** Se ejecutan tras aplicar 1.1 a 1.4. Deben pasar las tres suites nuevas y la suite existente debe dar el mismo resultado que en la línea base.

---

## 3. Trazabilidad criterio → prueba → resultado esperado → estado

| Criterio | ID | Prueba | Tipo | Resultado esperado | Estado |
|---|---|---|---|---|---|
| **Línea base** | T-01 | Suite existente: `python tools/lab.py test api` | Línea base | Resultado desconocido. Se registra tal cual en `baseline.md`; los fallos preexistentes no son del cambio. | NO EJECUTADO |
| Línea base | T-02 a T-18 | `test_h01_support_logic.py` (lógica de verificación con `tmp_path`, `monkeypatch`, `MockTransport` y servidor local) | Línea base / positivo, negativo, borde, integración | Todas pasan. | NO EJECUTADO |
| Línea base | T-22 a T-26 | `test_h01_guardrails.py` | Línea base / integración | Pasan: `api/app`, `requirements.txt` y `tools/verify.py` sin diff; pruebas existentes sin modificar; sin `.sql` nuevo; API responde sin escribir en el cwd. | NO EJECUTADO |
| **1.1** `.env` con las 3 variables | T-02 | `test_env_valido_sin_problemas` (lógica) | Positivo | `validate_env` devuelve lista vacía. | NO EJECUTADO |
| 1.1 | T-03 | `test_env_variable_ausente` | Negativo | Reporta `CREWAI_INCLUDE_DATA` ausente. | NO EJECUTADO |
| 1.1 | T-04 | `test_env_valor_distinto` | Negativo | Reporta valor incorrecto de `PR_REPO`. | NO EJECUTADO |
| 1.1 | T-05 | `test_env_comillas_y_espacios_finales_no_validos` | Borde | `"true"` y `true ` (con espacio) se rechazan, igual que el `grep` con anclas. | NO EJECUTADO |
| 1.1 | T-06 | `test_env_crlf_comentarios_y_lineas_vacias` | Borde | CRLF, comentarios y líneas vacías se toleran; una variable comentada no cuenta. | NO EJECUTADO |
| 1.1 | T-07 | `test_env_duplicados_y_secretos` | Negativo | Duplicado y `GITHUB_TOKEN` se reportan. | NO EJECUTADO |
| 1.1 | T-08 | `test_env_valor_con_igual` | Borde | `PR_REPO=a=b` se reporta como valor incorrecto. | NO EJECUTADO |
| 1.1 | T-09 | `test_repo_root_respeta_override` | Aislamiento | `repo_root()` devuelve `tmp_path` con `H01_REPO_ROOT` y no toca el `.env` real. | NO EJECUTADO |
| 1.1 | **T-17** | `test_env_real_tiene_las_tres_variables_exactas` (change_state) | Positivo, repo real | `.env` real sin problemas. | NO EJECUTADO |
| 1.1 | T-18 | `test_env_real_sin_secretos_y_no_versionado` (change_state) | Positivo/seguridad | `git check-ignore .env` devuelve 0 y `.env` no tiene claves de secreto. | NO EJECUTADO |
| **1.2** Línea base registrada | T-10 | `test_baseline_md_rellenado_es_valido` (lógica) | Positivo | Sin problemas con fecha, código y resultado coherentes. | NO EJECUTADO |
| 1.2 | T-11 | `test_baseline_plantilla_sin_rellenar_se_rechaza` | Negativo | Detecta `<RELLENAR>`. | NO EJECUTADO |
| 1.2 | T-12 | `test_baseline_incoherente_o_sin_fecha` | Borde | Código `0` con "falla", código `1` con "pasa" y fecha ausente se rechazan. | NO EJECUTADO |
| 1.2 | T-27 | `test_baseline_md_real_rellenado` (change_state) | Positivo, repo real | `baseline.md` real sin placeholders y coherente. | NO EJECUTADO |
| 1.2 (manual) | M-1 | `python tools/verify.py; echo $?` (sección 5) | Línea base | Desconocido; la salida real se pega en `baseline.md`. | NO EJECUTADO |
| **1.3** Seis preguntas cerradas | T-13 | `test_spec_sin_marcadores_pendientes_y_con_los_seis_temas` (lógica) | Positivo | Sin marcadores y con los 6 temas presentes. | NO EJECUTADO |
| 1.3 | T-14 | `test_spec_con_pendientes_o_tema_faltante` | Negativo | Reporta el marcador y el tema ausente. | NO EJECUTADO |
| 1.3 | T-28 | `test_spec_real_cierra_las_seis_preguntas` (change_state) | Positivo, repo real (depende de S5) | Sin marcadores pendientes y 6 temas presentes. | NO EJECUTADO |
| 1.3 | T-29 | `test_tasks_1_1_a_1_4_marcadas` (change_state) | Positivo | Las 4 tareas del grupo 1 en `[x]`. | NO EJECUTADO |
| 1.3 | T-15 | `test_tasks_parseo` (lógica) | Borde | Detecta `[ ]`, `[x]` y `[X]`. | NO EJECUTADO |
| **1.4** Mock responde | T-16 | `test_check_health_*` con `MockTransport` (lógica) | Positivo/negativo/borde | `200`→200; `503`→503; `ConnectError` y timeout se propagan; URL con `/` final pide `/health` exactamente. | NO EJECUTADO |
| 1.4 | T-19 | `test_check_health_contra_servidor_local` y `test_url_con_ruta_incorrecta_da_404` | Integración | `200` contra servidor local propio; `404` con ruta base errónea. Valida el procedimiento, no el mock. | NO EJECUTADO |
| 1.4 | T-20 | `test_check_health_puerto_cerrado` | Negativo, integración | `httpx.ConnectError`. Equivale al `curl` con código 7. | NO EJECUTADO |
| 1.4 | **T-21** | `test_mock_w1_responde_200_en_health` (change_state) | Integración, mock real | `check_health(MOCK_W1_URL) == 200`. Falla, no se omite, si falta la variable. | NO EJECUTADO |
| 1.4 | T-30 | `test_url_del_mock_fijada_en_environment_ts` | Positivo | La URL verificada aparece como literal en `environment.ts`. | NO EJECUTADO |
| 1.4 | T-31 | `test_get_mock_url_exige_variable` (lógica) | Negativo | Sin `MOCK_W1_URL`, `AssertionError`. | NO EJECUTADO |
| 1.4 | T-32 | `test_environment_ts_coincidencia_exacta` (lógica) | Borde | `…:3000` no coincide con `…:30001`; la barra final se tolera. | NO EJECUTADO |
| 1.4 | T-33 | `test_diff_frontend_limitado_a_environment_ts` (change_state) | Integración | Dentro de `src/` solo cambia `src/environments/environment.ts`. | NO EJECUTADO |
| **Alcance** (sin cambios en API ni persistencia) | T-22 | `test_archivos_protegidos_sin_diff` | Integración | Sin diff en `api/app`, `api/requirements.txt` y `tools/verify.py`. | NO EJECUTADO |
| Alcance | T-23 | `test_pruebas_existentes_no_modificadas` | Integración | Ningún archivo de `api/tests/` modificado, borrado o renombrado. | NO EJECUTADO |
| Alcance | T-24 | `test_sin_archivos_nuevos_en_api_app` | Integración | Sin archivos sin rastrear en `api/app`. | NO EJECUTADO |
| Alcance (persistencia) | T-25 | `test_sin_sql_ni_migraciones_nuevas` | Integración | Sin `.sql` ni migraciones nuevos. | NO EJECUTADO |
| Alcance (contrato API) | T-26 | `test_api_responde_sin_escribir_en_cwd` | Integración, TestClient | `/openapi.json` →200, ruta inexistente →404, cwd (`tmp_path`) sigue vacío. | NO EJECUTADO |

---

## 4. Preparación y datos de prueba

**Preparación (una vez):**
1. Partir de `wallet-app-g6` con el entorno virtual del API activo (con `pytest` y `httpx`).
2. Capturar la referencia base antes de aplicar el cambio. Si el cambio ya está aplicado en el árbol de trabajo, usar el commit previo al cambio.
3. Tener a mano la URL del mock W1 (local o del grupo). Es un dato pendiente.

```bash
cd wallet-app-g6
export H01_BASE_REF="$(git rev-parse HEAD)"   # commit base (ver nota arriba)
export MOCK_W1_URL="<URL_REAL_DEL_MOCK_W1>"   # dato pendiente: sustituir por la URL local o del grupo
```

**Datos de prueba:**

| Dato | Valor | Uso |
|---|---|---|
| `.env` válido | `GITHUB_OWNER=user-bcp-student04`, `PR_REPO=wallet-app-g6`, `CREWAI_INCLUDE_DATA=true` | T-02, T-17 |
| `.env` inválidos | faltante, valor distinto, entre comillas, espacio final, duplicado, `GITHUB_TOKEN=x`, `PR_REPO=a=b` | T-03 a T-08 |
| `baseline.md` de prueba | contenido generado en `tmp_path` (no es una ejecución real) | T-10 a T-12 |
| Spec de prueba | texto sintético con los seis temas, con y sin marcadores | T-13, T-14 |
| Servidor local | `http.server` en `127.0.0.1` con puerto efímero. Su cuerpo `{"status":"ok"}` es de la propia prueba y **no representa** al mock W1. | T-19 |
| Puerto cerrado | puerto efímero liberado antes de la petición | T-20 |

---

## 5. Comandos reproducibles

**Fase 1: línea base** (versión actual). Conservar la salida completa.

```bash
# 1. Suite completa vía laboratorio (incluye las pruebas nuevas si están en api/tests)
python tools/lab.py test api

# 2. Equivalente directo y detallado; revisar que "skipped" sea 0
cd api
python -m pytest -rA -p no:cacheprovider tests/
cd ..

# 3. Solo las pruebas nuevas de línea base
cd api
python -m pytest -rA -p no:cacheprovider tests/test_h01_support_logic.py tests/test_h01_guardrails.py
cd ..

# 4. Línea base de verificación del repositorio (criterio 1.2, M-1); NO se invoca desde pytest (S12)
python tools/verify.py
echo "codigo_salida=$?"
```

Con la salida de 1 y 4 se rellena `baseline.md`: fecha, comando, código de salida, resultado y fallos preexistentes.

**Fase 2: pruebas del cambio** (tras aplicar 1.1 a 1.4):

```bash
cd api
python -m pytest -rA -p no:cacheprovider tests/test_h01_change_state.py
python -m pytest -rA -p no:cacheprovider tests/
cd ..
python tools/lab.py test api
```

**Verificación manual complementaria del mock (M-2 y M-3):**

```bash
curl -i "$MOCK_W1_URL/health"          # esperado (no ejecutado): HTTP 200
curl -i http://localhost:59999/health  # puerto sin servicio; esperado: sin respuesta HTTP, código de salida 7 (típico)
echo "codigo_salida=$?"
```

**Criterio de aceptación de la ejecución:**
- 0 `failed`, 0 `error`, 0 `skipped` en los archivos nuevos de la fase 2.
- La suite existente da el mismo resultado que en la línea base.
- No afirmo cobertura. Medirla requeriría `pytest --cov` y su salida real.

---

## 6. Complementos manuales (no son criterios de aceptación)

- **CORS del mock:** la decisión 1.3 propone un origen concreto (`http://localhost:4200`, no confirmado) y no usar `*`. Hasta que se confirme el origen no automatizo una aserción. Comprobación manual sugerida:
  ```bash
  curl -i -H "Origin: http://localhost:4200" "$MOCK_W1_URL/health"
  ```
  Revisar que `Access-Control-Allow-Origin` no sea `*`. NO EJECUTADO.
- **Compilación del frontend** tras fijar la URL: `npm run build` (o `ng build`). El resultado es desconocido. NO EJECUTADO.

---

## 7. Limpieza

```bash
unset MOCK_W1_URL H01_BASE_REF H01_REPO_ROOT
find api -name "__pycache__" -type d -prune -exec rm -rf {} +
rm -rf api/.pytest_cache .pytest_cache
git status --short   # esperado: solo los archivos del cambio y las 4 pruebas nuevas
```

- `tmp_path` se limpia automáticamente por pytest, y el servidor local de T-19 se detiene en el `yield` del fixture.
- Si la persona levantó el mock W1 para la prueba, debe detenerlo.
- **No** se borra `.env` ni `baseline.md`, porque son entregables.

---

## 8. Código de las pruebas

```python
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
```

```python
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
```

```python
# api/tests/test_h01_guardrails.py
"""Línea base. Comprueba que H01 no altera el API ni la persistencia (alcance del Arquitecto).

Requiere git en el PATH. H01_BASE_REF (por defecto HEAD) es el commit base.
Supuesto S8: app.main:app es importable con el directorio actual api/.
"""
import pytest
from fastapi.testclient import TestClient

try:
    from h01_support import base_ref, repo_root, run_git
except ImportError:
    from tests.h01_support import base_ref, repo_root, run_git

PROTECTED = ["api/app", "api/requirements.txt", "tools/verify.py"]


def _git_lines(*args: str) -> list[str]:
    proc = run_git(repo_root(), *args)
    assert proc.returncode == 0, f"git {' '.join(args)} falló: {proc.stderr}"
    return [line for line in proc.stdout.splitlines() if line.strip()]


@pytest.mark.parametrize("path", PROTECTED)
def test_archivos_protegidos_sin_diff(path):  # T-22
    assert _git_lines("diff", "--name-only", base_ref(), "--", path) == []


def test_pruebas_existentes_no_modificadas():  # T-23
    # M=modificado, D=borrado, R=renombrado: las pruebas nuevas (A / sin rastrear) no cuentan
    changed = _git_lines("diff", "--name-only", "--diff-filter=MDR", base_ref(), "--", "api/tests")
    assert changed == []


def test_sin_archivos_nuevos_en_api_app():  # T-24
    assert _git_lines("ls-files", "--others", "--exclude-standard", "--", "api/app") == []
    assert _git_lines("diff", "--name-only", "--diff-filter=A", base_ref(), "--", "api/app") == []


def test_sin_sql_ni_migraciones_nuevas():  # T-25
    candidates = _git_lines("ls-files", "--others", "--exclude-standard", "--", "api")
    candidates += _git_lines("diff", "--name-only", "--diff-filter=A", base_ref(), "--", "api")
    offenders = [
        p for p in candidates
        if p.lower().endswith(".sql") or "migration" in p.lower() or "alembic" in p.lower()
    ]
    assert offenders == []


def test_api_responde_sin_escribir_en_cwd(tmp_path, monkeypatch):  # T-26
    from app.main import app  # importar antes de cambiar el directorio actual

    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/__ruta_inexistente_h01__").status_code == 404
    assert list(tmp_path.iterdir()) == []
```

```python
# api/tests/test_h01_change_state.py
"""Pruebas del cambio H01 sobre el repositorio real (fase 2).

En la línea base pueden fallar legítimamente por artefactos aún no creados
(.env, baseline.md rellenado, spec cerrada, URL fijada). Eso no es regresión.
Ninguna prueba usa skip: si falta MOCK_W1_URL, falla.
"""
try:
    from h01_support import (
        BASELINE_PATH,
        ENVIRONMENT_TS_PATH,
        SPEC_PATH,
        TASKS_PATH,
        base_ref,
        check_baseline_text,
        check_health,
        check_spec_text,
        get_mock_url,
        parse_env_text,
        parse_tasks,
        read_env_problems,
        repo_root,
        run_git,
        url_in_environment_ts,
    )
except ImportError:
    from tests.h01_support import (
        BASELINE_PATH,
        ENVIRONMENT_TS_PATH,
        SPEC_PATH,
        TASKS_PATH,
        base_ref,
        check_baseline_text,
        check_health,
        check_spec_text,
        get_mock_url,
        parse_env_text,
        parse_tasks,
        read_env_problems,
        repo_root,
        run_git,
        url_in_environment_ts,
    )


def _read(rel: str) -> str:
    path = repo_root() / rel
    assert path.is_file(), f"no existe {rel}"
    return path.read_text(encoding="utf-8")


# ----------------------------------------------------------------- 1.1
def test_env_real_tiene_las_tres_variables_exactas():  # T-17
    assert read_env_problems(repo_root()) == []


def test_env_real_sin_secretos_y_no_versionado():  # T-18
    root = repo_root()
    values, _ = parse_env_text(_read(".env"))
    assert not [k for k in values if "TOKEN" in k.upper() or "SECRET" in k.upper()]
    proc = run_git(root, "check-ignore", "-q", ".env")
    assert proc.returncode == 0, ".env no está ignorado por git (supuesto S2)"
    tracked = run_git(root, "ls-files", "--error-unmatch", ".env")
    assert tracked.returncode != 0, ".env está versionado"


# ----------------------------------------------------------------- 1.2
def test_baseline_md_real_rellenado():  # T-27
    assert check_baseline_text(_read(BASELINE_PATH)) == []


# ----------------------------------------------------------------- 1.3
def test_spec_real_cierra_las_seis_preguntas():  # T-28 (depende de S5)
    assert check_spec_text(_read(SPEC_PATH)) == []


def test_tasks_1_1_a_1_4_marcadas():  # T-29
    tasks = parse_tasks(_read(TASKS_PATH))
    for task_id in ("1.1", "1.2", "1.3", "1.4"):
        assert tasks.get(task_id) is True, f"tarea {task_id} no está marcada [x]"


# ----------------------------------------------------------------- 1.4
def test_mock_w1_responde_200_en_health():  # T-21
    assert check_health(get_mock_url()) == 200


def test_url_del_mock_fijada_en_environment_ts():  # T-30
    url = get_mock_url()
    assert url_in_environment_ts(_read(ENVIRONMENT_TS_PATH), url), (
        f"{url} no aparece como literal en {ENVIRONMENT_TS_PATH}"
    )


def test_diff_frontend_limitado_a_environment_ts():  # T-33
    root = repo_root()
    tracked = run_git(root, "diff", "--name-only", base_ref(), "--", "src")
    untracked = run_git(root, "ls-files", "--others", "--exclude-standard", "--", "src")
    assert tracked.returncode == 0, tracked.stderr
    assert untracked.returncode == 0, untracked.stderr
    changed = [p for p in (tracked.stdout + untracked.stdout).splitlines() if p.strip()]
    assert set(changed) <= {ENVIRONMENT_TS_PATH}, f"cambios fuera de environment.ts: {changed}"
```

---

## 9. Qué no cubre este informe

- **Contenido de `tools/verify.py`, de la spec y del mock W1:** no los he visto. T-28 depende de S5 y T-21 de S6.
- **Cuerpo de `GET /health`:** desconocido. No se verifica.
- **Correcciones de Seguridad:** no hay entrega de Seguridad en el contexto (S10).
- **Resultados:** ninguno. Hasta que una persona ejecute los comandos de la sección 5 y adjunte la salida real, todas las filas de la sección 3 permanecen en **NO EJECUTADO**.