# testing_report.md

**Feature:** [H01] Preparación del entorno y línea base
**Rol:** Ingeniero de pruebas
**Fecha:** 2026-11-06

> **Estado global: NO EJECUTADO** (salvo lo indicado en la sección 10). Los resultados de las filas de la sección 3 son esperados, no observados. La persona que ejecute debe adjuntar la salida real de cada comando. No afirmo cobertura ni porcentaje alguno.

---

## 1. Alcance y supuestos declarados

H01 es preparación de entorno. No cambia `api/app/`, no añade endpoints ni persistencia, y el frontend solo cambia el valor de la URL del mock W1 en `environment.ts`. Por eso las pruebas verifican artefactos (`.env`, línea base, spec, `environment.ts`), la disponibilidad del mock y que el API no haya cambiado.

**Resolución de B-1 (opción a del Chapter).** Las comprobaciones de H01 **no** están en `api/tests/`. Viven en `api/h01_checks/`, con nombre `check_*.py`, y no entran en la suite permanente de la API:

- `pytest tests/` y `python tools/lab.py test api` no las recogen (no están en `tests/`).
- `pytest` sin argumentos desde `api/` tampoco, porque su nombre no cumple `test_*.py`. Se ejecutan nombrando los archivos de forma explícita (sección 5).
- `api/tests/` queda sin archivos nuevos ni modificados. Coincide con el supuesto 7 del Arquitecto y la verificación 7 del Backend.
- La ruta `api/h01_checks/` se publica con el mapeo existente `api/` → `api/` de `crew/publish_pr.py`, sin cambiar `PATH_MAP`.

**Supuestos (cada prueba que depende de uno lo cita):**

| # | Supuesto |
|---|---|
| S1 | Las comprobaciones viven en `api/h01_checks/` (fuera de `api/tests/`) y se ejecutan desde `api/` nombrando los archivos `check_h01_*.py`. La raíz del repositorio es `Path(__file__).parents[2]`, y puede sobrescribirse con `H01_REPO_ROOT`. |
| S2 | `.env` está en la raíz de `wallet-app-g6`, no se versiona y está en `.gitignore`. El `.gitignore` actual ya incluye `.env` y `.env.*` con la excepción `!.env.example`. |
| S3 | `environment.ts` está en `src/environments/environment.ts`. Se desconoce el nombre de su propiedad, por lo que la prueba busca la URL como literal entre comillas en cualquier propiedad. |
| S4 | La línea base se registra en `openspec/changes/registro-activacion-wallet/baseline.md` con la plantilla del Backend (campos "Fecha y hora de ejecución", "Código de salida" y "Resultado (pasa / falla)"). |
| S5 | Las preguntas abiertas de la spec se marcan con alguno de estos tokens: `[PENDIENTE]`, `[ABIERTA]`, `NEEDS CLARIFICATION`, `TBD`, `TODO` o `PREGUNTA ABIERTA`. `TBD` y `TODO` solo se detectan en mayúsculas ("todo" es una palabra común en español). Una pregunta está cerrada solo si existe una línea del tema con `Responsable: <nombre o rol>` (distinto de "por designar" o "pendiente") y `Fecha: AAAA-MM-DD`. Si la spec usa otro formato, hay que ajustar `PENDING_MARKERS` y `DECISION_*_RE` en `h01_support.py`. |
| S6 | `GET /health` del mock devuelve `200` sin autenticación. El cuerpo es desconocido y no se verifica. |
| S7 | La URL del mock es desconocida. Se entrega como variable obligatoria `MOCK_W1_URL`, validada (http/https con host, sin credenciales, query ni fragmento). Si falta o es inválida, la prueba **falla**, no se omite. |
| S8 | H01 es de preparación y aún no hay código de producto: `api/app` no existe en la base. T-26 exige que siga sin existir. Si existiera en la base, T-26 importa `app.main:app` desde `api/` y comprueba `/openapi.json` y una ruta inexistente. |
| S9 | `httpx` está instalado, porque `TestClient` de Starlette lo requiere. H01 no actualiza dependencias. |
| S10 | Las correcciones SEC-06, SEC-07 y SEC-08 del informe de Seguridad están **aplicadas** en el código de `api/h01_checks/` y cubiertas por T-35 a T-38. |
| S11 | No hay subidas de archivos en H01. El aislamiento con `tmp_path`/`monkeypatch` se usa para las raíces de repositorio simuladas, `H01_REPO_ROOT`, `H01_BASE_REF`, `MOCK_W1_URL` y el directorio actual. |
| S12 | `python tools/verify.py` **no** se invoca desde pytest (riesgo de recursión). Se ejecuta como comando manual y se registra (criterio 1.2). Como las comprobaciones de H01 no están en `api/tests/`, `tools/verify.py` y `python tools/lab.py test api` las ignoran y la línea base de 1.2 sigue siendo "antes del cambio". |
| S13 | No se modifican pruebas existentes ni se añade nada a `api/tests/`. Los archivos nuevos son `api/h01_checks/h01_support.py`, `check_h01_support_logic.py`, `check_h01_guardrails.py` y `check_h01_change_state.py`. |

**Contratos de API y persistencia:**
- H01 no define contrato nuevo.
- El único endpoint es `GET /health` del mock (T-19 a T-21).
- Persistencia: no hay SQL ni migración. La guarda T-25 comprueba que no aparezcan archivos `.sql` o de migración nuevos.
- Los cambios en `schemas.py` y `services.py` quedan cubiertos por el diff de `api/app` (T-22).

---

## 2. Orden de ejecución y regla de línea base

**Fase 1: línea base** (versión actual, antes de aplicar el cambio). La línea base de 1.2 es la suite existente más `python tools/verify.py`. Las comprobaciones de H01 no forman parte de esa medición.

- Las pruebas de `check_h01_support_logic.py` y `check_h01_guardrails.py` deben pasar en la línea base. Si una falla, se corrige la prueba o se descarta, y **no se atribuye al cambio**.
- Las pruebas de `check_h01_change_state.py` verifican artefactos que aún pueden no existir en la línea base: `.env`, `baseline.md` rellenado, spec cerrada, URL fijada. Si fallan por ese motivo, se registran como "pendiente de aplicar el cambio". No son regresión ni defecto de la prueba. Son pruebas de **fase 2**: T-17, T-18, T-21, T-27 a T-30 y T-33.
- Cualquier fallo de la suite existente en la línea base se documenta como preexistente en `baseline.md` y no se corrige en H01.
- Un resultado `skipped` cuenta como NO cumplido. Las pruebas no usan `skip`, `xfail` ni variables opcionales: si falta un dato (`MOCK_W1_URL`), fallan.

**Fase 2: pruebas del cambio.** Se ejecutan tras aplicar 1.1 a 1.4. Deben pasar las tres suites de `api/h01_checks/` y la suite existente debe dar el mismo resultado que en la línea base.

**Después del merge:** `check_h01_change_state.py` y las guardas con `git diff` contra `H01_BASE_REF` pierden sentido. Son comprobaciones de la historia, no de la suite permanente. Pueden retirarse de `api/h01_checks/` en un PR posterior sin tocar `api/tests/`.

---

## 3. Trazabilidad criterio → prueba → resultado esperado → estado

Cada ID aparece una sola vez, con su archivo y su fase. Los archivos están en `api/h01_checks/`. "Lógica" es `check_h01_support_logic.py`; "guardas" es `check_h01_guardrails.py`; "estado del cambio" es `check_h01_change_state.py`.

| Criterio | ID | Prueba | Fase y tipo | Resultado esperado | Estado |
|---|---|---|---|---|---|
| **Línea base** | T-01 | Suite existente: `python tools/lab.py test api` | Fase 1, línea base | Resultado desconocido. Se registra tal cual en `baseline.md`; los fallos preexistentes no son del cambio. | NO EJECUTADO |
| **1.1** `.env` con las 3 variables | T-02 | `test_env_valido_sin_problemas` (lógica) | Fase 1, positivo | `validate_env` devuelve lista vacía. | NO EJECUTADO |
| 1.1 | T-03 | `test_env_variable_ausente` (lógica) | Fase 1, negativo | Reporta `CREWAI_INCLUDE_DATA` ausente. | NO EJECUTADO |
| 1.1 | T-04 | `test_env_valor_distinto` (lógica) | Fase 1, negativo | Reporta valor incorrecto de `PR_REPO`. | NO EJECUTADO |
| 1.1 | T-05 | `test_env_comillas_y_espacios_finales_no_validos` (lógica) | Fase 1, borde | `"true"`, `true ` y `True` se rechazan, igual que el `grep` con anclas. | NO EJECUTADO |
| 1.1 | T-06 | `test_env_crlf_comentarios_y_lineas_vacias` (lógica) | Fase 1, borde | CRLF, comentarios y líneas vacías se toleran; una variable comentada no cuenta. | NO EJECUTADO |
| 1.1 | T-07 | `test_env_duplicados_y_secretos` (lógica) | Fase 1, negativo | Duplicado y `GITHUB_TOKEN` se reportan. | NO EJECUTADO |
| 1.1 | T-08 | `test_env_valor_con_igual` (lógica) | Fase 1, borde | `PR_REPO=a=b` se reporta como valor incorrecto. | NO EJECUTADO |
| 1.1 | T-09 | `test_repo_root_respeta_override_y_lee_env_aislado` (lógica) | Fase 1, aislamiento | `repo_root()` devuelve `tmp_path` con `H01_REPO_ROOT` y no toca el `.env` real. | NO EJECUTADO |
| 1.1 | T-37 | `test_env_mensajes_no_exponen_el_valor` (lógica) | Fase 1, seguridad (SEC-07) | Con `PR_REPO=ghp_FAKE123456`, ningún mensaje contiene el valor y se reporta "valor con aspecto de secreto". | NO EJECUTADO |
| 1.1 | T-17 | `test_env_real_tiene_las_tres_variables_exactas` (estado del cambio) | **Fase 2**, positivo, repo real | `.env` real sin problemas (incluye comprobación de secretos por clave y por valor). | NO EJECUTADO |
| 1.1 | T-18 | `test_env_real_no_versionado` (estado del cambio) | **Fase 2**, seguridad | `git check-ignore .env` devuelve 0 y `git ls-files --error-unmatch .env` falla. | NO EJECUTADO |
| **1.2** Línea base registrada | T-10 | `test_baseline_md_rellenado_es_valido` (lógica) | Fase 1, positivo | Sin problemas con fecha, código y resultado coherentes. | NO EJECUTADO |
| 1.2 | T-11 | `test_baseline_plantilla_sin_rellenar_se_rechaza` (lógica) | Fase 1, negativo | Detecta `<RELLENAR>`. | NO EJECUTADO |
| 1.2 | T-12 | `test_baseline_incoherente_o_sin_fecha` (lógica) | Fase 1, borde | Código `0` con "falla", código `1` con "pasa" y fecha ausente se rechazan. | NO EJECUTADO |
| 1.2 | T-27 | `test_baseline_md_real_rellenado` (estado del cambio) | **Fase 2**, repo real | `baseline.md` real sin placeholders y coherente. | NO EJECUTADO |
| 1.2 (manual) | M-1 | `python tools/verify.py; echo $?` (sección 5) | Fase 1, línea base | Desconocido; la salida real se pega en `baseline.md`. | NO EJECUTADO |
| **1.3** Seis preguntas cerradas | T-13 | `test_spec_sin_marcadores_pendientes_y_con_los_seis_temas` (lógica) | Fase 1, positivo | Sin marcadores y con una decisión con responsable y fecha por cada uno de los 6 temas. | NO EJECUTADO |
| 1.3 | T-14 | `test_spec_con_pendientes_o_tema_faltante` (lógica) | Fase 1, negativo | Reporta el marcador y el tema sin decisión. | NO EJECUTADO |
| 1.3 | T-39 | `test_spec_tema_mencionado_pero_abierto_falla` (lógica) | Fase 1, negativo (OBS-02) | Un tema mencionado sin responsable, con "por designar" o sin fecha se reporta como no cerrado. | NO EJECUTADO |
| 1.3 | T-15 | `test_tasks_parseo` (lógica) | Fase 1, borde | Detecta `[ ]`, `[x]` y `[X]`. | NO EJECUTADO |
| 1.3 | T-28 | `test_spec_real_cierra_las_seis_preguntas` (estado del cambio) | **Fase 2**, repo real (depende de S5) | Sin marcadores pendientes y 6 temas con responsable y fecha. | NO EJECUTADO |
| 1.3 | T-29 | `test_tasks_1_1_a_1_4_marcadas` (estado del cambio) | **Fase 2**, positivo | Las 4 tareas del grupo 1 en `[x]`. | NO EJECUTADO |
| **1.4** Mock responde | T-16 | `test_check_health_*` con `MockTransport` (lógica) | Fase 1, positivo/negativo/borde | `200`→200; `503`→503; `ConnectError` y timeout se propagan; URL con `/` final pide `/health` exactamente. | NO EJECUTADO |
| 1.4 | T-19 | `test_check_health_contra_servidor_local` y `test_url_con_ruta_base_incorrecta_da_404` (lógica) | Fase 1, integración | `200` contra servidor local propio; `404` con ruta base errónea. Valida el procedimiento, no el mock. | NO EJECUTADO |
| 1.4 | T-20 | `test_check_health_puerto_cerrado` (lógica) | Fase 1, negativo | `httpx.ConnectError` (o `ConnectTimeout` en Windows). Equivale al `curl` con código 7. | NO EJECUTADO |
| 1.4 | T-31 | `test_get_mock_url_exige_variable` (lógica) | Fase 1, negativo | Sin `MOCK_W1_URL`, `AssertionError`. | NO EJECUTADO |
| 1.4 | T-32 | `test_environment_ts_coincidencia_exacta` (lógica) | Fase 1, borde | `…:3000` no coincide con `…:30001`; la barra final se tolera. | NO EJECUTADO |
| 1.4 | T-38 | `test_get_mock_url_rechaza_urls_inseguras` (lógica) | Fase 1, seguridad (SEC-08) | Credenciales, query, fragmento, esquema distinto de http(s) o ausencia de esquema se rechazan. | NO EJECUTADO |
| 1.4 | T-21 | `test_mock_w1_responde_200_en_health` (estado del cambio) | **Fase 2**, mock real | `check_health(MOCK_W1_URL) == 200`. Falla, no se omite, si falta la variable. | NO EJECUTADO |
| 1.4 | T-30 | `test_url_del_mock_fijada_en_environment_ts` (estado del cambio) | **Fase 2**, positivo | La URL verificada aparece como literal en `environment.ts`. | NO EJECUTADO |
| 1.4 | T-33 | `test_diff_frontend_limitado_a_environment_ts` (estado del cambio) | **Fase 2**, integración | Dentro de `src/` solo cambia `src/environments/environment.ts`. | NO EJECUTADO |
| **Alcance** (sin cambios en API ni persistencia) | T-22 | `test_archivos_protegidos_sin_diff` (guardas) | Fase 1, integración | Sin diff en `api/app`, `api/requirements.txt` y `tools/verify.py`. | NO EJECUTADO |
| Alcance | T-23 | `test_pruebas_existentes_no_modificadas` (guardas) | Fase 1, integración | Ningún archivo de `api/tests/` modificado, borrado, renombrado ni añadido. | NO EJECUTADO |
| Alcance (B-1) | T-34 | `test_sin_pruebas_h01_en_api_tests` (guardas) | Fase 1, integración | Ningún archivo con `h01` en el nombre dentro de `api/tests/`. | NO EJECUTADO |
| Alcance | T-24 | `test_sin_archivos_nuevos_en_api_app` (guardas) | Fase 1, integración | Sin archivos sin rastrear ni añadidos en `api/app`. | NO EJECUTADO |
| Alcance (persistencia) | T-25 | `test_sin_sql_ni_migraciones_nuevas` (guardas) | Fase 1, integración | Sin `.sql` ni migraciones nuevos. | NO EJECUTADO |
| Alcance (contrato API) | T-26 | `test_api_responde_sin_escribir_en_cwd` (guardas) | Fase 1, integración | Sin `api/app` en la base: sigue sin existir. Con `api/app` en la base: `/openapi.json` →200, ruta inexistente →404, cwd (`tmp_path`) sigue vacío; si OpenAPI se deshabilita fuera de desarrollo, ajustar esta aserción (OBS-11). | NO EJECUTADO |
| Seguridad (SEC-06) | T-35 | `test_base_ref_rechaza_opciones_de_git` (lógica) | Fase 1, seguridad | `H01_BASE_REF='--output=/tmp/h01_pwned'` lanza `ValueError` y no ejecuta git con esa opción. | NO EJECUTADO |
| Seguridad (SEC-06) | T-36 | `test_base_ref_resuelve_sha_y_rechaza_refs_inexistentes` (lógica) | Fase 1, seguridad | Con un repositorio temporal, `base_ref()` devuelve un SHA de 40 caracteres; una referencia inexistente lanza `ValueError`. | NO EJECUTADO |

---

## 4. Preparación y datos de prueba

**Preparación (una vez):**
1. Partir de `wallet-app-g6` con el entorno virtual del API activo (con `pytest`, `httpx` y `fastapi`).
2. Capturar la referencia base antes de aplicar el cambio. Si el cambio ya está aplicado en el árbol de trabajo, usar el commit previo al cambio. `H01_BASE_REF` solo admite nombres de referencia git (sin prefijo `-`); se resuelve a un SHA.
3. Tener a mano la URL del mock W1 (local o del grupo). Es un dato pendiente.

```bash
cd wallet-app-g6
export H01_BASE_REF="$(git rev-parse HEAD)"   # commit base (ver nota arriba)
export MOCK_W1_URL="<URL_REAL_DEL_MOCK_W1>"   # dato pendiente: http(s)://host[:puerto], sin credenciales
```

**Datos de prueba:**

| Dato | Valor | Uso |
|---|---|---|
| `.env` válido | `GITHUB_OWNER=user-bcp-student04`, `PR_REPO=wallet-app-g6`, `CREWAI_INCLUDE_DATA=true` | T-02, T-17 |
| `.env` inválidos | faltante, valor distinto, entre comillas, espacio final, duplicado, `GITHUB_TOKEN=x`, `PR_REPO=a=b`, `PR_REPO=ghp_FAKE123456` | T-03 a T-08, T-37 |
| `baseline.md` de prueba | contenido generado en `tmp_path` (no es una ejecución real) | T-10 a T-12 |
| Spec de prueba | texto sintético con los seis temas: cerrados (responsable y fecha), con marcador y abiertos | T-13, T-14, T-39 |
| Servidor local | `http.server` en `127.0.0.1` con puerto efímero. Su cuerpo `{"status":"ok"}` es de la propia prueba y **no representa** al mock W1. | T-19 |
| Puerto cerrado | puerto efímero liberado antes de la petición | T-20 |
| URLs inválidas | con credenciales, con query, con fragmento, `ftp://`, sin esquema | T-38 |
| Repositorio git temporal | `git init` en `tmp_path` con un commit vacío | T-36 |

---

## 5. Comandos reproducibles

**Fase 1: línea base** (versión actual). Conservar la salida completa.

```bash
# 1. Suite existente vía laboratorio (no incluye las comprobaciones de H01)
python tools/lab.py test api

# 2. Equivalente directo y detallado; revisar que "skipped" sea 0
cd api
python -m pytest -rA -p no:cacheprovider tests/

# 3. Solo las comprobaciones de línea base de H01
python -m pytest -rA -p no:cacheprovider h01_checks/check_h01_support_logic.py h01_checks/check_h01_guardrails.py
cd ..

# 4. Línea base de verificación del repositorio (criterio 1.2, M-1); NO se invoca desde pytest (S12)
python tools/verify.py
echo "codigo_salida=$?"
```

Con la salida de 1 y 4 se rellena `baseline.md`: fecha, comando, código de salida, resultado y fallos preexistentes. Se registra un resumen (conteos, nombres de pruebas fallidas) y se revisa antes del commit (SEC-03).

**Fase 2: pruebas del cambio** (tras aplicar 1.1 a 1.4):

```bash
cd api
python -m pytest -rA -p no:cacheprovider h01_checks/check_h01_change_state.py
python -m pytest -rA -p no:cacheprovider tests/
cd ..
python tools/lab.py test api
```

**Comprobación del alcance de B-1 (NO EJECUTADO):**

```bash
cd api
python -m pytest --collect-only -q -p no:cacheprovider tests/ | grep -ci "h01"
# esperado: 0
python -m pytest --collect-only -q -p no:cacheprovider | grep -ci "h01"
# esperado: 0 (el nombre check_*.py no cumple el patrón de colección por defecto)
```

**Verificación manual complementaria del mock (M-2 y M-3):**

```bash
curl -i "$MOCK_W1_URL/health"          # esperado (no ejecutado): HTTP 200
curl -i http://localhost:59999/health  # puerto sin servicio; esperado: sin respuesta HTTP, código de salida 7 (típico)
echo "codigo_salida=$?"
```

**Criterio de aceptación de la ejecución:**
- 0 `failed`, 0 `error`, 0 `skipped` en `api/h01_checks/` en la fase 2.
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
git status --short   # esperado: solo los archivos del cambio y api/h01_checks/; nada en api/tests/
```

- `tmp_path` se limpia automáticamente por pytest, y el servidor local de T-19 se detiene en el `yield` del fixture.
- Si la persona levantó el mock W1 para la prueba, debe detenerlo.
- **No** se borra `.env` ni `baseline.md`, porque son entregables.

---

## 8. Código de las pruebas

El código completo está en la sección 11, con la ruta en la primera línea de cada bloque. Son archivos nuevos bajo `api/h01_checks/`; no se toca `api/tests/`.

| Archivo | Contenido |
|---|---|
| `api/h01_checks/h01_support.py` | Utilidades: lectura de `.env`, validación de la línea base y de la spec, `base_ref()` validada (SEC-06), mensajes sin valores de `.env` (SEC-07), validación de `MOCK_W1_URL` (SEC-08), `check_health`. |
| `api/h01_checks/check_h01_support_logic.py` | Lógica con datos sintéticos (fase 1). |
| `api/h01_checks/check_h01_guardrails.py` | Guardas de alcance sobre git y el API (fase 1). |
| `api/h01_checks/check_h01_change_state.py` | Estado real del cambio (fase 2). |

---

## 9. Qué no cubre este informe

- **Contenido de `tools/verify.py` y del mock W1:** no los he visto. T-21 depende de S6.
- **Cuerpo de `GET /health`:** desconocido. No se verifica.
- **Formato real de las decisiones en la spec:** T-28 asume una línea por tema con `Responsable:` y `Fecha:` (S5).
- **Resultados de la fase 2 y de las guardas contra el repositorio real:** ninguno hasta que una persona los ejecute y adjunte la salida real.

---

## 10. Ejecución parcial observada (entorno de desarrollo, no sustituye la ejecución humana)

- `check_h01_support_logic.py` en un entorno virtual temporal (Python 3.13, `pytest`, `httpx`, `fastapi`): 35 pruebas, todas pasan.
- `check_h01_guardrails.py` contra este repositorio (`H01_REPO_ROOT` en la raíz): 8 pasan, incluida T-26 (no existe `api/app`).
- `pytest` sin argumentos desde `api/`: 0 pruebas recogidas de `h01_checks/` (B-1 resuelto en colección por defecto).
- Evaluación de la spec real con `check_spec_text`: lista vacía; los seis temas de 1.3 tienen decisión con responsable y fecha (2026-11-06), de modo que T-28 debería pasar en la fase 2.
- Pendiente de ejecución humana: T-01, M-1, T-17, T-18, T-21, T-27, T-29, T-30 y T-33, que dependen de `.env`, `baseline.md`, `tasks.md` con 1.4 marcada, `environment.ts` y el mock real.

---

## 11. Código de las pruebas

```python
# api/h01_checks/h01_support.py
"""Utilidades de verificación para H01 (no es un archivo de pruebas).

Viven en api/h01_checks/, fuera de api/tests/: no entran en la suite permanente de la API.
Supuestos S1 a S12 del testing_report.md.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

import httpx

EXPECTED_ENV = {
    "GITHUB_OWNER": "user-bcp-student04",
    "PR_REPO": "wallet-app-g6",
    "CREWAI_INCLUDE_DATA": "true",
}
SECRET_KEY_RE = re.compile(r"(TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|PRIVATE)", re.IGNORECASE)
SECRET_VALUE_RE = re.compile(r"ghp_|github_pat_|-----BEGIN", re.IGNORECASE)

CHANGE_DIR = "openspec/changes/registro-activacion-wallet"
BASELINE_PATH = f"{CHANGE_DIR}/baseline.md"
SPEC_PATH = f"{CHANGE_DIR}/specs/wallet-onboarding/spec.md"
TASKS_PATH = f"{CHANGE_DIR}/tasks.md"
ENVIRONMENT_TS_PATH = "src/environments/environment.ts"

# S5: marcadores de pregunta abierta (ajustar si la spec usa otros).
# TBD y TODO distinguen mayúsculas: "todo" es una palabra común en español.
PENDING_MARKERS = re.compile(
    r"(?i:\[PENDIENTE\]|\[ABIERTA\]|NEEDS CLARIFICATION|PREGUNTA ABIERTA)|\bTBD\b|\bTODO\b"
)

SPEC_TOPICS = {
    "frontera de eventos": re.compile(r"frontera\s+de\s+eventos", re.IGNORECASE),
    "pasos adicionales al KYC simulado": re.compile(r"pasos\s+adicionales", re.IGNORECASE),
    "persistencia de eventos": re.compile(r"persistencia\s+de\s+eventos", re.IGNORECASE),
    "CORS del mock": re.compile(r"CORS", re.IGNORECASE),
    "usuario activo": re.compile(r"usuario\s+activo", re.IGNORECASE),
    "fuente de gasto de adquisición": re.compile(
        r"gasto\s+de\s+adquisici[oó]n", re.IGNORECASE
    ),
}
# Una decisión cerrada es una línea del tema con responsable nombrado y fecha AAAA-MM-DD.
DECISION_OWNER_RE = re.compile(r"Responsable:\s*(?!por designar|pendiente)\S", re.IGNORECASE)
DECISION_DATE_RE = re.compile(r"Fecha:\s*\d{4}-\d{2}-\d{2}", re.IGNORECASE)

_REF_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z._/~^@{}-]*")  # no puede empezar por '-'


# ---------------------------------------------------------------- raíz y git
def repo_root() -> Path:
    override = os.environ.get("H01_REPO_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[2]


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def base_ref() -> str:
    """SEC-06: valida H01_BASE_REF y devuelve el SHA resuelto (nunca el texto crudo)."""
    ref = os.environ.get("H01_BASE_REF", "HEAD")
    if not _REF_RE.fullmatch(ref):
        raise ValueError("H01_BASE_REF inválida")
    proc = run_git(repo_root(), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if proc.returncode != 0:
        raise ValueError("H01_BASE_REF no resuelve a un commit")
    return proc.stdout.strip()


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
    """SEC-07: los mensajes nunca incluyen el valor leído de .env."""
    problems: list[str] = []
    for key, expected in EXPECTED_ENV.items():
        if key not in values:
            problems.append(f"falta {key}")
        elif values[key] != expected:
            problems.append(f"valor incorrecto en {key} (longitud {len(values[key])})")
    for key in duplicates:
        problems.append(f"clave duplicada: {key}")
    for key, value in values.items():
        if SECRET_KEY_RE.search(key):
            problems.append(f"clave con aspecto de secreto: {key}")
        if SECRET_VALUE_RE.search(value):
            problems.append(f"valor con aspecto de secreto en {key}")
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
    """Exige, por cada tema de 1.3, una decisión con responsable nombrado y fecha."""
    problems = [f"marcador pendiente: {m.group(0)}" for m in PENDING_MARKERS.finditer(text)]
    lines = text.splitlines()
    for name, pattern in SPEC_TOPICS.items():
        closed = any(
            pattern.search(line) and DECISION_OWNER_RE.search(line) and DECISION_DATE_RE.search(line)
            for line in lines
        )
        if not closed:
            problems.append(f"sin decisión con responsable y fecha: {name}")
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
def validate_mock_url(url: str) -> None:
    """SEC-08: la URL termina en un archivo versionado y en el bundle del navegador."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise AssertionError("URL del mock inválida: se exige http(s) con host")
    if parts.username or parts.password:
        raise AssertionError("URL del mock con credenciales")
    if parts.query or parts.fragment:
        raise AssertionError("URL del mock con query o fragmento")


def get_mock_url() -> str:
    url = os.environ.get("MOCK_W1_URL", "").strip()
    if not url:
        raise AssertionError(
            "MOCK_W1_URL es obligatoria (URL local o del grupo del mock W1, sin /health). "
            "Defínela antes de ejecutar; esta prueba no se omite."
        )
    validate_mock_url(url)
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
# api/h01_checks/check_h01_support_logic.py
"""Línea base. Prueba la lógica de verificación de H01 con datos sintéticos.

Fuera de api/tests/: no se recogen con `pytest tests/` ni con `python tools/lab.py test api`.
Aislamiento: tmp_path (raíces de repositorio simuladas) y monkeypatch (variables de entorno).
Estas pruebas no leen el .env real ni el mock real.
"""
import socket
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

from h01_support import (
    BASELINE_PATH,
    base_ref,
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
OWNER_DATE = "Responsable: Líder técnico. Fecha: 2026-11-06."
ALL_TOPICS = (
    f"- Frontera de eventos: decidido. {OWNER_DATE}\n"
    f"- Pasos adicionales al KYC simulado: ninguno. {OWNER_DATE}\n"
    f"- Persistencia de eventos: en memoria. {OWNER_DATE}\n"
    f"- CORS del mock: origen de desarrollo. {OWNER_DATE}\n"
    f"- Usuario activo: definido. {OWNER_DATE}\n"
    f"- Fuente de gasto de adquisición: semilla. {OWNER_DATE}\n"
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


def test_env_mensajes_no_exponen_el_valor():  # T-37 (SEC-07)
    fake = "ghp_FAKE123456"
    problems = _problems(VALID_ENV.replace("PR_REPO=wallet-app-g6", f"PR_REPO={fake}"))
    assert any(p.startswith("valor incorrecto en PR_REPO") for p in problems)
    assert "valor con aspecto de secreto en PR_REPO" in problems
    assert not any(fake in p for p in problems)


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
    sin_cors = ALL_TOPICS.replace(f"- CORS del mock: origen de desarrollo. {OWNER_DATE}\n", "")
    assert "sin decisión con responsable y fecha: CORS del mock" in check_spec_text(sin_cors)


@pytest.mark.parametrize(
    "open_line",
    [
        "- Usuario activo: se define en otra historia.\n",
        "- Usuario activo: definido. Responsable: por designar. Fecha: 2026-11-06.\n",
        "- Usuario activo: definido. Responsable: Líder técnico.\n",
    ],
)
def test_spec_tema_mencionado_pero_abierto_falla(open_line):  # T-39 (OBS-02)
    text = ALL_TOPICS.replace(f"- Usuario activo: definido. {OWNER_DATE}\n", open_line)
    assert "sin decisión con responsable y fecha: usuario activo" in check_spec_text(text)


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


@pytest.mark.parametrize(
    "bad_url",
    [
        "http://usuario:clave@localhost:3000",
        "http://localhost:3000/?token=abc",
        "http://localhost:3000/#frag",
        "ftp://localhost:3000",
        "localhost:3000",
    ],
)
def test_get_mock_url_rechaza_urls_inseguras(monkeypatch, bad_url):  # T-38 (SEC-08)
    monkeypatch.setenv("MOCK_W1_URL", bad_url)
    with pytest.raises(AssertionError):
        get_mock_url()


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
    # el socket ya está cerrado: nadie escucha; Windows agota el tiempo en vez de rechazar
    with pytest.raises((httpx.ConnectError, httpx.ConnectTimeout)):
        check_health(f"http://127.0.0.1:{port}", timeout=2.0)


# ------------------------------------------------------ base_ref (SEC-06)
def test_base_ref_rechaza_opciones_de_git(monkeypatch):  # T-35
    monkeypatch.setenv("H01_BASE_REF", "--output=/tmp/h01_pwned")
    with pytest.raises(ValueError):
        base_ref()


def test_base_ref_resuelve_sha_y_rechaza_refs_inexistentes(tmp_path, monkeypatch):  # T-36
    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)

    git("init", "-q")
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "base")
    monkeypatch.setenv("H01_REPO_ROOT", str(tmp_path))
    monkeypatch.delenv("H01_BASE_REF", raising=False)
    assert len(base_ref()) == 40  # SHA resuelto, no el texto "HEAD"
    monkeypatch.setenv("H01_BASE_REF", "rama-que-no-existe")
    with pytest.raises(ValueError):
        base_ref()
```

```python
# api/h01_checks/check_h01_guardrails.py
"""Línea base. Comprueba que H01 no altera el API ni la persistencia (alcance del Arquitecto).

Fuera de api/tests/: no se recogen con `pytest tests/` ni con `python tools/lab.py test api`.
Requiere git en el PATH. H01_BASE_REF (por defecto HEAD) es el commit base y se valida (SEC-06).
Supuesto S8: si api/app existe en la base, app.main:app es importable con el directorio actual api/.
H01 es de preparación: si api/app aún no existe en la base, T-26 exige que siga sin existir.
"""
import pytest

from h01_support import base_ref, repo_root, run_git

PROTECTED = ["api/app", "api/requirements.txt", "tools/verify.py"]


def _git_lines(*args: str) -> list[str]:
    proc = run_git(repo_root(), *args)
    assert proc.returncode == 0, f"git {' '.join(args)} falló: {proc.stderr}"
    return [line for line in proc.stdout.splitlines() if line.strip()]


@pytest.mark.parametrize("path", PROTECTED)
def test_archivos_protegidos_sin_diff(path):  # T-22
    assert _git_lines("diff", "--name-only", base_ref(), "--", path) == []


def test_pruebas_existentes_no_modificadas():  # T-23
    # M=modificado, D=borrado, R=renombrado, A=añadido: api/tests/ no cambia en H01
    changed = _git_lines("diff", "--name-only", "--diff-filter=MDRA", base_ref(), "--", "api/tests")
    assert changed == []
    assert _git_lines("ls-files", "--others", "--exclude-standard", "--", "api/tests") == []


def test_sin_pruebas_h01_en_api_tests():  # T-34 (B-1)
    names = [p.name for p in (repo_root() / "api" / "tests").glob("*h01*")]
    assert names == []


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
    in_base = _git_lines("ls-tree", "-r", "--name-only", base_ref(), "--", "api/app")
    if not in_base:
        assert not (repo_root() / "api" / "app").exists(), "H01 no crea api/app"
        return

    from fastapi.testclient import TestClient
    from app.main import app  # importar antes de cambiar el directorio actual

    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/__ruta_inexistente_h01__").status_code == 404
    assert list(tmp_path.iterdir()) == []
```

```python
# api/h01_checks/check_h01_change_state.py
"""Comprobaciones del cambio H01 sobre el repositorio real (fase 2).

Fuera de api/tests/: no se recogen con `pytest tests/` ni con `python tools/lab.py test api`.
Se ejecutan a propósito (ver testing_report.md §5).
En la línea base pueden fallar legítimamente por artefactos aún no creados
(.env, baseline.md rellenado, spec cerrada, URL fijada). Eso no es regresión.
Ninguna prueba usa skip: si falta MOCK_W1_URL, falla.
"""
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


def test_env_real_no_versionado():  # T-18
    root = repo_root()
    # la comprobación de secretos por clave y por valor ya vive en read_env_problems (T-17)
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
