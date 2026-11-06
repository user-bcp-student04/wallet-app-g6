# testing_report.md

**Feature:** [H01] Pruebas del onboarding (`registro-activacion-wallet`, grupo 3 de `tasks.md`)
**Fecha de redacción:** 2026-11-06
**Autor:** Ingeniero de pruebas

## 0. Estado global

**Nada de lo descrito aquí se ha ejecutado.** Todos los resultados son **esperados**, derivados de `backend_spec.md` y del código entregado por Backend. El estado de cada prueba es `NO EJECUTADO` hasta que una persona corra los comandos y adjunte la salida real (3.12). No afirmo cobertura, porcentaje de líneas ni número de pruebas. Ese número solo existirá en la salida real de `pytest`.

El Frontend entregó "Sin cambios". No dispongo de código ni de rutas del cliente Angular, así que **no escribo `*.spec.ts` con nombres inventados**. Los criterios que dependen del cliente quedan como casos diseñados, marcados `NO AUTOMATIZADO – BLOQUEADO` (sección 4.2). No se consideran cubiertos.

## 1. Supuestos declarados

| # | Supuesto | Si es falso |
|---|---|---|
| T-1 | Se prueba el API descrito en `backend_spec.md`: rutas, campos (`documentNumber`, `scenario`, `decision`, `status`, `decisionStatus`, `walletId`, `balances`, `verificationId`), códigos (`BAD_REQUEST`, `NOT_FOUND`, `DECISION_CONFLICT`, `PAYLOAD_TOO_LARGE`, `KYC_UNAVAILABLE`, `RATE_LIMITED`, `METHOD_NOT_ALLOWED`, `INTERNAL_ERROR`) y módulos (`app.main`, `app.config`, `app.repository`, `app.services`, `app.errors`). | Hay que reconciliar con el `schemas.py` real. Las diferencias son hallazgos, no se "arreglan" en la prueba. |
| T-2 | Existe `api/app/` con ese contenido. Si el repositorio ya tiene `api/app/` distinto, prevalece el código existente (A-1 de Backend). | Si no existe, la línea base no es ejecutable (ImportError): se registra como **bloqueo**, no como fallo de pruebas. |
| T-3 | Las pruebas nuevas van en `api/tests/onboarding/` con nombres únicos `test_h01_*.py`, para no colisionar con archivos existentes (`test_health.py`, `conftest.py`, etc.). Son archivos nuevos y no se toca ninguna aserción existente. Esto difiere de la propuesta plana de Arquitectura (S-1) únicamente para evitar colisiones. | Se pueden mover a `api/tests/` renombrando. |
| T-4 | No hay subida de archivos ni directorio de subidas en este feature (Backend §4 y §6). `tmp_path` y `monkeypatch` aíslan lo que sí existe: el directorio de trabajo (`monkeypatch.chdir(tmp_path)` + prueba de que no se escribe nada), las banderas de `app.config` y el estado en memoria. | Si el estado fuera en disco (P-1), hay que reevaluar. |
| T-5 | `python tools/lab.py test api` ejecuta `pytest` sobre `api/`. No conozco su contenido. Además se da el comando directo `cd api && python -m pytest ...`. | La persona debe confirmar qué hace `lab.py` y adjuntar su salida íntegra. |
| T-6 | `pytest` y `httpx` están instalables con `api/requirements-dev.txt` (P-9). Los pines `pytest==8.3.4` y `httpx==0.28.1` están **sin verificar** contra PyPI/OSV (A-11). | Ver sección 6.4. |
| T-7 | Las pruebas no usan `pytest-xdist` ni orden aleatorio. El estado en memoria se resetea por prueba (S-4). | En paralelo el almacén compartido dará fallos espurios. |
| T-8 | Seguridad: **no recibí su entrega** (no aparece en el contexto). No inventé sus correcciones. Verifico únicamente las medidas visibles en `backend_spec.md`: validación de ids y documento, límite de tamaño, errores sin trazas, reset desactivable y ausencia de campos internos. | Cuando exista la entrega de Seguridad, cada corrección se añade como caso en la sección 5. |
| T-9 | El prefijo `TEST-` se bloquea solo en el cliente (P-4). El servidor lo exige únicamente con `ENFORCE_TEST_DOC_PREFIX=true`. | Los dos casos del servidor están probados. |
| T-10 | Mediana con cantidad par = promedio de los dos centrales (S-5). Ubicación de eventos y mediana: desconocida (P-6). | Ver 4.2. |
| T-11 | Los tests de transporte (cuerpo *chunked* y `Content-Length` no numérico) dependen de cómo `TestClient` entrega la petición al ASGI. | Si fallan en la línea base se corrigen o se descartan con justificación (regla de línea base), no se atribuyen al cambio. |

## 2. Regla de ejecución: línea base primero

- **Línea base (Fase 1):** toda la suite del API, es decir las pruebas existentes más las nuevas `test_h01_*`, sobre la **versión actual** del repositorio, antes de aplicar cualquier otro cambio.
- **Cambio (Fase 2):** se ejecuta solo si hay algo que aplicar sobre la línea base (por ejemplo, el código de `backend_spec.md` si `api/app/` no existía, o `requirements-dev.txt`). Se repiten los mismos comandos y se compara contra la Fase 1.
- Una prueba que **falla en la línea base** se corrige (si el error es de la prueba) o se descarta con justificación escrita (si no es verificable). **No se atribuye al cambio.** Si el fallo evidencia un defecto del API, se registra como hallazgo (S-7) y no se modifica la lógica en este Issue.
- Como el cambio es solo de pruebas, es esperable que la Fase 2 no aporte diferencias. Si no hay nada que aplicar, la Fase 2 se marca "No aplica" con esa justificación.
- **Skip cuenta como NO cumplido.** Ninguna prueba nueva usa `skip`, `skipif`, `xfail` ni variables opcionales (`RUN_OSV=1` o similares). Criterio de salida: cero `SKIPPED`, `XFAIL` y `XPASS` en la salida (comando en 6.3).

## 3. Datos de prueba

| Dato | Valor | Uso |
|---|---|---|
| Documento válido | `TEST-0001` | Casos felices |
| Documento sin prefijo | `DOC-123` | Cliente bloquea; servidor lo acepta por defecto (T-9) |
| Documento en límite | `A` (1) y `TEST-` + 27×`A` (32) válidos; `TEST-` + 28×`A` (33) inválido | Borde |
| Documentos inválidos | `""`, `"   "`, `TEST 001`, `TEST-1'; DROP TABLE x;--`, `TEST-ñ`, `TEST-1\nX`, `12345` (número) | Negativos |
| Escenarios | `APPROVED`, `REJECTED`, `MANUAL_REVIEW`, `KYC_UNAVAILABLE` | Provocan 201 (x3) y 503 |
| Decisiones | `APPROVED`, `REJECTED` válidas; `MANUAL_REVIEW`, `PENDING` inválidas | 200 / 400 |
| Ids inexistentes pero válidos | `ver_0000000000000000`, `wlt_ffffffffffffffff`, `"a"*64` | 404 |
| Ids inválidos | `id.con.punto`, `id con espacio`, `x';DROP`, `<script>`, `"a"*65` | 400 |
| Tamaño de cuerpo | Exactamente `config.MAX_BODY_BYTES` (acepta) y `+1` (413) | Borde |
| Valor "secreto" | `SECRETO valor!` en `documentNumber`, `secreto-interno-xyz` en excepción | Que no se filtre en respuestas |

## 4. Trazabilidad: criterio → prueba → resultado esperado → estado

Rutas relativas a `api/tests/onboarding/`. Estado de **todas** las filas: `NO EJECUTADO`, salvo las marcadas `NO AUTOMATIZADO – BLOQUEADO`.

### 4.1 Parte API (automatizada)

| Criterio | Prueba (archivo::función) | Resultado esperado | Estado |
|---|---|---|---|
| 3.1 `GET /health` 200 | `test_h01_health.py::test_health_responde_200_con_estado_ok` | `200`, cuerpo `{"status":"ok"}` | NO EJECUTADO |
| 3.1 (límite API de la latencia) | `test_h01_health.py::test_health_ignora_parametro_de_latencia` | `GET /health?latency=abc` → `200`. El API no valida la latencia (A-7); el bloqueo es del cliente | NO EJECUTADO |
| 3.1 error | `test_h01_health.py::test_health_rechaza_metodo_post_con_405` | `405`, `{"code":"METHOD_NOT_ALLOWED","message":...}` | NO EJECUTADO |
| 3.2 `GET /scenarios` | `test_h01_scenarios.py::test_scenarios_devuelve_lista_para_el_selector`, `::test_scenarios_ids_son_unicos_y_label_no_vacio`, `::test_scenarios_son_aceptados_por_post_kyc` | `200`; 4 ids `{APPROVED, REJECTED, MANUAL_REVIEW, KYC_UNAVAILABLE}` con `label` no vacío; cada id es usable en `POST /kyc/verifications` (201 los tres primeros, 503 el último) | NO EJECUTADO |
| 3.2 error | `test_h01_scenarios.py::test_scenarios_rechaza_post_con_405` | `405` con formato común. El "error de red con mensaje legible" es del cliente (4.2, C-02) | NO EJECUTADO |
| 3.3 `201` x3 | `test_h01_kyc_verifications.py::test_post_crea_verificacion_201[APPROVED/REJECTED/MANUAL_REVIEW]` | `201`; campos exactos `{id,status,decisionStatus,walletId,createdAt}`; `status`=escenario; `decisionStatus` = `NOT_REQUIRED`/`NOT_REQUIRED`/`PENDING`; `walletId` solo en `APPROVED` | NO EJECUTADO |
| 3.3 `503` | `...::test_post_kyc_no_disponible_503_sin_efectos` | `503 {"code":"KYC_UNAVAILABLE",...}` y no se crea verificación, wallet ni caso | NO EJECUTADO |
| 3.3 documento sin `TEST-` (lado servidor) | `...::test_post_documento_sin_prefijo_test_es_aceptado_por_el_servidor_por_defecto`, `::test_post_con_prefijo_obligatorio_activado_rechaza_documento_sin_test`, `::test_post_con_prefijo_obligatorio_activado_acepta_test` | Por defecto `DOC-123` → `201`. Con `ENFORCE_TEST_DOC_PREFIX=True`: `DOC-123` → `400 BAD_REQUEST`; `TEST-123` → `201`. El bloqueo en cliente es C-03 (4.2) | NO EJECUTADO |
| 3.3 negativos/bordes | `...::test_post_payload_invalido_400[*]`, `::test_post_json_malformado_400`, `::test_post_cuerpo_no_objeto_400`, `::test_post_longitud_documento_en_el_limite[*]`, `::test_post_recorta_espacios_del_documento`, `::test_post_ignora_campos_desconocidos`, `::test_post_ids_unicos` | `400 BAD_REQUEST` en payloads inválidos; 1 y 32 caracteres → 201; 33 → 400; espacios recortados; campos extra ignorados; ids distintos | NO EJECUTADO |
| 3.4 `200` | `test_h01_kyc_verifications.py::test_get_verificacion_200`, `::test_get_verificacion_pendiente_refleja_estado` | `200`; mismo cuerpo que la creación (`MANUAL_REVIEW` → `decisionStatus=PENDING`) | NO EJECUTADO |
| 3.4 `404` | `...::test_get_verificacion_inexistente_404`, `::test_get_verificacion_id_en_el_limite_de_64_es_404` | `404 NOT_FOUND` con `{"code","message"}` | NO EJECUTADO |
| 3.4 borde | `...::test_get_verificacion_id_invalido_400`, `::test_get_verificacion_no_expone_campos_internos` | id de 65 caracteres o con símbolos → `400`; sin `decision_status`, `wallet_id`, `created_at` | NO EJECUTADO |
| 3.5 `200` sobre `PENDING` | `test_h01_kyc_decision.py::test_decision_aprobada_sobre_pending_200_y_abre_wallet`, `::test_decision_rechazada_sobre_pending_200_sin_wallet` | `200`; `status`=decisión; `decisionStatus=DECIDED`; wallet solo si `APPROVED` | NO EJECUTADO |
| 3.5 `409` | `...::test_segunda_decision_409_decision_conflict`, `::test_decision_sobre_verificacion_no_pending_409[APPROVED/REJECTED]` | `409 {"code":"DECISION_CONFLICT",...}` y el estado no cambia | NO EJECUTADO |
| 3.5 negativos/bordes | `...::test_decision_inexistente_404`, `::test_decision_invalida_400[*]`, `::test_decision_con_id_invalido_400`, `::test_decision_invalida_no_altera_el_estado`, `::test_decision_cuerpo_sobre_el_limite_413` | `404`; `MANUAL_REVIEW`/`PENDING`/ausente → `400`; id inválido → `400`; tras un 400 aún se puede decidir con 200; cuerpo grande → `413` | NO EJECUTADO |
| 3.5 concurrencia | `...::test_dos_decisiones_simultaneas_un_exito_un_conflicto` | Exactamente un éxito y un `DECISION_CONFLICT`; una sola wallet | NO EJECUTADO |
| 3.6 `200` saldos 0 | `test_h01_wallets.py::test_wallet_200_con_saldos_en_cero` | `200`, `{"id":<wid>,"balances":{"available":0,"pending":0}}`, enteros | NO EJECUTADO |
| 3.6 `404` | `...::test_wallet_inexistente_404`, `::test_wallet_id_en_el_limite_de_64_es_404`, `::test_wallet_id_invalido_400`, `::test_no_hay_wallet_para_verificaciones_no_aprobadas[*]` | `404 NOT_FOUND`; 65 caracteres → `400`; id de verificación `REJECTED`/`MANUAL_REVIEW` usado como wallet → `404` | NO EJECUTADO |
| 3.7 caso `KYC_REVIEW` `OPEN` | `test_h01_support_cases.py::test_caso_kyc_review_open_tras_manual_review`, `::test_dos_revisiones_generan_dos_casos`, `::test_caso_se_cierra_al_decidir` | Un caso `{id,type:"KYC_REVIEW",status:"OPEN",verificationId,createdAt}`; tras decidir, `CLOSED` | NO EJECUTADO |
| 3.7 lista vacía | `...::test_lista_vacia_sin_casos`, `::test_approved_rejected_y_503_no_generan_casos`, `::test_support_cases_rechaza_post_con_405` | `200` y `[]`; sin casos en `APPROVED`/`REJECTED`/503; `405` con POST | NO EJECUTADO |
| 3.8 `POST /control/reset` `200` | `test_h01_control_reset.py::test_reset_limpia_estado_200`, `::test_reset_sobre_estado_vacio_es_idempotente`, `::test_reset_permite_empezar_de_cero` | `200 {"status":"reset"}`; después, casos `[]` y verificaciones y wallets → `404`; repetible | NO EJECUTADO |
| 3.8 error/borde | `...::test_reset_deshabilitado_devuelve_404_y_conserva_estado`, `::test_reset_rechaza_get_con_405` | Con `ENABLE_CONTROL_RESET=False` → `404 NOT_FOUND` y el estado se conserva; GET → `405` | NO EJECUTADO |
| 3.8 persistencia | `...::test_estado_persiste_entre_clientes_mientras_no_haya_reset`, `::test_el_flujo_completo_no_escribe_archivos_en_disco` | Estado compartido en memoria entre clientes; `tmp_path` (cwd) queda vacío | NO EJECUTADO |
| 3.8 "limpia estado local" y "cancelar no llama a la API" | — | Es del cliente (4.2, C-06 y C-07) | NO AUTOMATIZADO – BLOQUEADO |
| 3.9 `400` | `test_h01_error_handler.py::test_400_validacion_usa_formato_comun_y_nombra_campos`, `::test_validacion_nunca_responde_422[*]`, `::test_400_no_repite_valores_enviados` | `400 BAD_REQUEST`, cuerpo exacto `{"code","message"}`, campos nombrados, sin 422, sin eco de valores | NO EJECUTADO |
| 3.9 `404` | `...::test_404_ruta_inexistente`, `::test_404_recurso_inexistente` | `404 NOT_FOUND`, mensaje fijo | NO EJECUTADO |
| 3.9 `409` | `...::test_409_conflicto_de_decision` | `409 DECISION_CONFLICT` | NO EJECUTADO |
| 3.9 `413` | `...::test_413_cuerpo_demasiado_grande` | `413 PAYLOAD_TOO_LARGE` | NO EJECUTADO |
| 3.9 `429` | `...::test_codigos_http_generan_codigo_y_mensaje_comunes[429]`, `::test_429_conserva_cabecera_retry_after` | **Solo a nivel de handler** sobre una app aislada: `429 RATE_LIMITED` y `Retry-After` preservado. Ningún endpoint real lo genera (A-6) | NO EJECUTADO |
| 3.9 `503` | `...::test_503_kyc_no_disponible`, `::test_codigos_http_generan_codigo_y_mensaje_comunes[503]` | `503 KYC_UNAVAILABLE` en el endpoint real; `503 SERVICE_UNAVAILABLE` genérico | NO EJECUTADO |
| 3.9 otros | `...::test_405_metodo_no_permitido`, `::test_codigo_desconocido_usa_http_error`, `::test_500_no_filtra_detalles_internos` | `405` común; 418 → `HTTP_ERROR`; 500 → `INTERNAL_ERROR` sin trazas ni texto interno | NO EJECUTADO |
| 3.9 "se muestra el mensaje" | — | Es del cliente (C-08) | NO AUTOMATIZADO – BLOQUEADO |
| 3.10 estado activo (lado API) | `test_h01_flujo_integracion.py::test_wallet_activa_solo_tras_aprobacion[*]` | Solo `APPROVED` directo o `MANUAL_REVIEW`→`APPROVED` tienen `walletId` y wallet con saldos 0. `REJECTED`, `PENDING` y `MANUAL_REVIEW`→`REJECTED` no | NO EJECUTADO |
| 3.10 pasos, bloqueos, "incompleto" | — | Es del cliente (C-09 a C-12) | NO AUTOMATIZADO – BLOQUEADO |
| 3.11 eventos y mediana | — | Sin código ni ubicación conocida (P-6). Casos en C-13 a C-16 | NO AUTOMATIZADO – BLOQUEADO |
| 3.12 salida real adjunta | Procedimiento de la sección 7 | La persona adjunta la salida íntegra al PR | NO EJECUTADO |

### 4.2 Casos de cliente (diseño; no hay código de cliente que probar)

Se implementarán como `*.spec.ts` con API simulada (S-6) cuando se confirmen la ruta, el ejecutor (P-2) y la ubicación de eventos y mediana (P-6). Mientras tanto no cuentan como cobertura.

| ID | Criterio | Precondición | Acción | Resultado esperado |
|---|---|---|---|---|
| C-01 | 3.1 | Formulario de latencia | Latencia inválida (vacía, negativa, texto) | Envío bloqueado, mensaje de validación, 0 llamadas a `GET /health` |
| C-02 | 3.2 | Servicio HTTP simulado | (a) responde la lista; (b) falla la red | (a) el selector muestra las opciones; (b) mensaje legible, sin texto técnico |
| C-03 | 3.3 | Formulario KYC | Documento `DOC-123` | Bloqueado, 0 llamadas a `POST /kyc/verifications` |
| C-04 | 3.3 | Servicio simulado | Respuesta `503 KYC_UNAVAILABLE` | Se muestra el `message` accionable |
| C-05 | 3.3 | Servicio simulado | `201` con cada estado | La UI refleja `APPROVED`, `REJECTED` y `MANUAL_REVIEW` |
| C-06 | 3.8 | Estado local con datos | Confirmar el reset | 1 llamada a `POST /control/reset` y estado local limpio |
| C-07 | 3.8 | Estado local con datos | Cancelar la confirmación | 0 llamadas y estado intacto |
| C-08 | 3.9 | Servicio simulado | Respuestas 400, 404, 409, 413, 429 y 503 | Se muestra el `message` de cada una |
| C-09 | 3.10 | Onboarding | Abrir el flujo | Pasos visibles en orden |
| C-10 | 3.10 | Paso con dato faltante | Intentar avanzar | Bloqueado |
| C-11 | 3.10 | Paso con dato inválido | Intentar avanzar | Bloqueado |
| C-12 | 3.10 | Estados: exitoso, incompleto, `PENDING`, `REJECTED` | Evaluar "activo" | Solo el onboarding exitoso (`APPROVED`) es "activo" |
| C-13 | 3.11 | Servicio de eventos | Onboarding completado | Se registra el evento "completo" |
| C-14 | 3.11 | Servicio de eventos | Salida sin terminar | Se registra el evento "abandonado" |
| C-15 | 3.11 | Función de mediana | Cantidad impar | Valor central |
| C-16 | 3.11 | Función de mediana | Cantidad par (T-10) | Promedio de los dos centrales. Lista vacía: por definir (P-6) |

## 5. Casos por tipo

| Tipo | Casos (archivo) |
|---|---|
| **Positivo** | Health 200; lista de escenarios; `POST` 201 x3; `GET` de verificación; decisión `APPROVED` y `REJECTED` sobre `PENDING`; wallet con saldos 0; caso `KYC_REVIEW` `OPEN`; reset 200 |
| **Negativo** | 400 por payload inválido, JSON malformado, cuerpo no objeto, decisión inválida e id inválido; 404 de verificación, wallet y ruta; 405; 409 por segunda decisión o decisión sobre no `PENDING`; 413; 503; reset deshabilitado → 404; 500 sin filtración |
| **Borde** | Documento de 1/32/33 caracteres; espacios recortados; campos desconocidos; id de 64 (404) y 65 (400); cuerpo exacto en el límite (201) y +1 (413); cuerpo *chunked*; `Content-Length` no numérico; reset repetido; lista de casos vacía; prefijo `TEST-` en servidor activado y desactivado; código HTTP desconocido |
| **Integración** | Flujo aprobado directo; flujo revisión manual → decisión → wallet → caso cerrado → 409; flujo rechazo manual; reset tras un flujo completo; persistencia en memoria entre clientes; sin archivos en disco; handler de errores en app real y en app aislada; concurrencia de dos decisiones |
| **Seguridad (visible en Backend)** | Ids con símbolos o largos → 400 sin eco; documento con inyección o Unicode → 400; mensajes sin trazas; sin campos internos; reset desactivable; `RATE_LIMITED` y 500 genéricos |

## 6. Preparación, comandos y limpieza

### 6.1 Preparación (una persona; NO EJECUTADO)

```bash
git status --short && git rev-parse HEAD        # anotar el commit base
cd api
python --version
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt                 # o el manifiesto existente (T-6)
pip check
pip freeze | grep -iE "^(fastapi|starlette|pydantic|uvicorn|httpx|pytest)=="
```

Copiar los archivos de la sección 8 a `api/tests/onboarding/`. No modificar archivos existentes.

### 6.2 Fase 1: línea base (obligatoria; todas las pruebas)

```bash
# Desde la raíz del repositorio
python tools/lab.py test api 2>&1 | tee salida_h01_fase1_lab.txt

# Directo, suite completa del API (existentes + nuevas)
cd api
python -m pytest tests -v -rA --strict-markers 2>&1 | tee ../salida_h01_fase1_pytest.txt

# Solo las nuevas (para aislar fallos)
python -m pytest tests/onboarding -v -rA --strict-markers 2>&1 | tee ../salida_h01_fase1_h01.txt
```

Útiles para depurar, sin sustituir a lo anterior:

```bash
python -m pytest tests/onboarding/test_h01_kyc_decision.py -v
python -m pytest tests/onboarding -v -k "413 or chunked or content_length"
```

### 6.3 Criterios de salida de la ejecución

1. `pytest` termina con código 0.
2. No aparecen `SKIPPED`, `XFAIL` ni `XPASS` (un skip cuenta como NO cumplido):
   ```bash
   grep -E " (SKIPPED|XFAIL|XPASS)" ../salida_h01_fase1_pytest.txt   # debe no producir salida
   ```
   PowerShell: `Select-String -Pattern " (SKIPPED|XFAIL|XPASS)" ..\salida_h01_fase1_pytest.txt`.
3. Cada fallo se clasifica: error de la prueba (se corrige), prueba no verificable (se descarta con justificación), defecto del API (hallazgo, S-7). Ninguno se atribuye al cambio.
4. Si `import app` falla porque `api/app/` no existe, se registra "línea base bloqueada (T-2)".

### 6.4 Dependencias (manual y obligatorio; no es una prueba pytest)

Los pines de Backend no están verificados (A-11). Antes de fusionar, la persona ejecuta y adjunta la salida:

```bash
cd api
pip check
pip install pip-audit            # herramienta externa, no está en requirements-dev.txt
pip-audit -r requirements.txt
# Alternativa por paquete (OSV):
curl -s -X POST https://api.osv.dev/v1/query \
  -d '{"package":{"name":"starlette","ecosystem":"PyPI"},"version":"0.41.3"}'
```

Repetir para `fastapi`, `pydantic`, `uvicorn`, `httpx` y `pytest`. No afirmo que existan o no avisos. Es un paso de proceso, no una verificación opcional dentro de la suite.

### 6.5 Fase 2: del cambio (solo si hay algo que aplicar)

Si, tras la Fase 1, se aplica código de `backend_spec.md` o un cambio de `requirements-dev.txt`, se repiten los comandos de 6.2 con salidas `*_fase2_*.txt` y se compara:

```bash
diff <(grep -E "PASSED|FAILED|ERROR" salida_h01_fase1_h01.txt | sort) \
     <(grep -E "PASSED|FAILED|ERROR" salida_h01_fase2_h01.txt | sort)
```

Solo los fallos nuevos de la Fase 2 se atribuyen al cambio. Si no se aplica nada, se anota "Fase 2: no aplica".

### 6.6 Limpieza

- Automática por prueba: el fixture `entorno_aislado` resetea el almacén antes y después, restaura las banderas de `app.config` (`monkeypatch`) y vuelve al directorio original. `tmp_path` lo elimina pytest.
- Manual:
  ```bash
  cd api && rm -rf .pytest_cache && find . -name "__pycache__" -type d -prune -exec rm -rf {} +
  deactivate
  # si se levantó uvicorn para las curl de Backend: detenerlo con Ctrl+C
  rm -f ../salida_h01_*.txt   # solo después de adjuntarlas al PR
  ```

## 7. Procedimiento 3.12: evidencia en el PR

La persona responsable pega, sin editar ni resumir:

```text
Fecha/hora de ejecución: <completar>
Commit: <git rev-parse HEAD>
Python: <python --version>
Entorno: <pip freeze (extracto de 6.1)>
Comando: python tools/lab.py test api            -> salida íntegra
Comando: cd api && python -m pytest tests -v -rA --strict-markers -> salida íntegra
Resultado de grep SKIPPED/XFAIL/XPASS: <vacío | contenido>
Salida de pip check / pip-audit / OSV (6.4): <íntegra>
Ejecución de cliente (ng test --watch=false): <NO EJECUTADO: bloqueado por P-2/P-6 | salida íntegra>
Fallos y su clasificación (corregir / descartar / hallazgo): <completar>
```

## 8. Hallazgos y riesgos abiertos

| # | Tema | Acción necesaria |
|---|---|---|
| R-1 | No hay código de cliente: 3.1 (latencia), 3.2 (red), 3.3 (`TEST-`), 3.8 (cancelar), 3.9 (mensajes), 3.10 y 3.11 no están cubiertos | Una persona confirma ruta, ejecutor y ubicación (P-2, P-6) y se implementan C-01 a C-16 |
| R-2 | Ningún endpoint real produce `429` (A-6) | Se prueba solo el handler. Decidir si el Issue exige un limitador |
| R-3 | No recibí la entrega de Seguridad (T-8) | Añadir sus correcciones como casos |
| R-4 | `api/app/` existente frente a `backend_spec.md` (T-2) | Si difieren nombres o campos, la prueba que falle es un hallazgo |
| R-5 | Contenido de `tools/lab.py` y tabla de `design.md` desconocidos | Confirmar y adjuntar |
| R-6 | Tests de transporte (T-11) | Se corrigen o descartan si fallan en la línea base |
| R-7 | Pines de dependencias sin verificar | Ejecutar 6.4 |
| R-8 | Un único almacén global: la suite no admite paralelismo | No usar `-n` |

## 9. Código de las pruebas

```python
# api/tests/onboarding/__init__.py
"""Pruebas H01 del onboarding de la wallet (archivos nuevos)."""
```

```python
# api/tests/onboarding/conftest.py
"""Fixtures de H01.

Aislamiento:
- monkeypatch.chdir(tmp_path): cualquier escritura accidental con ruta relativa cae en tmp_path.
- monkeypatch.setattr(config, ...): fija las banderas del servidor, sin depender del entorno.
- El almacén en memoria se resetea directamente (no via POST /control/reset) antes y después.
"""
import sys
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parents[2]  # .../api
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from fastapi.testclient import TestClient  # noqa: E402

from app import config  # noqa: E402
from app.main import app  # noqa: E402
from app.repository import get_store  # noqa: E402


@pytest.fixture(autouse=True)
def entorno_aislado(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "ENFORCE_TEST_DOC_PREFIX", False)
    monkeypatch.setattr(config, "ENABLE_CONTROL_RESET", True)
    get_store().reset()
    yield
    get_store().reset()


@pytest.fixture
def store():
    return get_store()


@pytest.fixture
def client():
    # raise_server_exceptions=False: permite observar respuestas 500 (backend_spec §5).
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def crear(client):
    def _crear(scenario, documento="TEST-0001"):
        return client.post(
            "/kyc/verifications",
            json={"documentNumber": documento, "scenario": scenario},
        )

    return _crear


@pytest.fixture
def decidir(client):
    def _decidir(verification_id, decision):
        return client.post(
            f"/kyc/verifications/{verification_id}/decision",
            json={"decision": decision},
        )

    return _decidir


@pytest.fixture
def afirmar_error():
    """Comprueba el formato único de error {"code","message"} y devuelve el cuerpo."""

    def _afirmar(resp, status, code):
        assert resp.status_code == status, resp.text
        assert resp.headers["content-type"].startswith("application/json")
        cuerpo = resp.json()
        assert set(cuerpo) == {"code", "message"}
        assert cuerpo["code"] == code
        # Heurística de "accionable": texto no trivial. La revisión humana sigue siendo necesaria.
        assert isinstance(cuerpo["message"], str)
        assert len(cuerpo["message"].strip()) >= 20
        assert "Traceback" not in resp.text
        return cuerpo

    return _afirmar
```

```python
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
```

```python
# api/tests/onboarding/test_h01_scenarios.py
"""3.2 GET /scenarios (lado API). El error de red es del cliente."""
import pytest

ESCENARIOS = {"APPROVED", "REJECTED", "MANUAL_REVIEW", "KYC_UNAVAILABLE"}


def test_scenarios_devuelve_lista_para_el_selector(client):
    r = client.get("/scenarios")
    assert r.status_code == 200
    lista = r.json()
    assert isinstance(lista, list)
    assert {item["id"] for item in lista} == ESCENARIOS


def test_scenarios_ids_son_unicos_y_label_no_vacio(client):
    lista = client.get("/scenarios").json()
    ids = [item["id"] for item in lista]
    assert len(ids) == len(set(ids))
    for item in lista:
        assert set(item) == {"id", "label"}
        assert isinstance(item["label"], str) and item["label"].strip()


def test_scenarios_rechaza_post_con_405(client, afirmar_error):
    afirmar_error(client.post("/scenarios"), 405, "METHOD_NOT_ALLOWED")


@pytest.mark.parametrize(
    "scenario,esperado",
    [("APPROVED", 201), ("REJECTED", 201), ("MANUAL_REVIEW", 201), ("KYC_UNAVAILABLE", 503)],
)
def test_scenarios_son_aceptados_por_post_kyc(client, crear, scenario, esperado):
    ids = {item["id"] for item in client.get("/scenarios").json()}
    assert scenario in ids
    assert crear(scenario).status_code == esperado
```

```python
# api/tests/onboarding/test_h01_kyc_verifications.py
"""3.3 POST /kyc/verifications y 3.4 GET /kyc/verifications/{id}."""
import json
import re
from datetime import datetime

import pytest

from app import config

ID_VER = re.compile(r"^ver_[0-9a-f]{16}$")
ID_WLT = re.compile(r"^wlt_[0-9a-f]{16}$")
CAMPOS = {"id", "status", "decisionStatus", "walletId", "createdAt"}
JSON_HEADERS = {"Content-Type": "application/json"}

ESPERADO = {
    "APPROVED": ("NOT_REQUIRED", True),
    "REJECTED": ("NOT_REQUIRED", False),
    "MANUAL_REVIEW": ("PENDING", False),
}


def _cuerpo_de_tamano(n):
    """JSON compacto de exactamente n bytes (campo 'relleno' desconocido, ignorado por el API)."""
    base = {"documentNumber": "TEST-1", "scenario": "APPROVED", "relleno": ""}
    vacio = json.dumps(base, separators=(",", ":")).encode()
    cuerpo = dict(base, relleno="a" * (n - len(vacio)))
    texto = json.dumps(cuerpo, separators=(",", ":")).encode()
    assert len(texto) == n
    return texto


# ---------------- 3.3 positivos ----------------

@pytest.mark.parametrize("scenario", ["APPROVED", "REJECTED", "MANUAL_REVIEW"])
def test_post_crea_verificacion_201(crear, scenario):
    r = crear(scenario)
    assert r.status_code == 201
    cuerpo = r.json()
    assert set(cuerpo) == CAMPOS
    decision_status, con_wallet = ESPERADO[scenario]
    assert cuerpo["status"] == scenario
    assert cuerpo["decisionStatus"] == decision_status
    assert ID_VER.match(cuerpo["id"])
    if con_wallet:
        assert ID_WLT.match(cuerpo["walletId"])
    else:
        assert cuerpo["walletId"] is None
    creado = datetime.fromisoformat(cuerpo["createdAt"].replace("Z", "+00:00"))
    assert creado.tzinfo is not None


def test_post_ids_unicos(crear):
    ids = {crear("MANUAL_REVIEW").json()["id"] for _ in range(20)}
    assert len(ids) == 20


# ---------------- 3.3 503 ----------------

def test_post_kyc_no_disponible_503_sin_efectos(client, crear, store, afirmar_error):
    r = crear("KYC_UNAVAILABLE")
    afirmar_error(r, 503, "KYC_UNAVAILABLE")
    assert store.verifications == {}
    assert store.wallets == {}
    assert store.cases == {}
    assert client.get("/support/cases").json() == []


# ---------------- 3.3 documento sin TEST- (lado servidor, T-9) ----------------

def test_post_documento_sin_prefijo_test_es_aceptado_por_el_servidor_por_defecto(crear):
    assert crear("APPROVED", documento="DOC-123").status_code == 201


def test_post_con_prefijo_obligatorio_activado_rechaza_documento_sin_test(
    crear, monkeypatch, afirmar_error
):
    monkeypatch.setattr(config, "ENFORCE_TEST_DOC_PREFIX", True)
    afirmar_error(crear("APPROVED", documento="DOC-123"), 400, "BAD_REQUEST")


def test_post_con_prefijo_obligatorio_activado_acepta_test(crear, monkeypatch):
    monkeypatch.setattr(config, "ENFORCE_TEST_DOC_PREFIX", True)
    assert crear("APPROVED", documento="TEST-123").status_code == 201


# ---------------- 3.3 negativos ----------------

PAYLOADS_INVALIDOS = [
    pytest.param({}, id="vacio"),
    pytest.param({"scenario": "APPROVED"}, id="sin-documento"),
    pytest.param({"documentNumber": "TEST-1"}, id="sin-scenario"),
    pytest.param({"documentNumber": "TEST-1", "scenario": "INEXISTENTE"}, id="scenario-invalido"),
    pytest.param({"documentNumber": "TEST-1", "scenario": "approved"}, id="scenario-minusculas"),
    pytest.param({"documentNumber": "TEST-1", "scenario": None}, id="scenario-null"),
    pytest.param({"documentNumber": None, "scenario": "APPROVED"}, id="documento-null"),
    pytest.param({"documentNumber": "", "scenario": "APPROVED"}, id="documento-vacio"),
    pytest.param({"documentNumber": "   ", "scenario": "APPROVED"}, id="documento-espacios"),
    pytest.param({"documentNumber": "TEST 001", "scenario": "APPROVED"}, id="documento-con-espacio"),
    pytest.param({"documentNumber": "TEST-1'; DROP TABLE x;--", "scenario": "APPROVED"}, id="documento-inyeccion"),
    pytest.param({"documentNumber": "TEST-ñ", "scenario": "APPROVED"}, id="documento-unicode"),
    pytest.param({"documentNumber": "TEST-1\nX", "scenario": "APPROVED"}, id="documento-salto-de-linea"),
    pytest.param({"documentNumber": 12345, "scenario": "APPROVED"}, id="documento-numerico"),
    pytest.param({"documentNumber": "TEST-" + "A" * 28, "scenario": "APPROVED"}, id="documento-33-caracteres"),
]


@pytest.mark.parametrize("payload", PAYLOADS_INVALIDOS)
def test_post_payload_invalido_400(client, store, afirmar_error, payload):
    r = client.post("/kyc/verifications", json=payload)
    afirmar_error(r, 400, "BAD_REQUEST")
    assert store.verifications == {}


def test_post_json_malformado_400(client, afirmar_error):
    r = client.post("/kyc/verifications", content=b"{no-es-json", headers=JSON_HEADERS)
    afirmar_error(r, 400, "BAD_REQUEST")


def test_post_cuerpo_no_objeto_400(client, afirmar_error):
    afirmar_error(client.post("/kyc/verifications", json=[]), 400, "BAD_REQUEST")


def test_post_mensaje_400_no_repite_valores_enviados(client, afirmar_error):
    r = client.post(
        "/kyc/verifications",
        json={"documentNumber": "SECRETO valor!", "scenario": "APPROVED"},
    )
    cuerpo = afirmar_error(r, 400, "BAD_REQUEST")
    assert "SECRETO" not in cuerpo["message"]
    assert "documentNumber" in cuerpo["message"]


# ---------------- 3.3 bordes ----------------

@pytest.mark.parametrize(
    "documento,esperado",
    [("A", 201), ("TEST-" + "A" * 27, 201), ("TEST-" + "A" * 28, 400)],
    ids=["1-caracter", "32-caracteres", "33-caracteres"],
)
def test_post_longitud_documento_en_el_limite(crear, documento, esperado):
    assert crear("APPROVED", documento=documento).status_code == esperado


def test_post_recorta_espacios_del_documento(crear):
    assert crear("APPROVED", documento="  TEST-1  ").status_code == 201


def test_post_ignora_campos_desconocidos(client):
    r = client.post(
        "/kyc/verifications",
        json={"documentNumber": "TEST-1", "scenario": "APPROVED", "extra": 1},
    )
    assert r.status_code == 201
    assert "extra" not in r.json()


def test_post_cuerpo_en_el_limite_exacto_es_aceptado(client):
    cuerpo = _cuerpo_de_tamano(config.MAX_BODY_BYTES)
    r = client.post("/kyc/verifications", content=cuerpo, headers=JSON_HEADERS)
    assert r.status_code == 201


def test_post_cuerpo_sobre_el_limite_413(client, afirmar_error):
    cuerpo = _cuerpo_de_tamano(config.MAX_BODY_BYTES + 1)
    r = client.post("/kyc/verifications", content=cuerpo, headers=JSON_HEADERS)
    afirmar_error(r, 413, "PAYLOAD_TOO_LARGE")


def test_post_cuerpo_chunked_sobre_el_limite_413(client, afirmar_error):
    # Sin Content-Length (Transfer-Encoding: chunked): el middleware cuenta bytes recibidos (T-11).
    cuerpo = _cuerpo_de_tamano(config.MAX_BODY_BYTES + 1)

    def partes():
        yield cuerpo[:100]
        yield cuerpo[100:]

    r = client.post("/kyc/verifications", content=partes(), headers=JSON_HEADERS)
    afirmar_error(r, 413, "PAYLOAD_TOO_LARGE")


def test_post_content_length_invalido_400(client, afirmar_error):
    # Content-Length no numérico (T-11).
    r = client.post(
        "/kyc/verifications",
        content=b'{"documentNumber":"TEST-1","scenario":"APPROVED"}',
        headers={"Content-Type": "application/json", "Content-Length": "abc"},
    )
    afirmar_error(r, 400, "BAD_REQUEST")


# ---------------- 3.4 GET /kyc/verifications/{id} ----------------

def test_get_verificacion_200(client, crear):
    creada = crear("APPROVED").json()
    r = client.get(f"/kyc/verifications/{creada['id']}")
    assert r.status_code == 200
    assert r.json() == creada


def test_get_verificacion_pendiente_refleja_estado(client, crear):
    creada = crear("MANUAL_REVIEW").json()
    cuerpo = client.get(f"/kyc/verifications/{creada['id']}").json()
    assert cuerpo["status"] == "MANUAL_REVIEW"
    assert cuerpo["decisionStatus"] == "PENDING"


def test_get_verificacion_inexistente_404(client, afirmar_error):
    r = client.get("/kyc/verifications/ver_0000000000000000")
    afirmar_error(r, 404, "NOT_FOUND")


def test_get_verificacion_id_en_el_limite_de_64_es_404(client, afirmar_error):
    r = client.get("/kyc/verifications/" + "a" * 64)
    afirmar_error(r, 404, "NOT_FOUND")


def test_get_verificacion_id_invalido_400(client, afirmar_error):
    afirmar_error(client.get("/kyc/verifications/" + "a" * 65), 400, "BAD_REQUEST")
    afirmar_error(client.get("/kyc/verifications/id.con.punto"), 400, "BAD_REQUEST")


def test_get_verificacion_no_expone_campos_internos(client, crear):
    creada = crear("MANUAL_REVIEW").json()
    texto = client.get(f"/kyc/verifications/{creada['id']}").text
    for interno in ("decision_status", "wallet_id", "created_at", "lock"):
        assert interno not in texto
```

```python
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
```

```python
# api/tests/onboarding/test_h01_wallets.py
"""3.6 GET /wallets/{id}."""
import pytest


def test_wallet_200_con_saldos_en_cero(client, crear):
    v = crear("APPROVED").json()
    r = client.get(f"/wallets/{v['walletId']}")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo == {"id": v["walletId"], "balances": {"available": 0, "pending": 0}}
    for saldo in cuerpo["balances"].values():
        assert type(saldo) is int  # entero, no bool ni float (A-10)


def test_wallet_inexistente_404(client, afirmar_error):
    afirmar_error(client.get("/wallets/wlt_ffffffffffffffff"), 404, "NOT_FOUND")


def test_wallet_id_en_el_limite_de_64_es_404(client, afirmar_error):
    afirmar_error(client.get("/wallets/" + "a" * 64), 404, "NOT_FOUND")


def test_wallet_id_invalido_400(client, afirmar_error):
    afirmar_error(client.get("/wallets/" + "a" * 65), 400, "BAD_REQUEST")
    afirmar_error(client.get("/wallets/id.con.punto"), 400, "BAD_REQUEST")


@pytest.mark.parametrize("scenario", ["REJECTED", "MANUAL_REVIEW"])
def test_no_hay_wallet_para_verificaciones_no_aprobadas(client, crear, store, afirmar_error, scenario):
    v = crear(scenario).json()
    assert v["walletId"] is None
    assert store.wallets == {}
    afirmar_error(client.get(f"/wallets/{v['id']}"), 404, "NOT_FOUND")
```

```python
# api/tests/onboarding/test_h01_support_cases.py
"""3.7 GET /support/cases."""
import re

CAMPOS = {"id", "type", "status", "verificationId", "createdAt"}
ID_CASO = re.compile(r"^case_[0-9a-f]{16}$")


def test_lista_vacia_sin_casos(client):
    r = client.get("/support/cases")
    assert r.status_code == 200
    assert r.json() == []


def test_caso_kyc_review_open_tras_manual_review(client, crear):
    v = crear("MANUAL_REVIEW").json()
    r = client.get("/support/cases")
    assert r.status_code == 200
    casos = r.json()
    assert len(casos) == 1
    caso = casos[0]
    assert set(caso) == CAMPOS
    assert caso["type"] == "KYC_REVIEW"
    assert caso["status"] == "OPEN"
    assert caso["verificationId"] == v["id"]
    assert ID_CASO.match(caso["id"])


def test_dos_revisiones_generan_dos_casos(client, crear):
    ids = {crear("MANUAL_REVIEW").json()["id"] for _ in range(2)}
    casos = client.get("/support/cases").json()
    assert len(casos) == 2
    assert {c["verificationId"] for c in casos} == ids
    assert all(c["status"] == "OPEN" for c in casos)


def test_caso_se_cierra_al_decidir(client, crear, decidir):
    v = crear("MANUAL_REVIEW").json()
    assert decidir(v["id"], "REJECTED").status_code == 200
    casos = client.get("/support/cases").json()
    assert len(casos) == 1
    assert casos[0]["status"] == "CLOSED"


def test_approved_rejected_y_503_no_generan_casos(client, crear):
    crear("APPROVED")
    crear("REJECTED")
    assert crear("KYC_UNAVAILABLE").status_code == 503
    assert client.get("/support/cases").json() == []


def test_support_cases_rechaza_post_con_405(client, afirmar_error):
    afirmar_error(client.post("/support/cases"), 405, "METHOD_NOT_ALLOWED")
```

```python
# api/tests/onboarding/test_h01_control_reset.py
"""3.8 POST /control/reset (lado API) y persistencia en memoria.

"Limpia estado local" y "cancelar la confirmación no llama a la API" son del cliente (casos C-06 y C-07).
"""
from fastapi.testclient import TestClient

from app import config
from app.main import app


def test_reset_limpia_estado_200(client, crear):
    aprobada = crear("APPROVED").json()
    pendiente = crear("MANUAL_REVIEW").json()
    assert len(client.get("/support/cases").json()) == 1

    r = client.post("/control/reset")
    assert r.status_code == 200
    assert r.json() == {"status": "reset"}

    assert client.get("/support/cases").json() == []
    assert client.get(f"/wallets/{aprobada['walletId']}").status_code == 404
    assert client.get(f"/kyc/verifications/{aprobada['id']}").status_code == 404
    assert client.get(f"/kyc/verifications/{pendiente['id']}").status_code == 404


def test_reset_sobre_estado_vacio_es_idempotente(client):
    for _ in range(2):
        r = client.post("/control/reset")
        assert r.status_code == 200
        assert r.json() == {"status": "reset"}


def test_reset_permite_empezar_de_cero(client, crear):
    crear("MANUAL_REVIEW")
    assert client.post("/control/reset").status_code == 200
    assert crear("MANUAL_REVIEW").status_code == 201
    assert len(client.get("/support/cases").json()) == 1


def test_reset_deshabilitado_devuelve_404_y_conserva_estado(client, crear, monkeypatch, afirmar_error):
    v = crear("APPROVED").json()
    monkeypatch.setattr(config, "ENABLE_CONTROL_RESET", False)
    afirmar_error(client.post("/control/reset"), 404, "NOT_FOUND")
    assert client.get(f"/kyc/verifications/{v['id']}").status_code == 200


def test_reset_rechaza_get_con_405(client, afirmar_error):
    afirmar_error(client.get("/control/reset"), 405, "METHOD_NOT_ALLOWED")


def test_estado_persiste_entre_clientes_mientras_no_haya_reset(crear):
    v = crear("APPROVED").json()
    with TestClient(app, raise_server_exceptions=False) as otro:
        assert otro.get(f"/kyc/verifications/{v['id']}").status_code == 200
        assert otro.post("/control/reset").status_code == 200
    with TestClient(app, raise_server_exceptions=False) as tercero:
        assert tercero.get(f"/kyc/verifications/{v['id']}").status_code == 404


def test_el_flujo_completo_no_escribe_archivos_en_disco(client, crear, decidir, tmp_path):
    # El fixture autouse fijó el directorio de trabajo en tmp_path.
    v = crear("MANUAL_REVIEW").json()
    decidir(v["id"], "APPROVED")
    client.get("/support/cases")
    client.post("/control/reset")
    assert list(tmp_path.iterdir()) == []
```

```python
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
```

```python
# api/tests/onboarding/test_h01_flujo_integracion.py
"""Integración de extremo a extremo del API (3.3 a 3.8 y lado API de 3.10)."""
import pytest


def test_flujo_aprobado_directo(client, crear):
    v = crear("APPROVED")
    assert v.status_code == 201
    v = v.json()
    assert client.get(f"/kyc/verifications/{v['id']}").json() == v
    w = client.get(f"/wallets/{v['walletId']}")
    assert w.status_code == 200
    assert w.json()["balances"] == {"available": 0, "pending": 0}
    assert client.get("/support/cases").json() == []


def test_flujo_revision_manual_aprobada(client, crear, decidir, afirmar_error):
    v = crear("MANUAL_REVIEW").json()
    assert v["decisionStatus"] == "PENDING" and v["walletId"] is None

    casos = client.get("/support/cases").json()
    assert [(c["type"], c["status"], c["verificationId"]) for c in casos] == [
        ("KYC_REVIEW", "OPEN", v["id"])
    ]

    decidida = decidir(v["id"], "APPROVED")
    assert decidida.status_code == 200
    wid = decidida.json()["walletId"]
    assert client.get(f"/wallets/{wid}").json()["balances"] == {"available": 0, "pending": 0}
    assert client.get("/support/cases").json()[0]["status"] == "CLOSED"

    afirmar_error(decidir(v["id"], "REJECTED"), 409, "DECISION_CONFLICT")


def test_flujo_revision_manual_rechazada(client, crear, decidir, store):
    v = crear("MANUAL_REVIEW").json()
    decidida = decidir(v["id"], "REJECTED").json()
    assert decidida["status"] == "REJECTED"
    assert decidida["walletId"] is None
    assert store.wallets == {}
    assert client.get("/support/cases").json()[0]["status"] == "CLOSED"


def test_flujo_reset_tras_flujo_completo(client, crear, decidir):
    v = crear("MANUAL_REVIEW").json()
    decidir(v["id"], "APPROVED")
    assert client.post("/control/reset").status_code == 200
    assert client.get("/support/cases").json() == []
    assert client.get(f"/kyc/verifications/{v['id']}").status_code == 404


@pytest.mark.parametrize(
    "scenario,decision,activa",
    [
        pytest.param("APPROVED", None, True, id="aprobado-directo"),
        pytest.param("REJECTED", None, False, id="rechazado"),
        pytest.param("MANUAL_REVIEW", None, False, id="pending"),
        pytest.param("MANUAL_REVIEW", "APPROVED", True, id="pending-aprobado"),
        pytest.param("MANUAL_REVIEW", "REJECTED", False, id="pending-rechazado"),
    ],
)
def test_wallet_activa_solo_tras_aprobacion(client, crear, decidir, store, scenario, decision, activa):
    v = crear(scenario).json()
    if decision:
        v = decidir(v["id"], decision).json()
    if activa:
        assert v["walletId"] is not None
        w = client.get(f"/wallets/{v['walletId']}")
        assert w.status_code == 200
        assert w.json()["balances"] == {"available": 0, "pending": 0}
    else:
        assert v["walletId"] is None
        assert client.get(f"/wallets/{v['id']}").status_code == 404
        assert store.wallets == {}
```

```python
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
```