# testing_report.md

**Feature:** [H01] Validación final del cambio, tarea 4.1: `python tools/verify.py`
**Elaborado:** 2026-11-06T15:12:00-05:00
**Estado global: NO EJECUTADO.** No he ejecutado ningún comando ni prueba. Cada columna "Estado" dice NO EJECUTADO hasta que una persona adjunte la salida real. Este informe no afirma cobertura ni resultados.

---

## 1. Alcance y qué se prueba

El Issue pide ejecutar `python tools/verify.py` y registrar el resultado (CA-1). No define endpoints ni persistencia, y no recibí el contenido de `spec.md` ni el de `tools/verify.py`. Por eso:

1. **Ejecución y registro (CA-1).** No puedo automatizar la ejecución de `verify.py` dentro de pytest. Podría ser recursivo si `verify.py` llama a `lab.py test api`, y su contenido es desconocido (P2). Se ejecuta por comando con salida real adjunta, y pytest valida el registro en `tasks.md`.
2. **Base transversal opcional del Backend** (`api/app/config.py`, `errors.py`, `middleware.py`, `main.py`). Es el único código nuevo entregado. Se prueban su contrato de errores (`{"code","message"}`), el límite de cuerpo y la ausencia de fugas y de escrituras en disco.
3. **Correcciones de Seguridad.** No recibí una entrega del rol Seguridad, así que no invento hallazgos. Pruebo las medidas que sí constan en Arquitectura y Backend:
   - mensajes sin trazas ni valores recibidos;
   - límite de tamaño;
   - dependencias fijadas con `==`, incluido `starlette`.

---

## 2. Supuestos de las pruebas

| ID | Supuesto | Si es falso |
|---|---|---|
| ST1 | Las pruebas viven en `api/tests/`, y la raíz del repo es `Path(__file__).parents[2]`. | Las pruebas de contrato de la línea base fallan, y se corrige la ruta en la prueba. |
| ST2 | La base del Backend (sección B de `backend_spec.md`) está aplicada, o hay archivos equivalentes con los mismos nombres y firmas: `app.config._int_env`, `MAX_BODY_BYTES`, `app.errors.register_error_handlers`, `app.middleware.BodySizeLimitMiddleware(app, max_bytes)`, `app.main.app`. | Los archivos `test_h01_errors/body_limit/config/integration_main` no aplican y se descartan por escrito (no se marcan como skip). No se cuentan para ningún criterio. |
| ST3 | `python tools/lab.py test api` ejecuta pytest sobre `api/tests/`. No está confirmado. | Se usa el comando directo `cd api && python -m pytest tests`. |
| ST4 | No hay endpoints en el Issue. Las pruebas construyen apps FastAPI locales con rutas de prueba (`/ok`, `/raise/{status}`, `/items`, `/raw`, `/json`, `/boom`). Solo `GET /ruta-inexistente` se prueba contra `app.main.app`. | n/a |
| ST5 | No hay directorio de subidas ni persistencia. No invento `UPLOAD_DIR`. Uso `tmp_path` y `monkeypatch` (`chdir`, `HOME`, variables de entorno) para aislar el entorno y comprobar que no se escribe en disco. | n/a |
| ST6 | `verify.py` se ejecuta desde la raíz sin argumentos, y el código de salida 0 significa éxito (S2). | Se ajusta la ejecución cuando se conteste P2. |
| ST7 | La prueba de registro de `tasks.md` está fuera de `api/tests/` (en `openspec/changes/registro-activacion-wallet/tests/`). Así `lab.py test api` no la recoge en la línea base, donde 4.1 aún no está registrada. Se ejecuta explícitamente en la fase 2. | Se mueve. |
| ST8 | Python ≥ 3.10 (la base del Backend usa `dict[str, str] \| None`). Están instalados `pytest` y `httpx` (necesario para `TestClient`). Sus versiones las fija el manifiesto existente del repo; aquí no las invento. | n/a |
| ST9 | **Discrepancia de plantilla.** La plantilla de 4.1 marca siempre `[x]`, mientras que S4 dice que un fallo no se marca como éxito. La prueba implementa: `[x]` ⇔ `Resultado: APROBADO`, y `FALLIDO` ⇒ `[ ]`. Se confirma con P8. | Se ajusta una sola aserción (`test_estado_marca_coherente_con_resultado`). |
| ST10 | El resumen de la salida del registro va en una línea o como referencia a un log. La prueba lee solo las líneas sangradas contiguas a 4.1. | n/a |

**Regla sobre skip:** ninguna prueba usa `skip`, `skipif` ni `xfail`. Un skip cuenta como NO cumplido. El criterio de aceptación de las pruebas es 0 skipped y 0 failed.

**Hallazgo de defecto vs. fallo de prueba.** Si una prueba falla en la línea base por un error de la prueba (ruta, nombre), se corrige o se descarta. Si falla por un defecto real del código entregado (por ejemplo del middleware), se reporta como hallazgo a Backend. No se debilita la aserción ni se atribuye al cambio del Issue.

**Riesgo a observar (hipótesis, no verificada).** Según mi lectura de FastAPI, un cuerpo JSON con Pydantic en `chunked` podría convertir la excepción interna del middleware en 400 en lugar de 413. La prueba `test_json_chunked_excede_limite_413` lo comprobará. Si da 400, es un hallazgo para Backend, no un error de la prueba.

---

## 3. Trazabilidad: criterio → prueba → resultado esperado → estado

| Criterio | Prueba | Resultado esperado | Estado |
|---|---|---|---|
| **CA-1a.** Se ejecuta `python tools/verify.py` | T-V01 (comando, §6 fase 2 paso 3) | Se obtiene el código de salida. Si es 0, APROBADO (S2). Salida completa conservada. | NO EJECUTADO |
| **CA-1a.** Existen los artefactos de entrada | `test_h01_baseline_contract.py::test_verify_py_existe_y_compila`, `test_lab_py_existe`, `test_spec_existe` | Archivos presentes. `verify.py` compila sin ejecutarse. | NO EJECUTADO |
| **CA-1a.** La tarea 4.1 existe una sola vez en `tasks.md` | `test_h01_baseline_contract.py::test_tarea_4_1_existe_una_vez` | Exactamente una línea `- [ ] 4.1 …` o `- [x] 4.1 …`. | NO EJECUTADO |
| **CA-1b.** Se registra fecha/hora, comando, versión de Python, código de salida, resultado y resumen | `test_registro_4_1.py::test_campos_obligatorios_presentes`, `test_sin_placeholders`, `test_fecha_hora_iso_con_offset`, `test_comando_es_verify`, `test_version_python`, `test_codigo_salida_entero`, `test_resumen_no_vacio` | Seis campos presentes, sin `<…>`, formatos válidos. | NO EJECUTADO |
| **CA-1c.** Coherencia del registro (S2, S4) | `test_resultado_valido`, `test_resultado_coherente_con_codigo_salida`, `test_estado_marca_coherente_con_resultado` | `exit==0` ⇔ APROBADO. `[x]` ⇔ APROBADO. | NO EJECUTADO |
| **CC-1.** Contrato de error `{"code","message"}`, catálogo base | `test_h01_errors.py::test_http_exception_catalogo[400…413]`, `test_status_sin_mapeo`, `test_405_conserva_allow`, `test_401_conserva_www_authenticate` | Código HTTP y `code` según catálogo. Solo las claves `code` y `message`. | NO EJECUTADO |
| **CC-2.** 422 sin valores recibidos | `test_validacion_422_no_filtra_valor`, `test_validacion_422_campos_faltantes`, `test_validacion_422_query`, `test_validacion_422_json_invalido` | `INVALID_REQUEST`. Lista de campos (`body.qty`). El valor enviado no aparece. | NO EJECUTADO |
| **CC-3.** 500 genérico, sin trazas | `test_500_generico_sin_fuga`, `test_500_log_solo_tipo` | `INTERNAL_ERROR`. Sin `Traceback` ni texto de la excepción. El log solo contiene el tipo. | NO EJECUTADO |
| **CC-4.** Límite de cuerpo (Seguridad/Backend §4, §6) | `test_h01_body_limit.py` (positivo: `exacto_limite`, `cuerpo_vacio`; negativo: `limite_mas_uno`, `declarado_mayor`, `content_length_invalido[4]`; borde: `acumulado_multiples_chunks`, `content_length_falso`, `respuesta_ya_iniciada`, `scope_no_http`; `chunked`) | 200 en el límite. 413 `PAYLOAD_TOO_LARGE` por encima. 400 `BAD_REQUEST` con Content-Length inválido. La app no se invoca si el rechazo es previo. | NO EJECUTADO |
| **CC-5.** Configuración (`MAX_BODY_BYTES`) | `test_h01_config.py::test_int_env[8]`, `test_max_body_bytes_positivo`, `test_config_en_proceso_aislado_*` | Valores inválidos, 0 o negativos dan el default. Valores válidos se respetan. Defecto 1 048 576. | NO EJECUTADO |
| **CP-1.** Persistencia: la base no escribe en disco | `test_h01_integration_main.py::test_sin_escrituras_en_disco` | `tmp_path` vacío tras las peticiones. | NO EJECUTADO |
| **INT-1.** Integración `app.main` | `test_middleware_registrado`, `test_handlers_registrados`, `test_404_formato_unico`, `test_413_antes_del_router` | Middleware y handlers presentes. 404 con `{"code":"NOT_FOUND","message":"Recurso no encontrado."}`. 413 antes del enrutado. | NO EJECUTADO |
| **SEG-1.** Dependencias fijadas con `==`, incluido `starlette` (S7 Arquitecto) | `test_h01_requirements.py::test_todas_fijadas_con_igualdad`, `test_starlette_fijado`, `test_versiones_instaladas_coinciden`, `test_starlette_cumple_requisito_de_fastapi` | Sin rangos. Starlette fijado. El entorno instalado coincide con los pins y cumple el `Requires-Dist` de FastAPI. | NO EJECUTADO |
| **SEG-2.** Vulnerabilidades conocidas en pins (PyPI/OSV) | Procedimiento manual obligatorio (§6 fase 3 paso 12). **No es una prueba pytest opcional.** | `pip-audit` sin vulnerabilidades, o lista que se registra. | NO EJECUTADO |
| **REG-1.** Regresión: suite completa antes y después del registro | `python tools/lab.py test api` y `pytest api/tests` (fases 1 y 2) | 0 failed, 0 skipped, 0 errors en ambas. | NO EJECUTADO |
| **ALC-1.** Alcance: solo cambian `tasks.md` (y la base B si se adoptó) | `git diff --stat` (paso 11) | Sin cambios en `src/app/` (frontend), `package.json`, `angular.json`, ni en `tools/verify.py`. | NO EJECUTADO |

**Brechas declaradas (requieren aceptación humana):**
- No hay pruebas de endpoints de `wallet-onboarding` porque se desconoce su contrato (P1).
- No se sabe qué pruebas existentes cubren POST con cuerpo válido (P3).
- Qué comprueba `verify.py` es desconocido (P2). Su código de salida es la única evidencia, y no cubre lo que no verifique.
- No hay entrega de Seguridad (ver §1).

---

## 4. Casos por tipo

**Positivos**
- `/ok` responde 200 sin tocar el formato de error.
- Cuerpo exacto de `MAX` bytes → 200.
- Cuerpo vacío → 200.
- Registro 4.1 completo con `exit=0` ⇒ `[x]` y APROBADO.
- `MAX_BODY_BYTES=2048` válido se respeta.

**Negativos**
- Errores 400, 401, 403, 404, 409 y 413 vía `HTTPException`, sin reenviar `detail`.
- 405 y status sin mapeo.
- 422 por tipo inválido, campos faltantes, query inválida y JSON inválido.
- 500 por excepción no controlada.
- Cuerpo de `MAX+1` → 413.
- `Content-Length` declarado mayor que el límite → 413 sin invocar la app.
- `Content-Length` inválido (`abc`, `-1`, `1.5`, vacío) → 400.
- Registro con placeholders, campos ausentes o incoherentes.
- Dependencias sin `==`.

**Borde**
- Límite exacto, límite +1 y cuerpo vacío.
- Varios chunks cuya suma supera el límite.
- `Content-Length` falso (5 declarado, 200 reales).
- Excepción del límite cuando la respuesta ya inició (no se envía un segundo `start`).
- Scope `lifespan` delegado sin tocar.
- `MAX_BODY_BYTES` en blanco, no numérico, `0`, negativo y con espacios.
- Fecha con `Z` y con offset.

**Integración**
- `app.main.app` con middleware y handlers reales.
- Peticiones con `TestClient` sobre la app real (404 y 413 previos al router).
- Procesos aislados que importan `app.config` con y sin variable de entorno.
- Entorno instalado frente a `requirements.txt`.
- Registro en `tasks.md` frente al resultado real de `verify.py`.

---

## 5. Preparación, datos y supuestos de entorno

**Preparación** (desde la raíz del repo; Linux/macOS, bash):

```bash
# NO EJECUTADO
mkdir -p /tmp/h01_evidencia
git status --short | tee /tmp/h01_evidencia/00_git_status.txt
git rev-parse HEAD | tee /tmp/h01_evidencia/00_git_head.txt
python --version | tee /tmp/h01_evidencia/00_python_version.txt
# Entorno: usar el existente del repo. Si hace falta uno nuevo:
python -m venv .venv && source .venv/bin/activate
pip install -r api/requirements.txt          # o el manifiesto existente
pip install pytest httpx                     # versiones: las que fije el manifiesto de desarrollo del repo (no confirmado)
pip freeze | tee /tmp/h01_evidencia/00_pip_freeze.txt
pip check | tee /tmp/h01_evidencia/00_pip_check.txt
```

**Datos de prueba** (todos sintéticos, dentro de las pruebas):

| Dato | Uso |
|---|---|
| `MAX=100` bytes en las apps de prueba | Borde del límite |
| `b"x"*100`, `b"x"*101`, `b""` | Positivo, negativo y vacío |
| `Content-Length: abc / -1 / 1.5 / (vacío)` | 400 |
| `{"name":"x","qty":"valor-sensible-no-numerico"}` | 422 sin eco del valor |
| `RuntimeError("detalle-secreto /etc/passwd")` | 500 sin fuga |
| `HTTPException(detail="detalle-interno-secreto")` | No se reenvía `detail` |
| `MAX_BODY_BYTES ∈ {None,"","   ","abc","0","-5","2048"," 4096 "}` | Configuración |
| Bloque 4.1 sintético con `exit=0` y `exit=1` (solo para validar el parser, véase la nota del §6) | Registro |

---

## 6. Comandos reproducibles (en este orden)

Conserva la salida real de cada comando y adjúntala a este informe.

### Fase 1 — Línea base (versión actual, antes de registrar 4.1)

Incluye las pruebas existentes y las nuevas de `api/tests/` (ST2).

```bash
# NO EJECUTADO
# 1) Suite según el repositorio
python tools/lab.py test api 2>&1 | tee /tmp/h01_evidencia/10_lab_test_api_base.log
echo "exit=${PIPESTATUS[0]}" | tee -a /tmp/h01_evidencia/10_lab_test_api_base.log

# 2) pytest directo, mostrando skips y generando JUnit XML
cd api
python -m pytest tests -v -rsxX --junitxml=/tmp/h01_evidencia/11_pytest_base.xml 2>&1 | tee /tmp/h01_evidencia/11_pytest_base.log
echo "exit=${PIPESTATUS[0]}" | tee -a /tmp/h01_evidencia/11_pytest_base.log
cd ..

# 3) Verificación explícita de 0 skipped / 0 xfailed
grep -Ei "skipped|xfail|xpass" /tmp/h01_evidencia/11_pytest_base.log || echo "sin skips/xfail en la salida"
```

Criterio de aceptación: `exit=0` en ambos, 0 failed, 0 errors, 0 skipped. Fallos:
- Por error de la prueba (ruta o nombre): se corrige o se descarta, y no se atribuye al cambio.
- Por defecto real del código: se reporta como hallazgo a Backend.

### Fase 2 — Cambio (tarea 4.1)

```bash
# NO EJECUTADO
# 4) Fecha/hora y versión
date --iso-8601=seconds | tee /tmp/h01_evidencia/20_fecha.txt
python --version | tee /tmp/h01_evidencia/20_python.txt

# 5) Ejecutar verify.py desde la raíz (T-V01)
python tools/verify.py 2>&1 | tee /tmp/h01_evidencia/21_verify.log
echo "exit=${PIPESTATUS[0]}" | tee -a /tmp/h01_evidencia/21_verify.log
```

6. Una persona edita `tasks.md` con la plantilla de Arquitectura/Backend (§9), usando valores reales de los pasos 4 y 5. Si `exit != 0`, aplica S4/ST9: `- [ ] 4.1 …` con `Resultado: FALLIDO`.

```bash
# NO EJECUTADO
# 7) Validar el registro
python -m pytest openspec/changes/registro-activacion-wallet/tests/test_registro_4_1.py -v -rsxX \
  2>&1 | tee /tmp/h01_evidencia/22_pytest_registro.log

# 8) Regresión tras el cambio (repetir pasos 1 y 2)
python tools/lab.py test api 2>&1 | tee /tmp/h01_evidencia/23_lab_test_api_post.log
cd api && python -m pytest tests -v -rsxX 2>&1 | tee /tmp/h01_evidencia/24_pytest_post.log; cd ..
```

**Nota sobre el parser del registro.** La prueba de 4.1 valida el `tasks.md` real. No incluye casos sintéticos con `exit=0`/`exit=1`. Si se quiere probar el parser con ambos, hay que añadir pruebas de parser aparte y no se ha hecho (no hay aserciones de ese tipo).

### Fase 3 — Alcance y seguridad

```bash
# NO EJECUTADO
# 11) El cambio solo toca tasks.md (y api/app + api/tests + api/requirements.txt si se adoptó la base B)
git diff --stat | tee /tmp/h01_evidencia/30_diff_stat.txt
git diff --name-only -- src package.json angular.json tools/verify.py | tee /tmp/h01_evidencia/31_no_tocados.txt
# Esperado: 31_no_tocados.txt vacío

# 12) SEG-2: vulnerabilidades en pins (requiere red; OBLIGATORIO si se adopta api/requirements.txt)
pip install pip-audit
pip-audit -r api/requirements.txt 2>&1 | tee /tmp/h01_evidencia/32_pip_audit.log
echo "exit=${PIPESTATUS[0]}" | tee -a /tmp/h01_evidencia/32_pip_audit.log
# Esperado: exit=0 y "No known vulnerabilities found".
# Si hay vulnerabilidades, registrar IDs (OSV/PyPI) y fecha de consulta; decide una persona.
```

Si no hay red para el paso 12, el criterio SEG-2 queda NO CUMPLIDO. No se sustituye por otra comprobación.

### Limpieza

```bash
# NO EJECUTADO — solo después de archivar /tmp/h01_evidencia
# (cp -r /tmp/h01_evidencia <destino de evidencia acordado en P4>)
rm -rf /tmp/h01_evidencia
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
rm -rf api/.pytest_cache .pytest_cache
# Si se creó venv de prueba:
deactivate 2>/dev/null; rm -rf .venv
git status --short   # solo deben quedar los cambios previstos
```

`tmp_path` lo borra pytest. Las pruebas no escriben fuera de él. Los cambios de `monkeypatch` (`chdir`, `HOME`, variables de entorno) se deshacen solos al terminar cada prueba.

---

## 7. Preguntas pendientes que afectan a las pruebas

- **P2:** qué comprueba `verify.py` y qué necesita. Si ya ejecuta `lab.py test api`, la fase 1 y la 2 paso 8 son redundantes pero no dañinas.
- **P4:** dónde se archiva la evidencia además de `tasks.md`.
- **P8 / ST9:** si un fallo de `verify.py` bloquea el cierre, y cómo se marca 4.1 en ese caso.
- **ST2:** si la base B se adopta o ya existe una equivalente con otras firmas.
- **Seguridad:** falta su entrega. Si se aporta, se añade una fila a la trazabilidad por cada corrección propuesta.

---

# Código de las pruebas

```python
# api/tests/test_h01_baseline_contract.py
"""Línea base H01: los artefactos de entrada de la tarea 4.1 existen y son coherentes.

No ejecuta tools/verify.py (su contenido es desconocido y podría ser recursivo).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHANGE = ROOT / "openspec" / "changes" / "registro-activacion-wallet"
TASKS = CHANGE / "tasks.md"
SPEC = CHANGE / "specs" / "wallet-onboarding" / "spec.md"
VERIFY = ROOT / "tools" / "verify.py"
LAB = ROOT / "tools" / "lab.py"

LINEA_4_1 = re.compile(
    r"^- \[[ xX]\] 4\.1 Ejecutar `python tools/verify\.py` y registrar el resultado\s*$",
    re.MULTILINE,
)


def test_verify_py_existe_y_compila():
    assert VERIFY.is_file(), f"No existe {VERIFY}"
    source = VERIFY.read_text(encoding="utf-8")
    compile(source, str(VERIFY), "exec")  # solo sintaxis; no se ejecuta


def test_lab_py_existe():
    assert LAB.is_file(), f"No existe {LAB}"


def test_spec_existe():
    assert SPEC.is_file(), f"No existe {SPEC}"


def test_tarea_4_1_existe_una_vez():
    assert TASKS.is_file(), f"No existe {TASKS}"
    text = TASKS.read_text(encoding="utf-8")
    matches = LINEA_4_1.findall(text)
    assert len(matches) == 1, (
        "La tarea 4.1 debe aparecer exactamente una vez; "
        f"encontradas: {len(matches)}"
    )
```

```python
# api/tests/test_h01_errors.py
"""Contrato de errores {"code","message"} (catálogo base de Arquitectura/Backend).

Usa una app FastAPI local con rutas de prueba (el Issue no define endpoints).
"""
import logging

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.errors import register_error_handlers


class Item(BaseModel):
    name: str
    qty: int


def _build_app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/raise/{status}")
    def raise_status(status: int):
        raise HTTPException(status_code=status, detail="detalle-interno-secreto")

    @app.get("/raise-401-header")
    def raise_401_header():
        raise HTTPException(
            status_code=401,
            detail="detalle-interno-secreto",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.get("/boom")
    def boom():
        raise RuntimeError("detalle-secreto /etc/passwd")

    @app.get("/q")
    def q(limit: int = 1):
        return {"limit": limit}

    @app.post("/items")
    def items(item: Item):
        return {"name": item.name, "qty": item.qty}

    return app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Aislamiento: ninguna prueba debe depender ni escribir en el cwd real.
    monkeypatch.chdir(tmp_path)
    return TestClient(_build_app(), raise_server_exceptions=False)


def _assert_error_shape(resp, status, code):
    assert resp.status_code == status
    body = resp.json()
    assert set(body.keys()) == {"code", "message"}
    assert body["code"] == code
    assert isinstance(body["message"], str) and body["message"]


def test_ruta_ok_no_se_ve_afectada(client):
    resp = client.get("/ok")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@pytest.mark.parametrize(
    "status,code,message",
    [
        (400, "BAD_REQUEST", "Solicitud incorrecta."),
        (401, "UNAUTHENTICATED", "Identidad no proporcionada."),
        (403, "FORBIDDEN", "Acceso denegado."),
        (404, "NOT_FOUND", "Recurso no encontrado."),
        (409, "CONFLICT", "Conflicto con el estado actual del recurso."),
        (413, "PAYLOAD_TOO_LARGE", "El cuerpo excede el tamaño permitido."),
    ],
)
def test_http_exception_catalogo(client, status, code, message):
    resp = client.get(f"/raise/{status}")
    _assert_error_shape(resp, status, code)
    assert resp.json()["message"] == message
    # El detail arbitrario de la excepción no se reenvía al cliente.
    assert "detalle-interno-secreto" not in resp.text


def test_status_sin_mapeo(client):
    resp = client.get("/raise/418")
    _assert_error_shape(resp, 418, "ERROR")
    assert resp.json()["message"] == "Error en la solicitud."
    assert "detalle-interno-secreto" not in resp.text


def test_405_conserva_allow(client):
    resp = client.post("/ok")
    _assert_error_shape(resp, 405, "METHOD_NOT_ALLOWED")
    assert resp.json()["message"] == "Método no permitido."
    assert "GET" in resp.headers.get("allow", "")


def test_401_conserva_www_authenticate(client):
    resp = client.get("/raise-401-header")
    _assert_error_shape(resp, 401, "UNAUTHENTICATED")
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_validacion_422_no_filtra_valor(client):
    resp = client.post(
        "/items", json={"name": "x", "qty": "valor-sensible-no-numerico"}
    )
    _assert_error_shape(resp, 422, "INVALID_REQUEST")
    assert "body.qty" in resp.json()["message"]
    assert "valor-sensible-no-numerico" not in resp.text


def test_validacion_422_campos_faltantes(client):
    resp = client.post("/items", json={})
    _assert_error_shape(resp, 422, "INVALID_REQUEST")
    message = resp.json()["message"]
    assert "body.name" in message
    assert "body.qty" in message


def test_validacion_422_query(client):
    resp = client.get("/q", params={"limit": "abc"})
    _assert_error_shape(resp, 422, "INVALID_REQUEST")
    assert "query.limit" in resp.json()["message"]
    assert "abc" not in resp.json()["message"]


def test_validacion_422_json_invalido(client):
    resp = client.post(
        "/items",
        content="esto-no-es-json",
        headers={"Content-Type": "application/json"},
    )
    _assert_error_shape(resp, 422, "INVALID_REQUEST")
    assert "esto-no-es-json" not in resp.text


def test_500_generico_sin_fuga(client):
    resp = client.get("/boom")
    assert resp.status_code == 500
    assert resp.json() == {
        "code": "INTERNAL_ERROR",
        "message": "Error interno del servidor.",
    }
    assert "Traceback" not in resp.text
    assert "secreto" not in resp.text
    assert "/etc/passwd" not in resp.text


def test_500_log_solo_tipo(client, caplog):
    caplog.set_level(logging.ERROR, logger="app.errors")
    client.get("/boom")
    messages = [r.getMessage() for r in caplog.records if r.name == "app.errors"]
    assert any("RuntimeError" in m for m in messages)
    assert not any("secreto" in m for m in messages)
```

```python
# api/tests/test_h01_body_limit.py
"""Límite de bytes del cuerpo (BodySizeLimitMiddleware).

Dos niveles: TestClient sobre una app local, y llamadas ASGI directas para los
casos que un cliente HTTP real no puede construir (Content-Length inválido).
"""
import asyncio
import json

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.errors import register_error_handlers
from app.middleware import BodySizeLimitMiddleware

MAX = 100
MSG_413 = {
    "code": "PAYLOAD_TOO_LARGE",
    "message": "El cuerpo excede el tamaño permitido.",
}


class Payload(BaseModel):
    text: str


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX)
    register_error_handlers(app)

    @app.post("/raw")
    async def raw(request: Request):
        data = await request.body()
        return {"size": len(data)}

    @app.post("/json")
    async def js(p: Payload):
        return {"len": len(p.text)}

    return app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return TestClient(_build_app(), raise_server_exceptions=False)


# ------------------------- Nivel TestClient -------------------------

def test_cuerpo_exacto_limite_es_aceptado(client):
    resp = client.post("/raw", content=b"x" * MAX)
    assert resp.status_code == 200
    assert resp.json() == {"size": MAX}


def test_cuerpo_vacio_es_aceptado(client):
    resp = client.post("/raw", content=b"")
    assert resp.status_code == 200
    assert resp.json() == {"size": 0}


def test_cuerpo_limite_mas_uno_413(client):
    resp = client.post("/raw", content=b"x" * (MAX + 1))
    assert resp.status_code == 413
    assert resp.json() == MSG_413
    assert resp.headers["content-type"].startswith("application/json")


def test_json_declarado_excede_limite_413(client):
    body = json.dumps({"text": "a" * 200}).encode("utf-8")
    resp = client.post(
        "/json", content=body, headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 413
    assert resp.json() == MSG_413


def test_raw_chunked_excede_limite_413(client):
    def chunks():
        yield b"x" * 60
        yield b"y" * 60

    resp = client.post("/raw", content=chunks())
    assert resp.status_code == 413
    assert resp.json() == MSG_413


def test_json_chunked_excede_limite_413(client):
    # RIESGO A OBSERVAR (hipótesis, no verificada): FastAPI podría envolver la
    # excepción interna del middleware como 400 al parsear un cuerpo JSON.
    # Un 400 aquí es un hallazgo para Backend, no un error de la prueba.
    body = json.dumps({"text": "a" * 200}).encode("utf-8")

    def chunks():
        yield body[:80]
        yield body[80:]

    resp = client.post(
        "/json", content=chunks(), headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 413
    assert resp.json() == MSG_413


# ------------------------- Nivel ASGI directo -------------------------

def _scope(headers=None, scope_type="http"):
    return {
        "type": scope_type,
        "method": "POST",
        "path": "/x",
        "headers": headers or [],
    }


async def _drive(mw, scope, chunks):
    sent = []
    queue = list(chunks)

    async def receive():
        if queue:
            body = queue.pop(0)
            return {"type": "http.request", "body": body, "more_body": bool(queue)}
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    await mw(scope, receive, send)
    return sent


def _reader_app(calls, start_first=False):
    async def app(scope, receive, send):
        calls.append(scope["type"])
        if scope["type"] != "http":
            return
        if start_first:
            await send({"type": "http.response.start", "status": 200, "headers": []})
        more = True
        while more:
            msg = await receive()
            more = msg.get("more_body", False)
        if not start_first:
            await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    return app


def _body_of(sent):
    return json.loads(sent[1]["body"].decode("utf-8"))


@pytest.mark.parametrize("raw", [b"abc", b"-1", b"1.5", b""])
def test_content_length_invalido_400_sin_invocar_app(raw):
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls), max_bytes=MAX)
    sent = asyncio.run(_drive(mw, _scope([(b"content-length", raw)]), []))
    assert sent[0]["status"] == 400
    assert _body_of(sent) == {
        "code": "BAD_REQUEST",
        "message": "Content-Length inválido.",
    }
    assert calls == []


def test_content_length_declarado_mayor_413_sin_invocar_app():
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls), max_bytes=MAX)
    sent = asyncio.run(
        _drive(mw, _scope([(b"content-length", str(MAX + 1).encode())]), [])
    )
    assert sent[0]["status"] == 413
    assert _body_of(sent) == MSG_413
    assert calls == []


def test_rechazo_incluye_content_length_y_connection_close():
    mw = BodySizeLimitMiddleware(_reader_app([]), max_bytes=MAX)
    sent = asyncio.run(
        _drive(mw, _scope([(b"content-length", b"9999")]), [])
    )
    headers = dict(sent[0]["headers"])
    assert headers[b"content-type"] == b"application/json"
    assert headers[b"connection"] == b"close"
    assert int(headers[b"content-length"]) == len(sent[1]["body"])


def test_declarado_igual_al_limite_con_cuerpo_exacto_pasa():
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls), max_bytes=MAX)
    sent = asyncio.run(
        _drive(mw, _scope([(b"content-length", str(MAX).encode())]), [b"x" * MAX])
    )
    assert sent[0]["status"] == 200
    assert calls == ["http"]


def test_acumulado_multiples_chunks_413():
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls), max_bytes=MAX)
    sent = asyncio.run(_drive(mw, _scope(), [b"x" * 60, b"x" * 60]))
    assert sent[0]["status"] == 413
    assert _body_of(sent) == MSG_413
    assert calls == ["http"]  # la app se invocó; el conteo real cortó


def test_content_length_falso_se_detecta_por_conteo_real():
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls), max_bytes=MAX)
    sent = asyncio.run(
        _drive(mw, _scope([(b"content-length", b"5")]), [b"x" * 200])
    )
    assert sent[0]["status"] == 413
    assert _body_of(sent) == MSG_413


def test_respuesta_ya_iniciada_no_se_duplica():
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls, start_first=True), max_bytes=MAX)
    sent = asyncio.run(_drive(mw, _scope(), [b"x" * 200]))
    starts = [m for m in sent if m["type"] == "http.response.start"]
    assert len(starts) == 1
    assert starts[0]["status"] == 200  # no se superpone un 413


def test_scope_no_http_se_delega_sin_tocar():
    calls = []
    mw = BodySizeLimitMiddleware(_reader_app(calls), max_bytes=MAX)
    sent = asyncio.run(_drive(mw, _scope(scope_type="lifespan"), []))
    assert calls == ["lifespan"]
    assert sent == []
```

```python
# api/tests/test_h01_config.py
"""Configuración MAX_BODY_BYTES: valores por defecto, inválidos y válidos."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from app import config

API_DIR = Path(__file__).resolve().parents[1]
DEFAULT = 1_048_576
VAR = "MAX_BODY_BYTES"


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, DEFAULT),
        ("", DEFAULT),
        ("   ", DEFAULT),
        ("abc", DEFAULT),
        ("0", DEFAULT),
        ("-5", DEFAULT),
        ("2048", 2048),
        (" 4096 ", 4096),
    ],
)
def test_int_env(monkeypatch, raw, expected):
    if raw is None:
        monkeypatch.delenv(VAR, raising=False)
    else:
        monkeypatch.setenv(VAR, raw)
    assert config._int_env(VAR, DEFAULT) == expected


def test_max_body_bytes_positivo():
    assert isinstance(config.MAX_BODY_BYTES, int)
    assert config.MAX_BODY_BYTES > 0


def _run_config(env_value):
    env = dict(os.environ)
    env.pop(VAR, None)
    if env_value is not None:
        env[VAR] = env_value
    env["PYTHONPATH"] = str(API_DIR)
    out = subprocess.run(
        [sys.executable, "-c", "from app import config; print(config.MAX_BODY_BYTES)"],
        cwd=str(API_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert out.returncode == 0, out.stderr
    return int(out.stdout.strip())


def test_config_en_proceso_aislado_default():
    assert _run_config(None) == DEFAULT


def test_config_en_proceso_aislado_valor_valido():
    assert _run_config("2048") == 2048


def test_config_en_proceso_aislado_valor_invalido():
    assert _run_config("no-es-numero") == DEFAULT
```

```python
# api/tests/test_h01_integration_main.py
"""Integración sobre app.main.app: middleware, handlers y ausencia de escrituras."""
import pytest
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import config
from app.main import app as main_app
from app.middleware import BodySizeLimitMiddleware


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Aísla cwd y HOME: cualquier escritura relativa o en HOME caería en tmp_path.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    return TestClient(main_app, raise_server_exceptions=False)


def test_middleware_registrado():
    assert any(m.cls is BodySizeLimitMiddleware for m in main_app.user_middleware)


def test_handlers_registrados():
    handlers = main_app.exception_handlers
    assert StarletteHTTPException in handlers
    assert RequestValidationError in handlers
    assert Exception in handlers


def test_404_formato_unico(client):
    resp = client.get("/ruta-inexistente")
    assert resp.status_code == 404
    assert resp.json() == {
        "code": "NOT_FOUND",
        "message": "Recurso no encontrado.",
    }


def test_413_antes_del_router(client):
    # El middleware actúa antes del enrutado: una ruta inexistente con cuerpo
    # excesivo debe dar 413 y no 404.
    resp = client.post(
        "/ruta-inexistente", content=b"x" * (config.MAX_BODY_BYTES + 1)
    )
    assert resp.status_code == 413
    assert resp.json() == {
        "code": "PAYLOAD_TOO_LARGE",
        "message": "El cuerpo excede el tamaño permitido.",
    }


def test_sin_escrituras_en_disco(client, tmp_path):
    client.get("/ruta-inexistente")
    client.post("/ruta-inexistente", content=b"x" * (config.MAX_BODY_BYTES + 1))
    client.post("/ruta-inexistente", content=b"{}")
    assert list(tmp_path.iterdir()) == []
```

```python
# api/tests/test_h01_requirements.py
"""Dependencias: pins con ==, starlette fijado, entorno coherente (Seguridad/Arquitecto S7).

La consulta a PyPI/OSV es un procedimiento manual obligatorio (ver testing_report.md §6,
paso 12); no se modela como prueba opcional.
"""
import re
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement

REQ = Path(__file__).resolve().parents[1] / "requirements.txt"
PIN = re.compile(r"^([A-Za-z0-9_.\-]+)==([A-Za-z0-9_.+!\-]+)$")


def _lines():
    assert REQ.is_file(), f"No existe {REQ}"
    out = []
    for raw in REQ.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            out.append(line)
    assert out, "requirements.txt no contiene requisitos"
    return out


def _pins():
    pins = {}
    for line in _lines():
        m = PIN.match(line)
        assert m, f"Requisito no fijado con '==': {line!r}"
        pins[m.group(1).lower().replace("_", "-")] = m.group(2)
    return pins


def test_todas_fijadas_con_igualdad():
    assert _pins()


def test_starlette_fijado():
    assert "starlette" in _pins(), "starlette debe fijarse con == de forma explícita"


def test_versiones_instaladas_coinciden():
    mismatches = []
    for name, version in _pins().items():
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            mismatches.append(f"{name}: no instalado (pin {version})")
            continue
        if installed != version:
            mismatches.append(f"{name}: instalado {installed}, pin {version}")
    assert not mismatches, "; ".join(mismatches)


def test_starlette_cumple_requisito_de_fastapi():
    starlette_version = metadata.version("starlette")
    requisitos = metadata.requires("fastapi") or []
    checked = False
    for raw in requisitos:
        req = Requirement(raw)
        if req.name.lower() == "starlette" and req.marker is None:
            checked = True
            assert req.specifier.contains(starlette_version, prereleases=True), (
                f"starlette {starlette_version} no cumple {req.specifier} de fastapi"
            )
    assert checked, "fastapi no declara Requires-Dist de starlette sin marcador"
```

```python
# openspec/changes/registro-activacion-wallet/tests/test_registro_4_1.py
"""Fase 2 (cambio): valida el registro de la tarea 4.1 en tasks.md.

Se ejecuta explícitamente DESPUÉS de ejecutar tools/verify.py y registrar el
resultado. Está fuera de api/tests/ para no contaminar la línea base (ST7).
"""
import re
from datetime import datetime
from pathlib import Path

import pytest


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "tools" / "verify.py").is_file():
            return parent
    raise AssertionError("No se encontró la raíz del repo (tools/verify.py)")


TASKS = (
    _repo_root()
    / "openspec"
    / "changes"
    / "registro-activacion-wallet"
    / "tasks.md"
)

LINEA = re.compile(
    r"^- \[(?P<mark>[ xX])\] 4\.1 Ejecutar `python tools/verify\.py` "
    r"y registrar el resultado\s*$"
)
CAMPO = re.compile(
    r"^- (Fecha/hora|Comando|Versión de Python|Código de salida|Resultado|"
    r"Resumen de la salida):\s*(.*)$"
)
CAMPOS = [
    "Fecha/hora",
    "Comando",
    "Versión de Python",
    "Código de salida",
    "Resultado",
    "Resumen de la salida",
]


def _leer_registro():
    assert TASKS.is_file(), f"No existe {TASKS}"
    lines = TASKS.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        m = LINEA.match(line)
        if not m:
            continue
        note = []
        for nxt in lines[i + 1:]:
            if nxt.startswith("  ") and nxt.strip():
                note.append(nxt.strip())
            else:
                break
        fields = {}
        for n in note:
            c = CAMPO.match(n)
            if c:
                fields[c.group(1)] = c.group(2).strip()
        return m.group("mark"), fields
    raise AssertionError("No se encontró la línea de la tarea 4.1 en tasks.md")


@pytest.fixture(scope="module")
def registro():
    return _leer_registro()


def test_campos_obligatorios_presentes(registro):
    _, fields = registro
    faltan = [c for c in CAMPOS if c not in fields]
    assert not faltan, f"Faltan campos en el registro de 4.1: {faltan}"


def test_sin_placeholders(registro):
    _, fields = registro
    con_placeholder = {
        k: v for k, v in fields.items() if re.search(r"<[^>]+>", v)
    }
    assert not con_placeholder, f"Quedan placeholders sin rellenar: {con_placeholder}"


def test_fecha_hora_iso_con_offset(registro):
    _, fields = registro
    value = fields["Fecha/hora"].strip("`")
    assert re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)$", value
    ), f"Formato de fecha/hora inválido: {value!r}"
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_comando_es_verify(registro):
    _, fields = registro
    assert fields["Comando"].strip("`") == "python tools/verify.py"


def test_version_python(registro):
    _, fields = registro
    assert re.match(r"^`?Python \d+\.\d+\.\d+\S*`?$", fields["Versión de Python"]), (
        f"Versión de Python inválida: {fields['Versión de Python']!r}"
    )


def test_codigo_salida_entero(registro):
    _, fields = registro
    assert re.match(r"^`?-?\d+`?$", fields["Código de salida"]), (
        f"Código de salida no numérico: {fields['Código de salida']!r}"
    )


def test_resultado_valido(registro):
    _, fields = registro
    assert fields["Resultado"].strip("`") in {"APROBADO", "FALLIDO"}


def test_resumen_no_vacio(registro):
    _, fields = registro
    assert fields["Resumen de la salida"].strip("`").strip() != ""


def test_resultado_coherente_con_codigo_salida(registro):
    _, fields = registro
    codigo = int(fields["Código de salida"].strip("`"))
    resultado = fields["Resultado"].strip("`")
    # S2: 0 = éxito, cualquier otro valor = fallo.
    assert (codigo == 0) == (resultado == "APROBADO"), (
        f"Incoherencia: código de salida {codigo} con Resultado {resultado}"
    )


def test_estado_marca_coherente_con_resultado(registro):
    # ST9: [x] <=> APROBADO (S4: un fallo no se marca como completado con éxito).
    mark, fields = registro
    resultado = fields["Resultado"].strip("`")
    assert (mark in {"x", "X"}) == (resultado == "APROBADO"), (
        f"Marca [{mark}] incoherente con Resultado {resultado}"
    )
```