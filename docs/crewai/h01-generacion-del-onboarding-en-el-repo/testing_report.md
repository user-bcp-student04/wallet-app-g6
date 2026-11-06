# testing_report.md

> **Estado global: NO EJECUTADO.** No he ejecutado nada ni dispongo de salida real de `pytest`, `ng test`, `curl`, `pip-audit` ni `python tools/lab.py test api`. Todos los resultados de este informe son **esperados**, derivados de leer el código entregado en `backend_spec.md` y `frontend_spec.md`. Una persona debe correr los comandos de la sección 7 y adjuntar la salida real, y ningún estado cambia hasta entonces. No afirmo cobertura: la medición de cobertura no está incluida y tampoco la he ejecutado.

## 1. Fuentes y supuestos declarados

**Fuentes.** Dispongo de:
- el Issue H01, tareas 2.1 a 2.8;
- `user_story.md` del Arquitecto;
- `backend_spec.md` con el código de `api/app/*`;
- `frontend_spec.md` con el código Angular.

No dispongo de:
- `spec.md` (P-1);
- el informe de Seguridad;
- las pruebas existentes del repositorio;
- el contenido de `tools/lab.py`.

| ID | Supuesto | Consecuencia si es falso |
|---|---|---|
| T-1 | Los CA son los *derivados* del Arquitecto (sección 4 de `user_story.md`). `spec.md` no está disponible, así que **2.1 («revisar contra la spec») no se puede verificar**. | Hay que contrastar la matriz con `spec.md` y corregir las pruebas afectadas. |
| T-2 | Uso las rutas, campos, escenarios (`APPROVED`/`REJECTED`/`PENDING`/`EXPIRED`), pasos (`registro`→`kyc`→`activacion`) y estados de wallet del código entregado. Son provisionales (S-4, P-3, P-4). | Si cambian, se actualizan las constantes de las pruebas. |
| T-3 | **No recibí el informe de Seguridad.** Como «correcciones propuestas por Seguridad» verifico los controles visibles en el diseño y el código: identidad por dependencia, directorio por SHA-256, límite de cuerpo, `extra="forbid"`, errores sin valores, pines exactos y escritura atómica. | Cuando llegue el informe, cada hallazgo debe sumarse a la matriz con su prueba. |
| T-4 | Las pruebas nuevas son **archivos nuevos** en `api/tests/h01/`, con su propio `conftest.py`. No modifico aserciones ni archivos existentes. | Si ya existe `api/tests/h01/`, renombra la carpeta. |
| T-5 | Las pruebas se ejecutan desde `api/` con `python -m pytest`. Asumo que `python tools/lab.py test api` hace lo mismo, pero no lo sé. `conftest.py` añade `api/` a `sys.path` por seguridad. | Si el lab usa otro directorio o runner, la salida del lab puede diferir. Se reporta aparte. |
| T-6 | Versiones de Python y de `pytest`/`httpx`/`starlette` **no verificadas**. `TestClient` requiere `httpx`. Los pines no se inventan: se obtienen de `pip freeze` tras instalar (sección 7). | — |
| T-7 | El estado se guarda en `DATA_DIR`, que cada prueba redirige a `tmp_path` con `monkeypatch`. El servicio es un `lru_cache`, así que se limpia con `cache_clear()` antes y después. No hay subida de archivos en este feature, y el aislamiento aplica al directorio de estado. | — |
| T-8 | Las variables `MAX_BODY_BYTES`, `MAX_VERIFICATIONS_PER_OWNER` y `DATA_DIR` **no** están definidas en el entorno al ejecutar. Una prueba asume el valor por defecto 16384. | Esa prueba fallaría por el entorno, no por el código. |
| T-9 | Una prueba comprueba los permisos 0700 y solo es válida en POSIX (Linux/macOS). | En Windows esa prueba falla. Se descarta documentándolo, no se salta. |
| T-10 | El formato de `spend` (`{"amount_cents": n}`) sale del código de `monthly_analytics()`. Ningún endpoint lo escribe, así que las pruebas lo siembran en disco. | — |
| T-11 | El frontend usa Jasmine/Karma (por defecto en Angular 17) y los archivos `tsconfig.app.json`/`tsconfig.spec.json` estándar. P-2 sigue abierta. | Con Jest hay que adaptar `jasmine.createSpyObj` y `toBeFalse`. |
| T-12 | `TestClient` no ejerce el servidor real (`uvicorn`/h11). Lo cubren los pasos manuales de la Fase 4. La concurrencia se prueba a nivel de servicio. El 413 con `Content-Length` falso o no numérico se prueba con un arnés ASGI. | — |
| T-13 | **Los skips cuentan como NO cumplido.** Ninguna prueba usa `skip`, `skipif`, `xfail` ni variables de entorno opcionales. Las comprobaciones de dependencias (`pip-audit`) son pasos obligatorios de la Fase 5. | — |

## 2. Orden de ejecución

1. **Fase 0, preparación.** Entorno, dependencias y comprobación de que `api/data` no existe.
2. **Fase 1, línea base.** Corre toda la suite, existente y nueva, sobre la versión actual del árbol, antes de tocar nada.
   - Incluye `test_h01_baseline.py`, que caracteriza infraestructura que no depende de las reglas del cambio.
   - Una prueba que falle aquí se clasifica en una de dos categorías:
     - **defecto de la prueba:** se corrige o se descarta, documentándolo;
     - **defecto del producto:** se reporta a Backend o Frontend.
   - **Un fallo de línea base no se atribuye al cambio.**
   - Opcional: `git worktree` del commit anterior para comparar solo las pruebas existentes (sección 7).
3. **Fase 2, pruebas del cambio.** Se ejecutan por tarea (2.3, 2.4, 2.5, 2.7, 2.8) y transversales, y solo tras una línea base limpia.
4. **Fase 3, frontend.** Pruebas Angular.
5. **Fase 4, integración con servidor real.** `uvicorn` y `curl`.
6. **Fase 5, dependencias.** `pip check` y `pip-audit` obligatorios.

## 3. Matriz criterio → prueba → resultado esperado → estado

Las pruebas están en `api/tests/h01/` (`B`=baseline, `C`=console, `K`=kyc, `O`=onboarding, `E`=events_analytics, `P`=persistence, `S`=security, `R`=errors, `Q`=requirements). Las de frontend están en `src/app/core/h01-frontend.spec.ts` (`FE`).

| CA | Criterio | Prueba(s) | Resultado esperado | Estado |
|---|---|---|---|---|
| 2.1 | `user_story.md` revisado contra la spec | M-0 (manual): comparar CA derivados con `spec.md` | Cada CA corresponde a un requisito de la spec. | **NO EJECUTADO, bloqueado: falta `spec.md`** |
| CA-2.2a | Una interfaz de request y otra de response por endpoint | FE `MockApiService expone un método por endpoint`; `npx tsc --noEmit`; B `test_openapi_expone_las_rutas_del_contrato`; M-1 (comparar `api.models.ts` con `schemas.py`) | Los 9 métodos existen, el TS compila y el OpenAPI expone las 9 rutas. | NO EJECUTADO |
| CA-2.2b | Un único `SessionService` | FE `SessionService … misma instancia`; `grep` de la sección 7 | Dos inyecciones devuelven la misma instancia y no hay otra clase de sesión. | NO EJECUTADO |
| CA-2.3a | El estado de wallet es consistente | O `test_estado_inicial_de_un_propietario_nuevo`, `test_estado_es_estable_entre_lecturas`, `test_wallet_status_segun_ultima_verificacion` | `NOT_STARTED` al inicio. Con registro hecho: `KYC_PENDING`, `KYC_FAILED` (rechazada o expirada) o `IN_PROGRESS`. `ACTIVE` al activar. | NO EJECUTADO |
| CA-2.3b | Paso con requisito incumplido se bloquea | O `test_paso_bloqueado_sin_requisito_previo`, `test_kyc_bloqueado_segun_verificacion`, `test_verificacion_sin_registro_no_salta_el_bloqueo` | 409 `STEP_BLOCKED` y estado y eventos sin cambios. | NO EJECUTADO |
| CA-2.3c | Solo documentos `TEST-` | K `test_documento_rechazado`, `test_documento_valido_en_el_limite`, `test_documento_con_tipo_incorrecto`, `test_documento_rechazado_no_se_refleja_ni_toca_disco`; O `test_registro_con_documento_no_test`; FE `testDocumentValidator` | `TEST-…` válido da 201 o 200. Sin prefijo da 422 `DOCUMENT_NOT_TEST`. Sufijo, longitud o tipo inválidos dan 422 `VALIDATION_ERROR`. El valor no se refleja y no se escribe nada. | NO EJECUTADO |
| CA-2.3d | Mensajes accionables | R `test_mensajes_de_bloqueo_indican_la_accion`, `test_mensaje_de_documento_indica_el_prefijo`; K `test_limite_de_verificaciones_por_propietario`; FE `toApiErrorView` | El `message` contiene una instrucción: «Completa…», «Crea…», «Espera…» o «Usa POST /control/reset». La frase exacta queda sujeta a revisión humana. | NO EJECUTADO |
| CA-2.4a | `POST /kyc/verifications` con 4 escenarios | K `test_crear_verificacion_por_escenario[×4]`; C `test_scenarios_publica_los_cuatro_escenarios_sin_identidad` | 201. `status` es igual al escenario. `decided_at` es nulo solo en `PENDING`. `verification_id` es hex de 32 caracteres. | NO EJECUTADO |
| CA-2.4b | Consulta de verificación | K `test_consultar_verificacion_creada`, `test_consultar_verificacion_inexistente_404`; S `test_aislamiento_entre_propietarios_en_kyc` | 200 con el mismo cuerpo que al crear. Un id inexistente o de otro propietario da 404 `NOT_FOUND`. | NO EJECUTADO |
| CA-2.4c | Decisión sobre `PENDING` | K `test_decidir_pendiente[×2]`, `test_decidir_registra_decided_at`, `test_decidir_sobre_no_pendiente_409[×3]`, `test_decidir_dos_veces_409`, `test_decision_invalida_422[×3]`, `test_decidir_inexistente_404` | `PENDING` pasa a `APPROVED` o `REJECTED` con 200. No pendiente da 409 `VERIFICATION_NOT_PENDING`. Una decisión distinta de `APPROVED`/`REJECTED` da 422. | NO EJECUTADO |
| CA-2.5a | Eventos de inicio, paso y cierre | E `test_eventos_del_flujo_completo_en_orden`, `test_eventos_no_se_duplican_al_repetir_pasos`, `test_pasos_bloqueados_no_registran_eventos`, `test_eventos_no_tienen_endpoint_publico` | Eventos `ONBOARDING_STARTED`, `STEP_COMPLETED`×3 y `ONBOARDING_CLOSED` en orden. Sin duplicados. Sin endpoint público (S-6). | NO EJECUTADO |
| CA-2.5b | Cálculo de duración | E `test_duracion_sin_cierre_o_sin_inicio_es_none`, `test_duracion_con_milisegundos`, `test_duracion_expuesta_en_onboarding` | `None` sin cierre. `cierre − inicio` en segundos con 3 decimales (90.123 con reloj inyectado). | NO EJECUTADO |
| CA-2.6a | Pasos visibles y paso actual | FE `OnboardingComponent marca el paso actual`; M-2 (manual) | El `<li>` con `aria-current="step"` es el paso actual y muestra «Paso actual». | NO EJECUTADO |
| CA-2.6b | Pagos de bajo monto según estado de wallet | O `test_pagos_de_bajo_monto_solo_con_wallet_activa`; O `test_wallet_status_segun_ultima_verificacion` (campo `low_amount_payments_enabled`); FE `PagosComponent` | `true` solo con `ACTIVE`. La pantalla muestra «Acceso habilitado» o «Acceso bloqueado». | NO EJECUTADO |
| CA-2.7a | Consola: `/health`, `/scenarios`, `/support/cases` | B `test_health_responde_ok_sin_identidad`; C `test_scenarios_…`, `test_support_cases_*`; FE `ConsolaComponent ejecuta un servicio individual` | 200 con los cuerpos del contrato. `/support/cases` lista solo las no aprobadas. Ejecutar uno no llama a los otros. | NO EJECUTADO |
| CA-2.7b | Errores legibles | FE `muestra el message del API, no JSON crudo`; R (formato único) | Se renderiza el `message`. El DOM no contiene `{"code"`. | NO EJECUTADO |
| CA-2.7c | `POST /control/reset` con confirmación | C `test_reset_*`; P `test_reset_repara_estado_corrupto`; FE `reset: sin confirmar no llama al API` | La API borra solo el estado del propietario y es idempotente. Sin confirmar no se llama a `reset()`. | NO EJECUTADO |
| CA-2.8 | Analítica mensual | E `test_analitica_*` (5 pruebas) | Filas `{month,new_active_users,attributed_spend_cents}` por mes UTC de `closed_at`. Con el flujo HTTP el gasto es 0 (T-10). | NO EJECUTADO |
| CA-T1 | Sin identidad → 401; la identidad no viene del cliente | S `test_endpoints_con_identidad_responden_401_sin_cabecera[×8]`, `test_cabecera_invalida_responde_401[×6]`, `test_owner_en_cuerpo_se_rechaza`, `test_owner_en_query_se_ignora`, `test_identificador_en_el_limite_es_valido` | 401 `UNAUTHENTICATED` sin escribir en disco. Un `owner` en el cuerpo da 422. Un `owner` en la query se ignora. | NO EJECUTADO |
| CA-T2 | Cuerpo grande → 413 | S `test_cuerpo_exacto_al_limite…`, `test_limite_por_defecto…`, `test_413_sin_identidad`, `test_413_con_cuerpo_por_trozos`, `test_middleware_*[×5]` | El límite exacto pasa. Un byte más da 413 `PAYLOAD_TOO_LARGE`. Cabecera `Content-Length` no numérica da 400 `BAD_REQUEST`. | NO EJECUTADO |
| CA-T3 | No se expone `owner_id` ni hash | S `test_respuestas_no_exponen_owner_ni_hash`, `test_directorio_usa_solo_el_hash`; P `test_error_500_no_filtra_rutas_ni_hash`; E `test_analitica_no_expone_propietarios` | Ni cuerpos ni cabeceras contienen el id ni el hash. | NO EJECUTADO |
| CA-T4 | Concurrencia del mismo usuario | P `test_escrituras_concurrentes_del_mismo_propietario`, `test_pasos_concurrentes_no_duplican_eventos`, `test_concurrencia_con_propietarios_distintos`; M-4 (`xargs -P`) | JSON válido, 20 verificaciones únicas y eventos sin duplicar. | NO EJECUTADO |
| PERS | Contrato de persistencia | P `test_estado_se_guarda_en_directorio_derivado_del_hash`, `test_el_estado_persistido_tiene_el_esquema_esperado`, `test_directorio_del_propietario_es_privado` (T-9), `test_no_quedan_temporales_tras_escribir`, `test_fallo_de_escritura_no_deja_estado_parcial`, `test_archivo_preexistente_valido_se_reutiliza`, `test_estado_corrupto_devuelve_500_y_no_se_sobrescribe[×4]`, `test_temporal_huerfano_es_inofensivo` | `DATA_DIR/<sha256>/state.json` con `schema_version`=1 y las 6 claves. Los estados ilegibles dan 500 sin tocar el archivo. | NO EJECUTADO |
| DEP | Pines exactos de dependencias | Q `test_paquetes_clave_con_pin_exacto[×4]`, `test_ninguna_linea_usa_rangos`; `pip check`; `pip-audit` (Fase 5, obligatorio) | `paquete==versión` para `fastapi`, `starlette`, `uvicorn` y `pydantic`. `pip check` y `pip-audit` sin hallazgos o con hallazgos documentados. | NO EJECUTADO |
| SEC | Infraestructura de errores | B `test_error_no_controlado_devuelve_500_generico`, `test_ruta_inexistente…404`, `test_metodo_no_permitido…405`; R `test_todos_los_errores_usan_solo_code_y_message[×8]` | Todo error es exactamente `{"code","message"}`. Sin `detail` de FastAPI y sin trazas. | NO EJECUTADO |

## 4. Casos por tipo

| Tipo | Casos |
|---|---|
| **Positivos** | Crear verificación por escenario. Consultar y decidir `PENDING`. Registro `TEST-0001`. Flujo completo a `ACTIVE`. `/scenarios` y `/support/cases`. Reset y reinicio del flujo. Analítica por mes. Estado preexistente válido reutilizado. |
| **Negativos** | Sin identidad o identidad inválida. Documento sin `TEST-`, con sufijo inválido o con tipo incorrecto. Escenario o decisión inválidos. Campo desconocido (`owner`). JSON malformado. Paso bloqueado. Paso inexistente. Decidir una verificación no pendiente. `LIMIT_REACHED`. Estado corrupto, de versión desconocida o incompleto. Fallo de escritura. 413. |
| **Borde** | Documento de 64 caracteres (válido) y de 65 (inválido). `TEST-` sin sufijo. Salto de línea final en el documento. Identificador de 128 caracteres (válido) y de 129 (inválido). Cuerpo de exactamente el límite y de un byte más. `Content-Length` no numérico. Idempotencia al repetir un paso. Cierre de mes con zona horaria distinta de UTC. Estados ilegibles durante la analítica. Verificación creada antes del registro. |
| **Integración** | Recorrido completo `registro → KYC → activación` por HTTP con reloj inyectado. Duración calculada de extremo a extremo. Analítica alimentada por el flujo HTTP. Concurrencia sobre almacenamiento real en `tmp_path`. Aislamiento entre propietarios. Fase 4 contra `uvicorn` real. |

## 5. Contratos de API y persistencia (lista de comprobación)

- **Códigos HTTP y `code`:** 200 (reset, estado, decisión), 201 (creación), 401, 404, 405, 409 (`STEP_BLOCKED`, `VERIFICATION_NOT_PENDING`, `LIMIT_REACHED`), 413, 422 (`VALIDATION_ERROR`, `DOCUMENT_NOT_TEST`), 500 (`INTERNAL_ERROR`) y 400 (`BAD_REQUEST`). Todos se comprueban en R, K, O, S y P.
- **Formas de respuesta:** `VerificationResponse` (K), `OnboardingStateResponse` (O y E con comprobación de claves exactas) y `SupportCasesResponse` y `ScenariosResponse` (C).
- **Persistencia:** ruta, hash, esquema, atomicidad, no sobrescribir estados corruptos, reset y concurrencia (sección 3, fila PERS).

## 6. Observaciones de lectura del código (NO son resultados)

Son puntos a confirmar con Backend o Producto. No hay prueba que los dé por buenos o malos:
1. Una verificación `PENDING` creada **antes** del registro deja la wallet en `KYC_PENDING`, aunque aún no se haya registrado el usuario. La spec no lo define.
2. `DATA_DIR` por defecto es relativo (`data`) y depende del directorio de trabajo. Las pruebas lo aíslan, pero en ejecución real conviene una ruta absoluta.
3. El gasto atribuido (2.8) será 0 mientras no exista un origen de pagos (B-6, P-6).
4. Con más de un worker no hay bloqueo entre procesos (S-8), y no tengo una prueba para eso.
5. `ConsolaComponent.confirmReset()` no comprueba por sí mismo que haya confirmación previa; solo la plantilla lo garantiza. La prueba FE cubre el flujo de la interfaz, no la llamada directa.

## 7. Preparación, datos, comandos y limpieza

**Datos de prueba.**
- **Propietarios:** `usuario-1`, `usuario-2`, `propietario-secreto-777` y `u-*` (generados).
- **Documentos:** `TEST-0001` (válido) y la lista de inválidos de `test_h01_kyc.py`.
- **Reloj:** fijo en `2026-03-15T12:00:00+00:00` (fixture `clock`).
- **Estados sembrados** para la analítica, escritos con `OwnerStore.write`.

**Fase 0, preparación** (una vez):
```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install pytest httpx
# Si api/requirements-dev.txt ya existe, no dupliques líneas:
pip freeze | grep -iE '^(pytest|httpx)==' >> requirements-dev.txt
pip check
unset MAX_BODY_BYTES MAX_VERIFICATIONS_PER_OWNER DATA_DIR
test ! -e data && echo "api/data no existe (correcto antes de empezar)"
mkdir -p ../evidencia
python -m pytest --collect-only -q tests/h01 | tee ../evidencia/f0_coleccion.txt
```

**Fase 1, línea base** (todas las pruebas, existentes y nuevas, sobre la versión actual):
```bash
cd api
# 1a. Solo las pruebas existentes (si no hay, pytest informará "no tests ran"; adjuntar la salida)
python -m pytest tests --ignore=tests/h01 -rs -q --basetemp=.pytest_tmp \
  --junitxml=../evidencia/f1a_existentes.xml | tee ../evidencia/f1a_existentes.txt
# 1b. Todas, incluidas las nuevas
python -m pytest tests -rs -v --basetemp=.pytest_tmp \
  --junitxml=../evidencia/f1b_todas.xml | tee ../evidencia/f1b_todas.txt
# 1c. Vía laboratorio
cd .. && python tools/lab.py test api | tee evidencia/f1c_lab.txt
# Criterio: skipped debe ser 0 y api/data no debe existir
grep -o 'skipped="[0-9]*"' evidencia/f1b_todas.xml
test ! -e api/data && echo "aislamiento OK: api/data no fue creado"
```
Opcional, para comparar contra el commit anterior (solo las pruebas existentes; las nuevas no existen ahí):
```bash
git worktree add ../base-previo "$(git merge-base HEAD origin/main)"   # supuesto: rama base origin/main
cd ../base-previo/api && python -m pytest tests -q -rs | tee ../../evidencia/f1d_commit_previo.txt
cd ../../ && git worktree remove ../base-previo
```
Clasifica cada fallo como «defecto de prueba» (se corrige o se descarta) o «defecto de producto». No avances a la Fase 2 con fallos sin clasificar.

**Fase 2, pruebas del cambio** (solo tras línea base limpia):
```bash
cd api
python -m pytest tests/h01/test_h01_kyc.py -v          | tee ../evidencia/f2_kyc.txt          # 2.3c, 2.4
python -m pytest tests/h01/test_h01_onboarding.py -v   | tee ../evidencia/f2_onboarding.txt   # 2.3, 2.6b
python -m pytest tests/h01/test_h01_events_analytics.py -v | tee ../evidencia/f2_eventos.txt  # 2.5, 2.8
python -m pytest tests/h01/test_h01_console.py -v      | tee ../evidencia/f2_consola.txt      # 2.7
python -m pytest tests/h01/test_h01_security.py tests/h01/test_h01_persistence.py \
  tests/h01/test_h01_errors.py tests/h01/test_h01_requirements.py -v | tee ../evidencia/f2_transversales.txt
```

**Fase 3, frontend** (T-11):
```bash
grep -rnE "class \w*Session\w*" src/app          # CA-2.2b: debe aparecer solo SessionService
npx tsc --noEmit -p tsconfig.app.json            # CA-2.2a
npx tsc --noEmit -p tsconfig.spec.json
ng test --watch=false --browsers=ChromeHeadless | tee evidencia/f3_frontend.txt
```
Procedimientos manuales M-1 (comparar `api.models.ts` con `schemas.py` campo por campo) y M-2 (recorrido de `frontend_spec.md` §10) con capturas.

**Fase 4, integración con servidor real:**
```bash
export DATA_DIR="$(mktemp -d)"
cd api && uvicorn app.main:app --port 8000 &
SERVER_PID=$!; sleep 2; B=http://127.0.0.1:8000; H='X-Owner-Id: smoke-1'; J='Content-Type: application/json'
curl -s -w ' [%{http_code}]\n' $B/health                                   # esperado 200 {"status":"ok"}
curl -s -w ' [%{http_code}]\n' $B/onboarding                               # esperado 401 UNAUTHENTICATED
curl -s -w ' [%{http_code}]\n' -H "$H" -H "$J" -d '{"document_number":"12345678","scenario":"APPROVED"}' $B/kyc/verifications  # 422 DOCUMENT_NOT_TEST
curl -s -w ' [%{http_code}]\n' -H "$H" -H "$J" -d '{"document_number":"TEST-0001"}' $B/onboarding/steps/registro                # 200
curl -s -w ' [%{http_code}]\n' -H "$H" -X POST $B/onboarding/steps/activacion                                                   # 409 STEP_BLOCKED
head -c 20000 /dev/zero | tr '\0' 'a' | curl -s -w ' [%{http_code}]\n' -H "$H" -H "$J" --data-binary @- $B/kyc/verifications  # 413 PAYLOAD_TOO_LARGE
# M-4: concurrencia real, 20 POST PENDING en paralelo para el mismo propietario
seq 20 | xargs -P 10 -I{} curl -s -o /dev/null -H "$H" -H "$J" -d '{"document_number":"TEST-C{}","scenario":"PENDING"}' $B/kyc/verifications
curl -s -H "$H" $B/support/cases | python -c "import sys,json; print(len(json.load(sys.stdin)['cases']))"   # esperado 20
curl -s -w ' [%{http_code}]\n' -H "$H" -X POST $B/control/reset            # esperado 200 {"status":"reset"}
```
Adjunta la salida literal. Los valores marcados «esperado» no son resultados.

**Fase 5, dependencias** (obligatoria; requiere acceso a la red):
```bash
cd api
pip check | tee ../evidencia/f5_pipcheck.txt
pip index versions fastapi | tee ../evidencia/f5_index_fastapi.txt     # repetir para starlette, uvicorn y pydantic
pip install pip-audit && pip-audit -r requirements.txt | tee ../evidencia/f5_pipaudit.txt
```
Un hallazgo de `pip-audit` se reporta. No se cambia ningún pin sin que Backend lo acepte, y la prueba de pines debe seguir pasando.

**Limpieza.**
```bash
kill $SERVER_PID 2>/dev/null; rm -rf "$DATA_DIR" api/.pytest_tmp
unset DATA_DIR SERVER_PID
git status --porcelain      # solo deben aparecer archivos nuevos de api/tests/h01/, el spec TS, requirements-dev.txt y evidencia/
test ! -e api/data && echo "sin residuos de datos en api/data"
deactivate
```
Las pruebas pytest no dejan estado, porque `tmp_path` lo gestiona pytest y `DATA_DIR` apunta a él.

## 8. Evidencia a adjuntar

`f0_coleccion.txt`, `f1a`, `f1b`, `f1c`, `f2_*.txt`, `f3_frontend.txt`, la salida de la Fase 4, `f5_*.txt` y el `.xml` JUnit (con `skipped="0"`). Hasta que se adjunten, **todo permanece NO EJECUTADO**.

## 9. No cubierto o pendiente

- Verificar 2.1 contra `spec.md` (P-1).
- Hallazgos específicos de Seguridad, cuando se entreguen (T-3).
- Medición de cobertura: no incluida.
- Multiproceso (varios workers de `uvicorn`).
- CORS, pagos reales y umbral de «bajo monto» (P-6).
- Pruebas visuales y de accesibilidad automatizadas (solo la guía manual M-2).

---

# Código de las pruebas

```python
# api/tests/h01/conftest.py
"""Fixtures aisladas para las pruebas de H01.

- DATA_DIR se redirige a tmp_path con monkeypatch (nunca se escribe en api/data).
- El servicio (lru_cache) se limpia antes y después de cada prueba.
- El reloj es inyectable para fijar fechas y duraciones.
"""
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[2]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import config  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services import OnboardingService, get_onboarding_service  # noqa: E402
from app.storage import OwnerStore  # noqa: E402


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs) -> None:
        self.now += timedelta(**kwargs)


class Api:
    """Atajos sobre TestClient: siempre envían X-Owner-Id salvo que se use el cliente crudo."""

    owner = "usuario-1"
    other = "usuario-2"

    def __init__(self, client: TestClient) -> None:
        self.client = client

    def headers(self, owner=None) -> dict:
        return {"X-Owner-Id": owner or self.owner}

    def get(self, path, owner=None, **kw):
        return self.client.get(path, headers=self.headers(owner), **kw)

    def post(self, path, owner=None, **kw):
        return self.client.post(path, headers=self.headers(owner), **kw)

    def crear(self, scenario="APPROVED", doc="TEST-0001", owner=None) -> dict:
        r = self.post("/kyc/verifications", owner=owner, json={"document_number": doc, "scenario": scenario})
        assert r.status_code == 201, r.text
        return r.json()

    def registrar(self, owner=None, doc="TEST-0001") -> dict:
        r = self.post("/onboarding/steps/registro", owner=owner, json={"document_number": doc})
        assert r.status_code == 200, r.text
        return r.json()

    def completar_flujo(self, owner=None) -> dict:
        self.registrar(owner)
        self.crear("APPROVED", owner=owner)
        r = self.post("/onboarding/steps/kyc", owner=owner)
        assert r.status_code == 200, r.text
        r = self.post("/onboarding/steps/activacion", owner=owner)
        assert r.status_code == 200, r.text
        return r.json()


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    destino = tmp_path / "data"
    monkeypatch.setattr(config, "DATA_DIR", destino)
    get_onboarding_service.cache_clear()
    yield destino
    get_onboarding_service.cache_clear()


@pytest.fixture
def clock():
    return FakeClock(datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc))


@pytest.fixture
def store(data_dir):
    return OwnerStore(data_dir)


@pytest.fixture
def service(store, clock):
    return OnboardingService(store, clock)


@pytest.fixture
def build_client(service):
    """Crea una app NUEVA (lee config.MAX_BODY_BYTES en ese momento) con el servicio aislado."""

    def _build() -> TestClient:
        aplicacion = create_app()
        aplicacion.dependency_overrides[get_onboarding_service] = lambda: service
        return TestClient(aplicacion, raise_server_exceptions=False)

    return _build


@pytest.fixture
def client(build_client):
    return build_client()


@pytest.fixture
def api(client):
    return Api(client)


@pytest.fixture
def state_file(data_dir):
    def _ruta(owner_id: str) -> Path:
        return data_dir / hashlib.sha256(owner_id.encode("utf-8")).hexdigest() / "state.json"

    return _ruta


@pytest.fixture
def leer_estado(state_file):
    def _leer(owner_id: str) -> dict:
        return json.loads(state_file(owner_id).read_text(encoding="utf-8"))

    return _leer
```

```python
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
```

```python
# api/tests/h01/test_h01_requirements.py
"""Dependencias: pines exactos (paquete==versión), incluido starlette. Obligatorio, sin red."""
import re
from pathlib import Path

import pytest

REQUIREMENTS = Path(__file__).resolve().parents[2] / "requirements.txt"
PAQUETES_CLAVE = ("fastapi", "starlette", "uvicorn", "pydantic")


def _lineas() -> list:
    texto = REQUIREMENTS.read_text(encoding="utf-8")
    return [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith("#")]


def _nombre(linea: str) -> str:
    return re.split(r"[\[=<>!~;\s]", linea, maxsplit=1)[0].lower()


def test_requirements_existe_y_tiene_contenido():
    assert REQUIREMENTS.is_file(), f"No existe {REQUIREMENTS}"
    assert _lineas(), "requirements.txt está vacío"


@pytest.mark.parametrize("paquete", PAQUETES_CLAVE)
def test_paquetes_clave_con_pin_exacto(paquete):
    coincidencias = [l for l in _lineas() if _nombre(l) == paquete]
    assert len(coincidencias) == 1, f"{paquete}: se esperaba exactamente una línea, hay {coincidencias}"
    assert re.search(r"==\s*\d+(\.\d+)*", coincidencias[0]), f"{paquete} no está fijado con ==: {coincidencias[0]}"


def test_ninguna_linea_usa_rangos():
    opciones = [l for l in _lineas() if not l.startswith("-")]
    prohibidos = (">=", "<=", "~=", "!=", ">", "<", "^", "*")
    malas = [l for l in opciones if "==" not in l or any(p in l for p in prohibidos)]
    assert malas == [], f"Líneas sin pin exacto: {malas}"
```

```python
# api/tests/h01/test_h01_console.py
"""Tarea 2.7 (lado API): /scenarios, /support/cases y /control/reset."""


def test_scenarios_publica_los_cuatro_escenarios_sin_identidad(client):
    r = client.get("/scenarios")
    assert r.status_code == 200
    items = r.json()["scenarios"]
    assert len(items) == 4
    assert {i["name"] for i in items} == {"APPROVED", "REJECTED", "PENDING", "EXPIRED"}
    assert all(set(i) == {"name", "description"} and i["description"].strip() for i in items)


def test_support_cases_vacio_para_propietario_nuevo(api, data_dir):
    r = api.get("/support/cases")
    assert r.status_code == 200
    assert r.json() == {"cases": []}
    assert not data_dir.exists()


def test_support_cases_lista_solo_las_no_aprobadas(api):
    ids = {s: api.crear(s)["verification_id"] for s in ("APPROVED", "REJECTED", "PENDING", "EXPIRED")}
    casos = api.get("/support/cases").json()["cases"]
    assert {c["verification_id"]: c["status"] for c in casos} == {
        ids["REJECTED"]: "REJECTED",
        ids["PENDING"]: "PENDING",
        ids["EXPIRED"]: "EXPIRED",
    }
    assert all(set(c) == {"verification_id", "status", "message"} and c["message"].strip() for c in casos)


def test_support_cases_no_mezcla_propietarios(api):
    api.crear("PENDING", owner=api.owner)
    assert api.get("/support/cases", owner=api.other).json() == {"cases": []}


def test_reset_devuelve_el_estado_inicial(api, state_file):
    api.registrar()
    api.crear("PENDING")
    assert state_file(api.owner).exists()
    r = api.post("/control/reset")
    assert r.status_code == 200
    assert r.json() == {"status": "reset"}
    assert not state_file(api.owner).exists()
    estado = api.get("/onboarding").json()
    assert estado["wallet_status"] == "NOT_STARTED"
    assert estado["current_step"] == "registro"
    assert api.get("/support/cases").json() == {"cases": []}


def test_reset_es_idempotente(api):
    assert api.post("/control/reset").status_code == 200  # sin estado previo
    api.registrar()
    assert api.post("/control/reset").status_code == 200
    assert api.post("/control/reset").status_code == 200


def test_reset_solo_afecta_al_propietario_autenticado(api, state_file):
    api.registrar(owner=api.owner)
    api.registrar(owner=api.other)
    assert api.post("/control/reset", owner=api.owner).status_code == 200
    assert not state_file(api.owner).exists()
    assert state_file(api.other).exists()
    assert api.get("/onboarding", owner=api.other).json()["current_step"] == "kyc"
```

```python
# api/tests/h01/test_h01_kyc.py
"""Tareas 2.3c y 2.4: KYC con cuatro escenarios, consulta, decisión y documento TEST-."""
import re
from datetime import datetime

import pytest

ESCENARIOS = ["APPROVED", "REJECTED", "PENDING", "EXPIRED"]

DOCUMENTOS_INVALIDOS = [
    ("12345678", "DOCUMENT_NOT_TEST"),
    ("test-123", "DOCUMENT_NOT_TEST"),
    ("Test-123", "DOCUMENT_NOT_TEST"),
    (" TEST-123", "DOCUMENT_NOT_TEST"),
    ("TEST", "DOCUMENT_NOT_TEST"),
    ("TEST-", "VALIDATION_ERROR"),
    ("TEST-a b", "VALIDATION_ERROR"),
    ("TEST-ñandú", "VALIDATION_ERROR"),
    ("TEST-0001\n", "VALIDATION_ERROR"),
    ("TEST-../x", "VALIDATION_ERROR"),
    ("TEST-" + "A" * 60, "VALIDATION_ERROR"),  # 65 caracteres: lo corta el esquema
    ("", "VALIDATION_ERROR"),
]


def _iso(valor: str) -> datetime:
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def _post_kyc(api, cuerpo, owner=None):
    return api.post("/kyc/verifications", owner=owner, json=cuerpo)


# ---------- Positivos ----------
@pytest.mark.parametrize("escenario", ESCENARIOS)
def test_crear_verificacion_por_escenario(api, clock, escenario):
    r = _post_kyc(api, {"document_number": "TEST-0001", "scenario": escenario})
    assert r.status_code == 201
    v = r.json()
    assert set(v) == {"verification_id", "document_number", "scenario", "status", "created_at", "decided_at"}
    assert re.fullmatch(r"[0-9a-f]{32}", v["verification_id"])
    assert v["scenario"] == escenario
    assert v["status"] == escenario
    assert _iso(v["created_at"]) == clock.now
    if escenario == "PENDING":
        assert v["decided_at"] is None
    else:
        assert _iso(v["decided_at"]) == clock.now


def test_consultar_verificacion_creada(api):
    creada = api.crear("PENDING")
    r = api.get(f"/kyc/verifications/{creada['verification_id']}")
    assert r.status_code == 200
    assert r.json() == creada


@pytest.mark.parametrize("decision", ["APPROVED", "REJECTED"])
def test_decidir_pendiente(api, decision):
    creada = api.crear("PENDING")
    r = api.post(f"/kyc/verifications/{creada['verification_id']}/decision", json={"decision": decision})
    assert r.status_code == 200
    assert r.json()["status"] == decision
    assert r.json()["decided_at"] is not None
    consultada = api.get(f"/kyc/verifications/{creada['verification_id']}").json()
    assert consultada["status"] == decision


def test_decidir_registra_decided_at(api, clock):
    creada = api.crear("PENDING")
    clock.advance(minutes=5)
    r = api.post(f"/kyc/verifications/{creada['verification_id']}/decision", json={"decision": "APPROVED"})
    assert (_iso(r.json()["decided_at"]) - _iso(r.json()["created_at"])).total_seconds() == 300


def test_documento_valido_en_el_limite(api):
    doc = "TEST-" + "A" * 59  # 64 caracteres: máximo permitido
    r = _post_kyc(api, {"document_number": doc, "scenario": "APPROVED"})
    assert r.status_code == 201
    assert r.json()["document_number"] == doc


# ---------- Negativos ----------
def test_consultar_verificacion_inexistente_404(api):
    r = api.get("/kyc/verifications/" + "0" * 32)
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"


@pytest.mark.parametrize("escenario", ["APPROVED", "REJECTED", "EXPIRED"])
def test_decidir_sobre_no_pendiente_409(api, escenario):
    creada = api.crear(escenario)
    r = api.post(f"/kyc/verifications/{creada['verification_id']}/decision", json={"decision": "APPROVED"})
    assert r.status_code == 409
    assert r.json()["code"] == "VERIFICATION_NOT_PENDING"
    # El estado no cambió.
    assert api.get(f"/kyc/verifications/{creada['verification_id']}").json()["status"] == escenario


def test_decidir_dos_veces_409(api):
    creada = api.crear("PENDING")
    ruta = f"/kyc/verifications/{creada['verification_id']}/decision"
    assert api.post(ruta, json={"decision": "REJECTED"}).status_code == 200
    segunda = api.post(ruta, json={"decision": "APPROVED"})
    assert segunda.status_code == 409
    assert segunda.json()["code"] == "VERIFICATION_NOT_PENDING"
    assert api.get(f"/kyc/verifications/{creada['verification_id']}").json()["status"] == "REJECTED"


@pytest.mark.parametrize("decision", ["PENDING", "EXPIRED", "aprobar"])
def test_decision_invalida_422(api, decision):
    creada = api.crear("PENDING")
    r = api.post(f"/kyc/verifications/{creada['verification_id']}/decision", json={"decision": decision})
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"
    assert api.get(f"/kyc/verifications/{creada['verification_id']}").json()["status"] == "PENDING"


def test_decidir_inexistente_404(api):
    r = api.post("/kyc/verifications/" + "f" * 32 + "/decision", json={"decision": "APPROVED"})
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"


@pytest.mark.parametrize("documento,codigo", DOCUMENTOS_INVALIDOS)
def test_documento_rechazado(api, documento, codigo):
    r = _post_kyc(api, {"document_number": documento, "scenario": "APPROVED"})
    assert r.status_code == 422
    assert r.json()["code"] == codigo
    assert set(r.json()) == {"code", "message"}


@pytest.mark.parametrize("documento", ["12345678", "test-123", "TEST-a b", "TEST-ñandú", "999-SECRETO-999"])
def test_documento_rechazado_no_se_refleja_ni_toca_disco(api, data_dir, documento):
    r = _post_kyc(api, {"document_number": documento, "scenario": "APPROVED"})
    assert r.status_code == 422
    assert documento not in r.text
    assert not data_dir.exists()  # la validación ocurre antes de abrir archivos


@pytest.mark.parametrize("valor", [123, None, ["TEST-1"], {"a": 1}])
def test_documento_con_tipo_incorrecto(api, valor):
    r = _post_kyc(api, {"document_number": valor, "scenario": "APPROVED"})
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"document_number": "TEST-0001", "scenario": "APPROVE"},
        {"document_number": "TEST-0001", "scenario": "approved"},
        {"document_number": "TEST-0001"},
        {"scenario": "APPROVED"},
        {},
    ],
)
def test_escenario_invalido_o_ausente_422(api, cuerpo):
    r = _post_kyc(api, cuerpo)
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"


def test_campo_desconocido_rechazado(api, data_dir):
    r = _post_kyc(api, {"document_number": "TEST-0001", "scenario": "APPROVED", "owner": "otro"})
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"
    assert "owner" in r.json()["message"]  # solo el nombre del campo, no el valor
    assert "otro" not in r.json()["message"]
    assert not data_dir.exists()


def test_json_malformado_usa_formato_unico(client):
    r = client.post(
        "/kyc/verifications",
        content=b"{no es json",
        headers={"X-Owner-Id": "usuario-1", "Content-Type": "application/json"},
    )
    assert r.status_code == 422
    cuerpo = r.json()
    assert set(cuerpo) == {"code", "message"}
    assert cuerpo["code"] == "VALIDATION_ERROR"
    assert "detail" not in cuerpo


# ---------- Borde ----------
def test_limite_de_verificaciones_por_propietario(api, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "MAX_VERIFICATIONS_PER_OWNER", 3)
    for _ in range(3):
        api.crear("PENDING")
    r = _post_kyc(api, {"document_number": "TEST-0001", "scenario": "PENDING"})
    assert r.status_code == 409
    assert r.json()["code"] == "LIMIT_REACHED"
    assert "reset" in r.json()["message"]
    # No afecta a otro propietario.
    assert _post_kyc(api, {"document_number": "TEST-0001", "scenario": "PENDING"}, owner=api.other).status_code == 201


def test_reset_libera_el_limite(api, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "MAX_VERIFICATIONS_PER_OWNER", 2)
    api.crear("PENDING")
    api.crear("PENDING")
    assert _post_kyc(api, {"document_number": "TEST-0001", "scenario": "PENDING"}).status_code == 409
    assert api.post("/control/reset").status_code == 200
    assert _post_kyc(api, {"document_number": "TEST-0001", "scenario": "PENDING"}).status_code == 201
```

```python
# api/tests/h01/test_h01_onboarding.py
"""Tareas 2.3 y 2.6b (lado API): estado de wallet, pasos con bloqueo e integración."""
import pytest


def _estados(r):
    return [s["status"] for s in r["steps"]]


# ---------- Estado ----------
def test_estado_inicial_de_un_propietario_nuevo(api, data_dir):
    r = api.get("/onboarding")
    assert r.status_code == 200
    e = r.json()
    assert set(e) == {"wallet_status", "current_step", "steps", "low_amount_payments_enabled", "duration_seconds"}
    assert e["wallet_status"] == "NOT_STARTED"
    assert e["current_step"] == "registro"
    assert [s["id"] for s in e["steps"]] == ["registro", "kyc", "activacion"]
    assert [s["order"] for s in e["steps"]] == [1, 2, 3]
    assert _estados(e) == ["CURRENT", "LOCKED", "LOCKED"]
    assert e["low_amount_payments_enabled"] is False
    assert e["duration_seconds"] is None
    assert not data_dir.exists()  # leer no escribe


def test_estado_es_estable_entre_lecturas(api):
    api.registrar()
    primero = api.get("/onboarding").json()
    assert api.get("/onboarding").json() == primero


@pytest.mark.parametrize(
    "escenario,wallet",
    [("PENDING", "KYC_PENDING"), ("REJECTED", "KYC_FAILED"), ("EXPIRED", "KYC_FAILED"), ("APPROVED", "IN_PROGRESS")],
)
def test_wallet_status_segun_ultima_verificacion(api, escenario, wallet):
    api.registrar()
    api.crear(escenario)
    e = api.get("/onboarding").json()
    assert e["wallet_status"] == wallet
    assert e["low_amount_payments_enabled"] is False


# ---------- Bloqueo ----------
@pytest.mark.parametrize("paso,mencionado", [("kyc", "registro"), ("activacion", "kyc")])
def test_paso_bloqueado_sin_requisito_previo(api, data_dir, paso, mencionado):
    r = api.post(f"/onboarding/steps/{paso}")
    assert r.status_code == 409
    assert r.json()["code"] == "STEP_BLOCKED"
    assert mencionado in r.json()["message"]
    assert not data_dir.exists()  # un paso bloqueado no escribe nada


@pytest.mark.parametrize(
    "escenario,fragmento",
    [
        (None, "POST /kyc/verifications"),
        ("PENDING", "pendiente"),
        ("REJECTED", "no fue aprobada"),
        ("EXPIRED", "no fue aprobada"),
    ],
)
def test_kyc_bloqueado_segun_verificacion(api, leer_estado, escenario, fragmento):
    api.registrar()
    if escenario:
        api.crear(escenario)
    r = api.post("/onboarding/steps/kyc")
    assert r.status_code == 409
    assert r.json()["code"] == "STEP_BLOCKED"
    assert fragmento in r.json()["message"]
    estado = api.get("/onboarding").json()
    assert _estados(estado) == ["COMPLETED", "CURRENT", "LOCKED"]
    assert len(leer_estado(api.owner)["events"]) == 2  # solo inicio + registro


def test_verificacion_sin_registro_no_salta_el_bloqueo(api):
    api.crear("APPROVED")
    r = api.post("/onboarding/steps/kyc")
    assert r.status_code == 409
    assert r.json()["code"] == "STEP_BLOCKED"
    assert "registro" in r.json()["message"]
    e = api.get("/onboarding").json()
    assert e["wallet_status"] == "IN_PROGRESS"
    assert e["current_step"] == "registro"


# ---------- Registro y validación ----------
def test_registro_exige_documento(api):
    for kwargs in ({}, {"json": {}}):
        r = api.post("/onboarding/steps/registro", **kwargs)
        assert r.status_code == 422
        assert r.json()["code"] == "VALIDATION_ERROR"
        assert "TEST-" in r.json()["message"]


def test_registro_con_documento_no_test(api, data_dir):
    r = api.post("/onboarding/steps/registro", json={"document_number": "12345678"})
    assert r.status_code == 422
    assert r.json()["code"] == "DOCUMENT_NOT_TEST"
    assert "12345678" not in r.text
    assert not data_dir.exists()


def test_registro_completa_el_primer_paso(api):
    e = api.registrar()
    assert e["wallet_status"] == "IN_PROGRESS"
    assert e["current_step"] == "kyc"
    assert _estados(e) == ["COMPLETED", "CURRENT", "LOCKED"]


def test_registro_no_guarda_el_documento(api, state_file):
    api.registrar(doc="TEST-SOLO-REGISTRO")
    assert "TEST-SOLO-REGISTRO" not in state_file(api.owner).read_text(encoding="utf-8")


@pytest.mark.parametrize("paso", ["kyc", "activacion"])
def test_pasos_distintos_de_registro_rechazan_documento(api, paso):
    r = api.post(f"/onboarding/steps/{paso}", json={"document_number": "TEST-0001"})
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"


def test_paso_inexistente_404(api):
    r = api.post("/onboarding/steps/inexistente")
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"
    assert "registro" in r.json()["message"]


# ---------- Integración ----------
def test_pendiente_aprobada_permite_continuar(api):
    api.registrar()
    v = api.crear("PENDING")
    assert api.post("/onboarding/steps/kyc").status_code == 409
    assert api.post(f"/kyc/verifications/{v['verification_id']}/decision", json={"decision": "APPROVED"}).status_code == 200
    r = api.post("/onboarding/steps/kyc")
    assert r.status_code == 200
    assert r.json()["current_step"] == "activacion"
    assert _estados(r.json()) == ["COMPLETED", "COMPLETED", "CURRENT"]


def test_rechazada_y_nueva_aprobada(api):
    api.registrar()
    api.crear("REJECTED")
    assert api.get("/onboarding").json()["wallet_status"] == "KYC_FAILED"
    assert api.post("/onboarding/steps/kyc").status_code == 409
    api.crear("APPROVED")  # cuenta la última verificación
    assert api.post("/onboarding/steps/kyc").status_code == 200


def test_recorrido_completo_activa_la_wallet(api, clock):
    api.registrar()
    api.crear("APPROVED")
    assert api.post("/onboarding/steps/kyc").status_code == 200
    clock.advance(seconds=42, milliseconds=500)
    final = api.post("/onboarding/steps/activacion")
    assert final.status_code == 200
    e = final.json()
    assert e["wallet_status"] == "ACTIVE"
    assert e["current_step"] is None
    assert _estados(e) == ["COMPLETED", "COMPLETED", "COMPLETED"]
    assert e["low_amount_payments_enabled"] is True
    assert e["duration_seconds"] == 42.5
    assert api.get("/onboarding").json() == e


def test_pagos_de_bajo_monto_solo_con_wallet_activa(api):
    assert api.get("/onboarding").json()["low_amount_payments_enabled"] is False
    assert api.registrar()["low_amount_payments_enabled"] is False
    api.crear("APPROVED")
    assert api.post("/onboarding/steps/kyc").json()["low_amount_payments_enabled"] is False
    assert api.post("/onboarding/steps/activacion").json()["low_amount_payments_enabled"] is True
    assert api.post("/control/reset").status_code == 200
    assert api.get("/onboarding").json()["low_amount_payments_enabled"] is False


def test_repetir_un_paso_completado_es_idempotente(api, leer_estado):
    api.registrar()
    assert api.registrar() == api.get("/onboarding").json()
    api.crear("APPROVED")
    primero = api.post("/onboarding/steps/kyc")
    segundo = api.post("/onboarding/steps/kyc")
    assert primero.status_code == segundo.status_code == 200
    assert primero.json() == segundo.json()
    assert len(leer_estado(api.owner)["events"]) == 3  # inicio, registro, kyc: sin duplicados


def test_propietarios_aislados(api):
    api.completar_flujo(owner=api.owner)
    otro = api.get("/onboarding", owner=api.other).json()
    assert otro["wallet_status"] == "NOT_STARTED"
    assert otro["current_step"] == "registro"
```

```python
# api/tests/h01/test_h01_events_analytics.py
"""Tareas 2.5 (eventos y duración) y 2.8 (analítica mensual)."""
from datetime import datetime

from app.services import compute_duration_seconds
from app.storage import default_state


# ---------- Duración ----------
def test_duracion_sin_cierre_o_sin_inicio_es_none():
    assert compute_duration_seconds(None, None) is None
    assert compute_duration_seconds("2026-03-15T12:00:00+00:00", None) is None
    assert compute_duration_seconds(None, "2026-03-15T12:00:00+00:00") is None


def test_duracion_con_milisegundos():
    assert compute_duration_seconds("2026-03-15T12:00:00+00:00", "2026-03-15T12:01:30.123000+00:00") == 90.123
    assert compute_duration_seconds("2026-03-15T12:00:00+00:00", "2026-03-15T12:00:00+00:00") == 0.0


def test_duracion_expuesta_en_onboarding(api, clock):
    api.registrar()
    api.crear("APPROVED")
    assert api.post("/onboarding/steps/kyc").status_code == 200
    assert api.get("/onboarding").json()["duration_seconds"] is None  # sin cierre
    clock.advance(seconds=90, milliseconds=123)
    final = api.post("/onboarding/steps/activacion").json()
    assert final["duration_seconds"] == 90.123
    assert api.get("/onboarding").json()["duration_seconds"] == 90.123


# ---------- Eventos ----------
def test_eventos_del_flujo_completo_en_orden(api, clock, leer_estado):
    api.registrar()
    clock.advance(seconds=1)
    api.crear("APPROVED")
    api.post("/onboarding/steps/kyc")
    clock.advance(seconds=1)
    api.post("/onboarding/steps/activacion")
    estado = leer_estado(api.owner)
    assert [(e["type"], e["step"]) for e in estado["events"]] == [
        ("ONBOARDING_STARTED", None),
        ("STEP_COMPLETED", "registro"),
        ("STEP_COMPLETED", "kyc"),
        ("STEP_COMPLETED", "activacion"),
        ("ONBOARDING_CLOSED", None),
    ]
    instantes = [datetime.fromisoformat(e["at"]) for e in estado["events"]]
    assert instantes == sorted(instantes)
    assert estado["started_at"] == estado["events"][0]["at"]
    assert estado["closed_at"] == estado["events"][-1]["at"]


def test_eventos_no_se_duplican_al_repetir_pasos(api, leer_estado):
    api.registrar()
    api.registrar()
    api.crear("APPROVED")
    api.post("/onboarding/steps/kyc")
    api.post("/onboarding/steps/kyc")
    assert len(leer_estado(api.owner)["events"]) == 3


def test_pasos_bloqueados_no_registran_eventos(api, leer_estado, state_file):
    assert api.post("/onboarding/steps/kyc").status_code == 409
    assert not state_file(api.owner).exists()
    api.registrar()
    assert api.post("/onboarding/steps/activacion").status_code == 409
    assert len(leer_estado(api.owner)["events"]) == 2


def test_eventos_no_tienen_endpoint_publico(api):
    for ruta in ("/events", "/onboarding/events", "/analytics", "/analytics/monthly"):
        r = api.get(ruta)
        assert r.status_code == 404
        assert r.json()["code"] == "NOT_FOUND"
    assert "events" not in api.get("/onboarding").json()


# ---------- Analítica mensual (2.8) ----------
def _estado_cerrado(closed_at, gasto=()):
    s = default_state()
    s["started_at"] = "2026-01-01T00:00:00+00:00"
    s["closed_at"] = closed_at
    s["steps_completed"] = ["registro", "kyc", "activacion"]
    s["spend"] = [{"amount_cents": c} for c in gasto]
    return s


def test_analitica_sin_estados_devuelve_lista_vacia(service):
    assert service.monthly_analytics() == []


def test_analitica_agrupa_por_mes_utc(service, store):
    store.write("u1", _estado_cerrado("2026-01-10T10:00:00+00:00", gasto=(500, 250)))
    store.write("u2", _estado_cerrado("2026-01-31T23:59:59+00:00", gasto=(100,)))
    store.write("u3", _estado_cerrado("2026-02-01T00:00:00+00:00"))
    sin_cerrar = _estado_cerrado(None, gasto=(999,))
    sin_cerrar["steps_completed"] = ["registro"]
    store.write("u4", sin_cerrar)  # no cerró: no cuenta ni su gasto
    filas = [f.model_dump() for f in service.monthly_analytics()]
    assert filas == [
        {"month": "2026-01", "new_active_users": 2, "attributed_spend_cents": 850},
        {"month": "2026-02", "new_active_users": 1, "attributed_spend_cents": 0},
    ]


def test_analitica_borde_de_zona_horaria(service, store):
    store.write("a", _estado_cerrado("2026-02-28T23:30:00-05:00"))  # = 2026-03-01 04:30 UTC
    store.write("b", _estado_cerrado("2026-01-31T19:00:00-05:00"))  # = 2026-02-01 00:00 UTC
    filas = [f.model_dump() for f in service.monthly_analytics()]
    assert [(f["month"], f["new_active_users"]) for f in filas] == [("2026-02", 1), ("2026-03", 1)]


def test_analitica_ignora_estados_ilegibles(service, store, data_dir):
    store.write("ok", _estado_cerrado("2026-01-10T10:00:00+00:00", gasto=(300,)))
    corrupto = data_dir / "zz-corrupto"
    corrupto.mkdir()
    (corrupto / "state.json").write_text("{no es json", encoding="utf-8")
    (data_dir / "notas.txt").write_text("archivo suelto", encoding="utf-8")
    filas = [f.model_dump() for f in service.monthly_analytics()]
    assert filas == [{"month": "2026-01", "new_active_users": 1, "attributed_spend_cents": 300}]


def test_analitica_integrada_con_el_flujo_http(api, service):
    api.completar_flujo(owner=api.owner)
    api.completar_flujo(owner=api.other)
    api.registrar(owner="usuario-3")  # no cierra
    filas = [f.model_dump() for f in service.monthly_analytics()]
    # Ningún endpoint escribe `spend`: el gasto atribuido es 0 hasta que exista origen de pagos (T-10).
    assert filas == [{"month": "2026-03", "new_active_users": 2, "attributed_spend_cents": 0}]


def test_analitica_no_expone_propietarios(service, store):
    store.write("propietario-secreto-777", _estado_cerrado("2026-01-10T10:00:00+00:00"))
    for fila in service.monthly_analytics():
        assert set(fila.model_dump()) == {"month", "new_active_users", "attributed_spend_cents"}
        assert "propietario-secreto-777" not in fila.model_dump_json()
```

```python
# api/tests/h01/test_h01_persistence.py
"""Contrato de persistencia: ruta, esquema, atomicidad, estados ilegibles y concurrencia."""
import hashlib
import json
import stat
from concurrent.futures import ThreadPoolExecutor

import pytest

from app import storage
from app.schemas import KycScenario
from app.storage import default_state

CLAVES = {"schema_version", "started_at", "closed_at", "steps_completed", "verifications", "events", "spend"}

ESTADOS_ILEGIBLES = {
    "no_json": "{esto no es json",
    "version_desconocida": json.dumps({**default_state(), "schema_version": 99}),
    "incompleto": json.dumps({"schema_version": 1, "started_at": None}),
    "no_objeto": "[]",
}


def _sembrar(state_file, owner, contenido):
    ruta = state_file(owner)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


# ---------- Ruta y esquema ----------
def test_estado_se_guarda_en_directorio_derivado_del_hash(api, data_dir):
    api.registrar()
    digest = hashlib.sha256(api.owner.encode("utf-8")).hexdigest()
    assert (data_dir / digest / "state.json").is_file()
    assert [p.name for p in data_dir.iterdir()] == [digest]


def test_el_estado_persistido_tiene_el_esquema_esperado(api, leer_estado):
    api.registrar()
    api.crear("PENDING")
    estado = leer_estado(api.owner)
    assert set(estado) == CLAVES
    assert estado["schema_version"] == 1
    assert estado["steps_completed"] == ["registro"]
    assert len(estado["verifications"]) == 1
    assert estado["closed_at"] is None
    assert estado["spend"] == []


def test_directorio_del_propietario_es_privado(api, state_file):  # POSIX (T-9)
    api.registrar()
    modo = stat.S_IMODE(state_file(api.owner).parent.stat().st_mode)
    assert modo & 0o077 == 0, oct(modo)


def test_no_quedan_temporales_tras_escribir(api, state_file):
    api.registrar()
    api.crear("PENDING")
    api.crear("APPROVED")
    nombres = sorted(p.name for p in state_file(api.owner).parent.iterdir())
    assert nombres == ["state.json"]


# ---------- Atomicidad ----------
def test_fallo_de_escritura_no_deja_estado_parcial(api, state_file, monkeypatch):
    def falla(*args, **kwargs):
        raise OSError("disco lleno simulado")

    with monkeypatch.context() as m:
        m.setattr(storage.os, "replace", falla)
        r = api.post("/kyc/verifications", json={"document_number": "TEST-0001", "scenario": "APPROVED"})
    assert r.status_code == 500
    assert r.json() == {
        "code": "INTERNAL_ERROR",
        "message": "Ocurrió un error interno. Inténtalo de nuevo más tarde.",
    }
    assert "disco lleno" not in r.text
    directorio = state_file(api.owner).parent
    assert not state_file(api.owner).exists()
    assert list(directorio.glob(".state-*")) == []
    assert api.get("/support/cases").json() == {"cases": []}


# ---------- Archivos preexistentes ----------
def test_archivo_preexistente_valido_se_reutiliza(api, state_file):
    previo = default_state()
    previo["started_at"] = "2026-01-01T00:00:00+00:00"
    previo["steps_completed"] = ["registro"]
    previo["events"] = [
        {"type": "ONBOARDING_STARTED", "step": None, "at": "2026-01-01T00:00:00+00:00"},
        {"type": "STEP_COMPLETED", "step": "registro", "at": "2026-01-01T00:00:00+00:00"},
    ]
    _sembrar(state_file, api.owner, json.dumps(previo))
    e = api.get("/onboarding").json()
    assert e["current_step"] == "kyc"
    assert e["wallet_status"] == "IN_PROGRESS"


@pytest.mark.parametrize("contenido", list(ESTADOS_ILEGIBLES.values()), ids=list(ESTADOS_ILEGIBLES))
def test_estado_corrupto_devuelve_500_y_no_se_sobrescribe(api, state_file, contenido):
    ruta = _sembrar(state_file, api.owner, contenido)
    lectura = api.get("/onboarding")
    assert lectura.status_code == 500
    assert lectura.json()["code"] == "INTERNAL_ERROR"
    escritura = api.post("/kyc/verifications", json={"document_number": "TEST-0001", "scenario": "APPROVED"})
    assert escritura.status_code == 500
    assert escritura.json()["code"] == "INTERNAL_ERROR"
    assert ruta.read_text(encoding="utf-8") == contenido  # no se sobrescribió


def test_error_500_no_filtra_rutas_ni_hash(api, state_file, data_dir):
    _sembrar(state_file, api.owner, "{corrupto")
    r = api.get("/onboarding")
    assert r.status_code == 500
    digest = hashlib.sha256(api.owner.encode("utf-8")).hexdigest()
    for prohibido in (str(data_dir), digest, api.owner, "state.json", "Traceback", "JSON"):
        assert prohibido not in r.text


def test_reset_repara_estado_corrupto(api, state_file):
    _sembrar(state_file, api.owner, "{corrupto")
    assert api.get("/onboarding").status_code == 500
    assert api.post("/control/reset").status_code == 200
    assert api.get("/onboarding").json()["wallet_status"] == "NOT_STARTED"


def test_temporal_huerfano_es_inofensivo(api, state_file):
    api.registrar()
    huerfano = state_file(api.owner).parent / ".state-huerfano.tmp"
    huerfano.write_text("basura", encoding="utf-8")
    assert api.get("/onboarding").json()["current_step"] == "kyc"
    api.crear("PENDING")
    assert api.get("/support/cases").status_code == 200
    assert huerfano.exists()  # no se lee ni se borra automáticamente


# ---------- Concurrencia (a nivel de servicio; T-12) ----------
def test_escrituras_concurrentes_del_mismo_propietario(service, state_file):
    total = 20
    with ThreadPoolExecutor(max_workers=10) as pool:
        resultados = list(
            pool.map(
                lambda i: service.create_verification("usuario-c", f"TEST-{i:04d}", KycScenario.PENDING),
                range(total),
            )
        )
    ids = {r.verification_id for r in resultados}
    assert len(ids) == total
    estado = json.loads(state_file("usuario-c").read_text(encoding="utf-8"))  # JSON válido
    assert {v["verification_id"] for v in estado["verifications"]} == ids
    assert len(estado["verifications"]) == total


def test_pasos_concurrentes_no_duplican_eventos(service, state_file):
    with ThreadPoolExecutor(max_workers=10) as pool:
        resultados = list(pool.map(lambda _: service.submit_step("usuario-c", "registro", "TEST-0001"), range(10)))
    assert all(r.current_step == "kyc" for r in resultados)
    estado = json.loads(state_file("usuario-c").read_text(encoding="utf-8"))
    assert estado["steps_completed"] == ["registro"]
    assert [(e["type"], e["step"]) for e in estado["events"]] == [
        ("ONBOARDING_STARTED", None),
        ("STEP_COMPLETED", "registro"),
    ]


def test_concurrencia_con_propietarios_distintos(service, state_file):
    propietarios = [f"u-{i}" for i in range(16)]

    def trabajo(owner):
        for n in range(3):
            service.create_verification(owner, f"TEST-{n}", KycScenario.PENDING)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(trabajo, propietarios))
    for owner in propietarios:
        estado = json.loads(state_file(owner).read_text(encoding="utf-8"))
        assert len(estado["verifications"]) == 3
```

```python
# api/tests/h01/test_h01_security.py
"""Identidad, aislamiento, fugas y límite de cuerpo (controles de Seguridad visibles; supuesto T-3)."""
import asyncio
import hashlib
import json

import pytest

from app import config
from app.middleware import BodyLimitMiddleware

VALID_KYC = {"document_number": "TEST-0001", "scenario": "APPROVED"}
JSON_CT = {"Content-Type": "application/json"}

RUTAS_CON_IDENTIDAD = [
    ("GET", "/support/cases", None),
    ("POST", "/control/reset", None),
    ("GET", "/onboarding", None),
    ("POST", "/onboarding/steps/registro", {"document_number": "TEST-0001"}),
    ("POST", "/onboarding/steps/kyc", None),
    ("POST", "/kyc/verifications", VALID_KYC),
    ("GET", "/kyc/verifications/abc", None),
    ("POST", "/kyc/verifications/abc/decision", {"decision": "APPROVED"}),
]


# ---------- Identidad ----------
@pytest.mark.parametrize("metodo,ruta,cuerpo", RUTAS_CON_IDENTIDAD)
def test_endpoints_con_identidad_responden_401_sin_cabecera(client, data_dir, metodo, ruta, cuerpo):
    r = client.request(metodo, ruta, json=cuerpo)
    assert r.status_code == 401
    assert r.json() == {"code": "UNAUTHENTICATED", "message": "No se pudo identificar al usuario."}
    assert not data_dir.exists()


@pytest.mark.parametrize("valor", ["", "a b", "a/b", "../x", "a;b", "a" * 129])
def test_cabecera_invalida_responde_401(client, valor):
    r = client.get("/onboarding", headers={"X-Owner-Id": valor})
    assert r.status_code == 401
    assert r.json()["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize("owner", ["a" * 128, "A.b_c-9"])
def test_identificador_en_el_limite_es_valido(client, owner):
    assert client.get("/onboarding", headers={"X-Owner-Id": owner}).status_code == 200


def test_owner_en_cuerpo_se_rechaza(api, data_dir):
    r = api.post("/kyc/verifications", json={**VALID_KYC, "owner": "usuario-2"})
    assert r.status_code == 422
    assert not data_dir.exists()


def test_owner_en_query_se_ignora(api):
    api.registrar()
    propio = api.get("/onboarding?owner=usuario-2&owner_id=usuario-2").json()
    assert propio["current_step"] == "kyc"  # sigue siendo el estado de usuario-1
    assert api.get("/onboarding", owner=api.other).json()["wallet_status"] == "NOT_STARTED"


# ---------- Aislamiento y rutas hostiles ----------
def test_aislamiento_entre_propietarios_en_kyc(api):
    v = api.crear("PENDING", owner=api.owner)
    assert api.get(f"/kyc/verifications/{v['verification_id']}", owner=api.other).status_code == 404
    r = api.post(
        f"/kyc/verifications/{v['verification_id']}/decision", owner=api.other, json={"decision": "APPROVED"}
    )
    assert r.status_code == 404
    assert api.get(f"/kyc/verifications/{v['verification_id']}", owner=api.owner).json()["status"] == "PENDING"


@pytest.mark.parametrize("vid", ["....", "%00", "con%20espacios", "x" * 64, "%2e%2e"])
def test_identificadores_de_ruta_no_tocan_el_disco(api, data_dir, vid):
    r = api.get(f"/kyc/verifications/{vid}")
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"
    assert not data_dir.exists()


def test_verification_id_demasiado_largo_422(api):
    r = api.get("/kyc/verifications/" + "x" * 65)
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("paso", ["kyc2", "REGISTRO", "Kyc", "registro "])
def test_step_id_fuera_de_contrato(api, data_dir, paso):
    r = api.post(f"/onboarding/steps/{paso}")
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"
    assert not data_dir.exists()


def test_step_id_demasiado_largo_422(api):
    r = api.post("/onboarding/steps/" + "x" * 33)
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"


def test_directorio_usa_solo_el_hash(api, data_dir):
    api.completar_flujo()
    digest = hashlib.sha256(api.owner.encode("utf-8")).hexdigest()
    assert sorted(p.name for p in data_dir.rglob("*")) == sorted([digest, "state.json"])
    assert all(api.owner not in str(p) for p in data_dir.rglob("*"))


# ---------- Fugas ----------
def test_respuestas_no_exponen_owner_ni_hash(api):
    owner = "propietario-secreto-777"
    digest = hashlib.sha256(owner.encode("utf-8")).hexdigest()
    textos = []

    def reg(r):
        textos.append(r.text + json.dumps(dict(r.headers)))
        return r

    reg(api.post("/onboarding/steps/registro", owner=owner, json={"document_number": "TEST-0001"}))
    v = reg(api.post("/kyc/verifications", owner=owner, json=VALID_KYC)).json()
    reg(api.get(f"/kyc/verifications/{v['verification_id']}", owner=owner))
    reg(api.get("/support/cases", owner=owner))
    reg(api.get("/onboarding", owner=owner))
    reg(api.post(f"/kyc/verifications/{v['verification_id']}/decision", owner=owner, json={"decision": "APPROVED"}))  # 409
    reg(api.post("/onboarding/steps/activacion", owner=owner))  # 409
    reg(api.post("/control/reset", owner=owner))
    assert len(textos) == 8
    for t in textos:
        assert owner not in t
        assert digest not in t


# ---------- Límite de cuerpo (413) ----------
_BASE = '{"document_number":"TEST-%s","scenario":"APPROVED"}'


def _cuerpo_con_sufijo(n: int) -> bytes:
    return (_BASE % ("A" * n)).encode("utf-8")


def test_valor_por_defecto_del_limite():
    # T-8: requiere MAX_BODY_BYTES sin definir en el entorno.
    assert config.MAX_BODY_BYTES == 16384


def test_cuerpo_exacto_al_limite_pasa_y_un_byte_mas_se_rechaza(monkeypatch, build_client, state_file, leer_estado):
    limite = len(_cuerpo_con_sufijo(20))
    monkeypatch.setattr(config, "MAX_BODY_BYTES", limite)
    cliente = build_client()
    cabeceras = {"X-Owner-Id": "usuario-1", **JSON_CT}
    ok = cliente.post("/kyc/verifications", content=_cuerpo_con_sufijo(20), headers=cabeceras)
    assert ok.status_code == 201
    grande = cliente.post("/kyc/verifications", content=_cuerpo_con_sufijo(21), headers=cabeceras)
    assert grande.status_code == 413
    assert grande.json()["code"] == "PAYLOAD_TOO_LARGE"
    assert set(grande.json()) == {"code", "message"}
    assert len(leer_estado("usuario-1")["verifications"]) == 1  # el rechazado no se guardó


def test_limite_por_defecto_en_el_borde(client):
    limite = config.MAX_BODY_BYTES
    cabeceras = {"X-Owner-Id": "usuario-1", **JSON_CT}
    en_limite = client.post("/kyc/verifications", content=b"x" * limite, headers=cabeceras)
    assert en_limite.status_code == 422  # pasó el límite; falla por no ser JSON
    assert en_limite.json()["code"] == "VALIDATION_ERROR"
    excedido = client.post("/kyc/verifications", content=b"x" * (limite + 1), headers=cabeceras)
    assert excedido.status_code == 413
    assert excedido.json()["code"] == "PAYLOAD_TOO_LARGE"


def test_413_sin_identidad(client, data_dir):
    r = client.post("/kyc/verifications", content=b"x" * (config.MAX_BODY_BYTES + 1), headers=JSON_CT)
    assert r.status_code == 413  # el límite se aplica antes que la identidad
    assert r.json()["code"] == "PAYLOAD_TOO_LARGE"
    assert not data_dir.exists()


def test_413_con_cuerpo_por_trozos(client):
    limite = config.MAX_BODY_BYTES

    def trozos():
        yield b"{"
        yield b"a" * limite

    r = client.post("/kyc/verifications", content=trozos(), headers={"X-Owner-Id": "usuario-1", **JSON_CT})
    assert r.status_code == 413
    assert r.json()["code"] == "PAYLOAD_TOO_LARGE"


# ---------- Middleware ASGI directo (determinista; T-12) ----------
def _llamar(max_bytes, headers, trozos):
    llamadas, enviados = [], []
    cola = [{"type": "http.request", "body": t, "more_body": i < len(trozos) - 1} for i, t in enumerate(trozos)]

    async def recibir():
        return cola.pop(0)

    async def enviar(mensaje):
        enviados.append(mensaje)

    async def interna(scope, receive, send):
        llamadas.append(True)
        mas = True
        while mas:
            mas = (await receive()).get("more_body", False)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"{}"})

    scope = {"type": "http", "method": "POST", "path": "/", "headers": headers}
    asyncio.run(BodyLimitMiddleware(interna, max_bytes)(scope, recibir, enviar))
    estado = next(m["status"] for m in enviados if m["type"] == "http.response.start")
    cuerpo = b"".join(m.get("body", b"") for m in enviados if m["type"] == "http.response.body")
    return estado, json.loads(cuerpo), llamadas


@pytest.mark.parametrize("valor", [b"abc", b"-5", b"1.5", b"10 "])
def test_middleware_content_length_no_numerico(valor):
    estado, cuerpo, llamadas = _llamar(10, [(b"content-length", valor)], [b"x"])
    assert estado == 400
    assert cuerpo["code"] == "BAD_REQUEST"
    assert llamadas == []


def test_middleware_content_length_en_el_limite():
    estado, _, llamadas = _llamar(10, [(b"content-length", b"10")], [b"x" * 10])
    assert estado == 200
    assert llamadas == [True]


def test_413_no_llama_a_la_aplicacion():
    estado, cuerpo, llamadas = _llamar(10, [(b"content-length", b"11")], [b"x" * 11])
    assert estado == 413
    assert cuerpo["code"] == "PAYLOAD_TOO_LARGE"
    assert llamadas == []


def test_middleware_cuenta_bytes_sin_content_length():
    estado, cuerpo, _ = _llamar(10, [], [b"x" * 6, b"x" * 6])
    assert estado == 413
    assert cuerpo["code"] == "PAYLOAD_TOO_LARGE"


def test_middleware_cuerpo_por_trozos_dentro_del_limite():
    estado, _, llamadas = _llamar(10, [], [b"x" * 5, b"x" * 5])
    assert estado == 200
    assert llamadas == [True]
```

```python
# api/tests/h01/test_h01_errors.py
"""Formato único de error {"code","message"} y mensajes accionables (CA-2.3d, 2.7b)."""
import re

import pytest

VERBOS_ACCION = re.compile(r"\b(Completa|Crea|Espera|Usa|Registra|Corrige|Envía|Ingresa|Revisa)\b")

CASOS = [
    # (método, ruta, json, con_identidad, status, code)
    ("GET", "/onboarding", None, False, 401, "UNAUTHENTICATED"),
    ("GET", "/kyc/verifications/nada", None, True, 404, "NOT_FOUND"),
    ("POST", "/onboarding/steps/foo", None, True, 404, "NOT_FOUND"),
    ("DELETE", "/onboarding", None, True, 405, "METHOD_NOT_ALLOWED"),
    ("POST", "/onboarding/steps/kyc", None, True, 409, "STEP_BLOCKED"),
    ("POST", "/kyc/verifications", {"document_number": "12345678", "scenario": "APPROVED"}, True, 422, "DOCUMENT_NOT_TEST"),
    ("POST", "/kyc/verifications", {"document_number": "TEST-1", "scenario": "NADA"}, True, 422, "VALIDATION_ERROR"),
    ("POST", "/onboarding/steps/registro", None, True, 422, "VALIDATION_ERROR"),
]


@pytest.mark.parametrize("metodo,ruta,cuerpo,con_id,status,code", CASOS)
def test_todos_los_errores_usan_solo_code_y_message(client, metodo, ruta, cuerpo, con_id, status, code):
    cabeceras = {"X-Owner-Id": "usuario-1"} if con_id else {}
    r = client.request(metodo, ruta, json=cuerpo, headers=cabeceras)
    assert r.status_code == status
    b = r.json()
    assert set(b) == {"code", "message"}
    assert b["code"] == code
    assert isinstance(b["message"], str) and b["message"].strip()
    assert "detail" not in b


@pytest.mark.parametrize("escenario", [None, "PENDING", "REJECTED", "EXPIRED"])
def test_mensajes_de_bloqueo_indican_la_accion(api, escenario):
    api.registrar()
    if escenario:
        api.crear(escenario)
    r = api.post("/onboarding/steps/kyc")
    assert r.status_code == 409
    assert VERBOS_ACCION.search(r.json()["message"]), r.json()["message"]


def test_mensaje_de_paso_previo_indica_la_accion(api):
    for paso in ("kyc", "activacion"):
        r = api.post(f"/onboarding/steps/{paso}")
        assert VERBOS_ACCION.search(r.json()["message"]), r.json()["message"]


def test_mensaje_de_documento_indica_el_prefijo(api):
    r = api.post("/kyc/verifications", json={"document_number": "12345678", "scenario": "APPROVED"})
    assert "TEST-" in r.json()["message"]
```

```typescript
// src/app/core/h01-frontend.spec.ts
// Supuestos (T-11): Jasmine/Karma (Angular 17 por defecto), rutas src/app/... de frontend_spec.md.
// Comando: ng test --watch=false --browsers=ChromeHeadless
import { Component } from '@angular/core';
import { HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { FormControl } from '@angular/forms';
import { provideRouter } from '@angular/router';
import { Subject, of, throwError } from 'rxjs';

import { OnboardingStateResponse } from './api.models';
import { documentErrorMessage, testDocumentValidator } from './document.validator';
import { MockApiService, toApiErrorView } from './mock-api.service';
import { SessionService } from './session.service';
import { ConsolaComponent } from '../consola/consola.component';
import { OnboardingComponent } from '../onboarding/onboarding.component';
import { PagosComponent } from '../pagos/pagos.component';

@Component({ standalone: true, template: '' })
class VacioComponent {}

function estado(over: Partial<OnboardingStateResponse> = {}): OnboardingStateResponse {
  return {
    wallet_status: 'IN_PROGRESS',
    current_step: 'kyc',
    steps: [
      { id: 'registro', order: 1, status: 'COMPLETED' },
      { id: 'kyc', order: 2, status: 'CURRENT' },
      { id: 'activacion', order: 3, status: 'LOCKED' },
    ],
    low_amount_payments_enabled: false,
    duration_seconds: null,
    ...over,
  };
}

describe('SessionService (CA-2.2b)', () => {
  beforeEach(() => sessionStorage.clear());

  it('devuelve la misma instancia en dos inyecciones', () => {
    expect(TestBed.inject(SessionService)).toBe(TestBed.inject(SessionService));
  });

  it('descarta wallet y verificación al cambiar de usuario', () => {
    const s = TestBed.inject(SessionService);
    s.setOwner('usuario-1');
    s.setWallet(estado());
    s.setOwner('usuario-2');
    expect(s.wallet()).toBeNull();
    expect(s.verification()).toBeNull();
  });
});

describe('toApiErrorView (CA-2.3d, CA-2.7b)', () => {
  it('conserva code y message del API', () => {
    const e = new HttpErrorResponse({ status: 409, error: { code: 'STEP_BLOCKED', message: 'Completa el paso previo.' } });
    expect(toApiErrorView(e)).toEqual({ status: 409, code: 'STEP_BLOCKED', message: 'Completa el paso previo.' });
  });

  it('mapea status 0 a NETWORK_ERROR', () => {
    expect(toApiErrorView(new HttpErrorResponse({ status: 0 })).code).toBe('NETWORK_ERROR');
  });

  it('usa un mensaje por defecto si el cuerpo no es {code,message}', () => {
    const e = toApiErrorView(new HttpErrorResponse({ status: 422, error: '<html>' }));
    expect(e.code).toBe('VALIDATION_ERROR');
    expect(e.message.length).toBeGreaterThan(0);
    expect(toApiErrorView(new HttpErrorResponse({ status: 502, error: '<html>' })).code).toBe('HTTP_ERROR');
  });

  it('un error que no es HTTP se vuelve UNKNOWN_ERROR', () => {
    expect(toApiErrorView(new Error('x')).code).toBe('UNKNOWN_ERROR');
  });
});

describe('testDocumentValidator (CA-2.3c)', () => {
  const casos: Array<[string, object | null]> = [
    ['TEST-0001', null],
    ['TEST-' + 'A'.repeat(59), null],
    ['', { required: true }],
    ['12345678', { notTest: true }],
    ['test-1', { notTest: true }],
    ['TEST-', { suffix: true }],
    ['TEST-a b', { suffix: true }],
    ['TEST-' + 'A'.repeat(60), { maxlength: true }],
  ];
  for (const [valor, esperado] of casos) {
    it(`valida "${valor.slice(0, 20)}"`, () => {
      expect(testDocumentValidator(new FormControl(valor))).toEqual(esperado);
    });
  }

  it('el mensaje de prefijo es accionable', () => {
    expect(documentErrorMessage({ notTest: true })).toContain('TEST-');
  });
});

describe('MockApiService (CA-2.2a, transversal-1)', () => {
  let http: HttpTestingController;
  let api: MockApiService;
  let session: SessionService;

  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: 'identificar', component: VacioComponent }]),
        MockApiService,
      ],
    });
    http = TestBed.inject(HttpTestingController);
    api = TestBed.inject(MockApiService);
    session = TestBed.inject(SessionService);
  });

  afterEach(() => http.verify());

  it('expone un método por endpoint', () => {
    for (const m of ['health', 'scenarios', 'supportCases', 'createVerification', 'getVerification', 'decideVerification', 'getOnboarding', 'submitStep', 'reset']) {
      expect(typeof (api as unknown as Record<string, unknown>)[m]).toBe('function');
    }
  });

  it('envía X-Owner-Id y nunca el propietario en el cuerpo', () => {
    session.setOwner('demo-user-1');
    api.createVerification({ document_number: 'TEST-0001', scenario: 'APPROVED' }).subscribe();
    const req = http.expectOne('/kyc/verifications');
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('X-Owner-Id')).toBe('demo-user-1');
    expect(Object.keys(req.request.body as object).sort()).toEqual(['document_number', 'scenario']);
    req.flush({});
  });

  it('submitStep de kyc envía cuerpo vacío a la ruta del paso', () => {
    session.setOwner('demo-user-1');
    api.submitStep({ step_id: 'kyc' }).subscribe();
    const req = http.expectOne('/onboarding/steps/kyc');
    expect(req.request.body).toEqual({});
    req.flush(estado());
  });

  it('un 401 limpia la sesión y propaga el error legible', () => {
    session.setOwner('demo-user-1');
    let error: { code?: string } | undefined;
    api.getOnboarding().subscribe({ error: (e) => (error = e) });
    http.expectOne('/onboarding').flush({ code: 'UNAUTHENTICATED', message: 'No se pudo identificar al usuario.' }, { status: 401, statusText: 'Unauthorized' });
    expect(session.isIdentified()).toBeFalse();
    expect(error?.code).toBe('UNAUTHENTICATED');
  });
});

function stubApi() {
  return jasmine.createSpyObj<MockApiService>('MockApiService', [
    'health', 'scenarios', 'supportCases', 'createVerification', 'getVerification',
    'decideVerification', 'getOnboarding', 'submitStep', 'reset',
  ]);
}

describe('ConsolaComponent (CA-2.7a, 2.7b, 2.7c)', () => {
  let api: jasmine.SpyObj<MockApiService>;

  beforeEach(() => {
    api = stubApi();
    TestBed.configureTestingModule({
      imports: [ConsolaComponent],
      providers: [{ provide: MockApiService, useValue: api }, provideRouter([])],
    });
  });

  it('reset: sin confirmar no llama al API; cancelar tampoco', () => {
    const c = TestBed.createComponent(ConsolaComponent).componentInstance;
    c.askReset();
    expect(c.confirmingReset()).toBeTrue();
    expect(api.reset).not.toHaveBeenCalled();
    c.cancelReset();
    expect(c.confirmingReset()).toBeFalse();
    expect(api.reset).not.toHaveBeenCalled();
  });

  it('reset: confirmar llama una sola vez', async () => {
    api.reset.and.returnValue(of({ status: 'reset' }));
    const c = TestBed.createComponent(ConsolaComponent).componentInstance;
    c.askReset();
    await c.confirmReset();
    expect(api.reset).toHaveBeenCalledTimes(1);
    expect(c.resetDone()).toBeTrue();
  });

  it('ejecuta un servicio individual sin llamar a los demás', async () => {
    api.health.and.returnValue(of({ status: 'ok' }));
    const c = TestBed.createComponent(ConsolaComponent).componentInstance;
    await c.run('health');
    expect(api.health).toHaveBeenCalledTimes(1);
    expect(api.scenarios).not.toHaveBeenCalled();
    expect(api.supportCases).not.toHaveBeenCalled();
    expect(c.health()?.status).toBe('ok');
  });

  it('muestra el message del API, no JSON crudo', async () => {
    api.health.and.returnValue(throwError(() => ({ status: 409, code: 'X', message: 'Mensaje legible' })));
    const fixture = TestBed.createComponent(ConsolaComponent);
    await fixture.componentInstance.run('health');
    fixture.detectChanges();
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Mensaje legible');
    expect(texto).not.toContain('{"code"');
  });

  it('no permite ejecuciones duplicadas simultáneas', async () => {
    const respuesta = new Subject<{ status: string }>();
    api.health.and.returnValue(respuesta);
    const c = TestBed.createComponent(ConsolaComponent).componentInstance;
    const p1 = c.run('health');
    const p2 = c.run('health');
    expect(api.health).toHaveBeenCalledTimes(1);
    respuesta.next({ status: 'ok' });
    respuesta.complete();
    await Promise.all([p1, p2]);
  });
});

describe('PagosComponent (CA-2.6b)', () => {
  async function render(habilitado: boolean): Promise<string> {
    const api = stubApi();
    api.getOnboarding.and.returnValue(of(estado({ low_amount_payments_enabled: habilitado, wallet_status: habilitado ? 'ACTIVE' : 'IN_PROGRESS' })));
    TestBed.configureTestingModule({
      imports: [PagosComponent],
      providers: [{ provide: MockApiService, useValue: api }, provideRouter([])],
    });
    const fixture = TestBed.createComponent(PagosComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  it('habilita el acceso solo con wallet activa', async () => {
    expect(await render(true)).toContain('Acceso habilitado');
  });

  it('bloquea el acceso si la wallet no está activa', async () => {
    expect(await render(false)).toContain('Acceso bloqueado');
  });
});

describe('OnboardingComponent (CA-2.6a, duplicados)', () => {
  let api: jasmine.SpyObj<MockApiService>;

  beforeEach(() => {
    api = stubApi();
    api.getOnboarding.and.returnValue(of(estado()));
    api.scenarios.and.returnValue(of({ scenarios: [] }));
    api.supportCases.and.returnValue(of({ cases: [] }));
    TestBed.configureTestingModule({
      imports: [OnboardingComponent],
      providers: [{ provide: MockApiService, useValue: api }, provideRouter([])],
    });
  });

  it('marca el paso actual con aria-current="step"', async () => {
    const fixture = TestBed.createComponent(OnboardingComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const actual = (fixture.nativeElement as HTMLElement).querySelector('[aria-current="step"]');
    expect(actual?.textContent).toContain('Verificación KYC');
    expect(actual?.textContent).toContain('Paso actual');
  });

  it('no envía dos veces el registro con doble clic', async () => {
    api.getOnboarding.and.returnValue(of(estado({ current_step: 'registro', wallet_status: 'NOT_STARTED' })));
    const respuesta = new Subject<OnboardingStateResponse>();
    api.submitStep.and.returnValue(respuesta);
    const fixture = TestBed.createComponent(OnboardingComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    const c = fixture.componentInstance;
    c.registroForm.controls.document_number.setValue('TEST-0001');
    const p1 = c.submitRegistro();
    const p2 = c.submitRegistro();
    expect(api.submitStep).toHaveBeenCalledTimes(1);
    respuesta.next(estado());
    respuesta.complete();
    await Promise.all([p1, p2]);
  });
});
```

Todo lo anterior está **NO EJECUTADO**. Hasta adjuntar la salida real de las fases 0 a 5, ningún criterio puede darse por cumplido.