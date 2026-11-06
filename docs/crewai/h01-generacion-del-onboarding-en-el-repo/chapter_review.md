# chapter_review.md

**Issue:** [H01] Generación del onboarding en el repo destino (tareas 2.2 a 2.8, grupo 2)
**Fecha de la revisión:** 2026-11-06
**Rol:** Chapter, revisor transversal

---

## 0. Estado de la revisión (leer primero)

- **Esta revisión es estática.** Audité lo que entregaron Arquitectura, Backend, Frontend, Pruebas y Seguridad. Ninguno de esos agentes ejecuta código, así que todos los resultados llegan como **NO EJECUTADO**, y yo tampoco ejecuté nada.
- No afirmo que ninguna prueba haya pasado. Donde escribo «esperado», es una expectativa derivada de leer el código y no un resultado.
- **Material que no vi:**
  - `spec.md` (P-1). Ningún rol lo tuvo. Los criterios de aceptación (CA) son los derivados por el Arquitecto a partir del texto de las tareas.
  - El árbol real del repositorio, las pruebas existentes y `tools/lab.py`.
  - La parte final del spec de pruebas del frontend, que llegó **truncada** (`ConsolaComponent` y `OnboardingComponent`). Lo uso solo como limitación y no como motivo de rechazo, porque lo visible cubre todos los criterios (ver §2).
- **Las aprobaciones humanas se conservan.** Este informe no aprueba ni sustituye ninguna. La aprobación final depende de la evidencia ejecutada (§6) y de las decisiones de personas (§7).
- **El estado de las tareas no cambia.** 2.2 a 2.8 siguen sin marcar. 2.1 figura `[x]`, pero su parte «revisar contra la spec» no está verificada (CR-01).

### Supuesto de stack confirmado (no es contradicción)

- Arquitectura, Backend y Pruebas trabajan en **Python + FastAPI bajo `api/`**.
- Las referencias legadas del Issue se traducen de forma coherente:
  - `PreparedStatement` no aplica, porque no hay SQL. Backend lo declara y el estado va en JSON por propietario.
  - `mvn test` equivale a `python -m pytest` y a `python tools/lab.py test api` (supuesto T-5 de Pruebas).
  - `auth/src/main/java` equivale a `api/app/`.
- El frontend es Angular, tal como lo fijó el Arquitecto («Stack cerrado»).
- **Ningún entregable mezcla stacks ni implementa uno distinto.** No hay Java, Maven ni Quarkus en el código, así que no es motivo de rechazo.

---

## 1. Contraste de contratos entre entregables

| Contrato | Arquitecto | Backend | Frontend | Pruebas | Resultado |
|---|---|---|---|---|---|
| Rutas (9 endpoints) | §3.1 y §3.2 (S-4) | Idénticas | `MockApiService`, 9 métodos | Matriz y OpenAPI en línea base | Coherente (rutas provisionales S-4) |
| Identidad | `get_current_owner`, nunca en cuerpo ni URL | Cabecera `X-Owner-Id` (B-3) | La envía en cada llamada | `test_owner_en_cuerpo_se_rechaza` y 401 | Coherente; riesgo en SEC-01 |
| Formato de error | `{"code","message"}` | Handlers para `ApiError`, `HTTPException`, validación y `Exception` | `toApiErrorView` lo mapea | Parametrizado ×8 | Coherente |
| Códigos de error | Tabla §3.3 | Añade `LIMIT_REACHED`, `BAD_REQUEST` y `METHOD_NOT_ALLOWED` (B-8) | Muestra el `message` del API | Los prueba | Ampliación declarada; falta actualizar `user_story.md` (CR-11) |
| Escenarios y pasos | Sin nombres (P-3, P-4) | `APPROVED/REJECTED/PENDING/EXPIRED`; `registro→kyc→activacion` | Tipos TS espejo de `schemas.py` | Mismas constantes (T-2) | Coherente, provisional |
| Documento `TEST-` | 422 `DOCUMENT_NOT_TEST` | Mismo código; sufijo `[A-Za-z0-9-]{1,59}`, máx. 64 | Validador espejo (mismos límites y mensajes) | Casos válidos, inválidos y borde | Coherente |
| Estado de wallet y pagos | `GET /onboarding` | `low_amount_payments_enabled = (ACTIVE)` | `/pagos` solo refleja ese campo | `test_pagos_de_bajo_monto_solo_con_wallet_activa` | Coherente (P-6 abierta) |
| Eventos y duración (2.5) | Sin endpoint (S-6) | Eventos en `state.json`; segundos con 3 decimales | Solo muestra `duration_seconds` | Pruebas de eventos y duración | Coherente |
| Persistencia | JSON por propietario, SHA-256, un proceso (S-8) | `storage.py` con lock, `os.replace` y `schema_version` | No aplica | Esquema, atomicidad, corrupción y concurrencia | Coherente |
| Límite de cuerpo | 16384 bytes (S-7) | `BodyLimitMiddleware` ASGI | Sin lógica | Borde exacto, chunked y `Content-Length` inválido | Coherente |
| Reset con confirmación | API sin cuerpo; la confirmación es de interfaz (S-5) | `POST /control/reset` borra solo el estado del propietario | Grupo de confirmación con Esc y Cancelar | Pruebas API; prueba FE no visible (truncada) | Coherente |

**No encontré contratos incompatibles ni supuestos contradictorios entre entregables.** Las discrepancias son ampliaciones declaradas. Backend no implementó la «ventana de pasos» que el Arquitecto había mencionado para `config.py` (B-10) y añadió códigos de error (B-8). Ambas están registradas.

---

## 2. Cobertura por criterio de aceptación

Leyenda: **D** = diseño presente, **I** = implementación presente, **T** = prueba asociada escrita (no ejecutada), **S** = revisión de seguridad. Todas las pruebas están **NO EJECUTADAS**.

| CA | Arquitectura | Persistencia | Implementación | Pruebas (nombre) | Seguridad | Cobertura |
|---|---|---|---|---|---|---|
| **2.1** Pipeline H01 y revisión de `user_story.md` contra la spec | D: `user_story.md` con CA derivados | — | — | M-0 manual; sin prueba automática | — | **Parcial.** Falta la spec (CR-01) |
| **CA-2.2a** Una interfaz request y otra response por endpoint | D: `MockApiService` espejo de `schemas.py` | — | I: `api.models.ts`, `mock-api.service.ts` | T: FE «método por endpoint», `tsc --noEmit`, OpenAPI (línea base), M-1 | S: `encodeURIComponent`, sin `innerHTML` | Cubierto |
| **CA-2.2b** Un único `SessionService` | D | — | I: `providedIn:'root'` | T: FE «misma instancia», `grep` | — | Cubierto |
| **CA-2.3a** Estado de wallet consistente | D | Estado derivado del JSON | I: `_wallet_status` | T: `test_estado_inicial…`, `test_estado_es_estable…`, `test_wallet_status_segun_ultima_verificacion` | — | Cubierto (ver CR-12) |
| **CA-2.3b** Bloqueo de pasos | D | Sin escritura al bloquear | I: `_assert_not_blocked` | T: `test_paso_bloqueado_…`, `test_kyc_bloqueado_segun_verificacion`, `test_verificacion_sin_registro_…` | S: 409 sin cambio de estado | Cubierto |
| **CA-2.3c** Documento `TEST-` | D | Validación antes de tocar disco | I: `_validate_document` y validador FE | T: `test_documento_rechazado` (12 casos), borde de 64, tipo incorrecto, no refleja valor | S: valor no reflejado | Cubierto |
| **CA-2.3d** Mensajes accionables | D | — | I: mensajes en `services.py` y UI | T: `test_mensajes_de_bloqueo_indican_la_accion`, `test_mensaje_de_documento_…`; FE `toApiErrorView` | — | Cubierto (el texto requiere revisión humana) |
| **CA-2.4a** `POST /kyc/verifications` con cuatro escenarios | D (nombres provisionales P-3) | Registro en `verifications` | I: `create_verification` | T: `test_crear_verificacion_por_escenario[×4]` | S: UUID4 no enumerable | Cubierto |
| **CA-2.4b** Consulta | D (ruta S-4) | Búsqueda solo dentro del propietario | I | T: `test_consultar_verificacion_*`, `test_aislamiento_entre_propietarios_en_kyc` | S: 404 para ajenas | Cubierto |
| **CA-2.4c** Decisión sobre `PENDING` | D | `decided_at` | I: `decide_verification` | T: `test_decidir_pendiente[×2]`, `…no_pendiente_409[×3]`, `…dos_veces_409`, `…invalida_422[×3]` | S: ver SEC-02 | Cubierto |
| **CA-2.5a** Eventos de inicio, paso y cierre | D (S-6) | `events` en `state.json` | I: `submit_step` | T: orden, sin duplicados, bloqueados sin eventos, sin endpoint | — | Cubierto |
| **CA-2.5b** Duración | D (unidad en P-7) | `started_at` y `closed_at` | I: `compute_duration_seconds` | T: `test_duracion_*` (3) | — | Cubierto |
| **CA-2.6a** Pasos visibles y paso actual | D | — | I: `onboarding.component.html` (`aria-current="step"`) | T: FE «marca el paso actual» **declarada, código no visible (truncado)**; M-2 manual | — | Cubierto en diseño; prueba por confirmar (CR-09) |
| **CA-2.6b** Pagos de bajo monto según wallet | D (P-6 abierta) | — | I: campo API y `PagosComponent` | T: `test_pagos_de_bajo_monto_solo_con_wallet_activa`; FE `PagosComponent` (no visible) | — | Cubierto en API; UI por confirmar |
| **CA-2.7a** Consola: `/health`, `/scenarios`, `/support/cases`, ejecución individual | D | — | I: `console.py`, `consola.component.*` | T: `test_health_*`, `test_scenarios_*`, `test_support_cases_*`; FE «servicio individual» (no visible) | S: `/health` y `/scenarios` anónimos | Cubierto en API; UI por confirmar |
| **CA-2.7b** Errores legibles | D | — | I: `toApiErrorView`, alertas por servicio | T: FE `toApiErrorView` (visible); «message, no JSON crudo» (no visible) | — | Cubierto |
| **CA-2.7c** `POST /control/reset` con confirmación | D (S-5) | Borra solo `state.json` del propietario | I: grupo de confirmación con Esc y foco | T: `test_reset_*` (3), `test_reset_repara_estado_corrupto`; FE «sin confirmar no llama» (no visible) | S: reset borra eventos (SEC-02) | Cubierto en API; UI por confirmar |
| **CA-2.8** Salida mensual de nuevos usuarios activos y gasto atribuido | D parcial: P-8 abierta | Lectura de todos los estados (`iter_states`) | I: `monthly_analytics()`, **sin endpoint, CLI ni archivo** | T: `test_analitica_*` (7) | S: SEC-09 | **Parcial.** Ver CR-02 |
| **CA-T1** Identidad desde el servidor, 401 sin ella | D | — | I: `get_current_owner` | T: 401 ×8, cabecera inválida ×6, owner en cuerpo y query | **SEC-01 (Alta)** | Cubierto como diseño; riesgo abierto |
| **CA-T2** Cuerpo grande, 413 | D | — | I: `BodyLimitMiddleware` | T: borde exacto, chunked, `Content-Length` no numérico | S: sin hallazgo | Cubierto |
| **CA-T3** No exponer owner ni hash | D | Directorio por hash | I | T: `test_respuestas_no_exponen_owner_ni_hash`, `test_directorio_usa_solo_el_hash`, `test_error_500_no_filtra…` | S: sin hallazgo | Cubierto |
| **CA-T4** Concurrencia del mismo usuario | D (S-8) | Lock por franjas y `os.replace` | I | T: 3 pruebas con hilos; M-4 | S: SEC-07 (varios workers) | Cubierto para un solo proceso |

**Criterios sin cobertura de diseño ni prueba: ninguno.** Dos criterios están cubiertos solo de forma parcial: 2.1 (falta la spec) y 2.8 (sin punto de salida ni origen de gasto). Ambos tienen diseño y prueba asociada, y la decisión pendiente se plantea como preguntas P-1 y P-8. Los trato como condiciones de decisión humana (CR-01, CR-02) y no como bloqueantes de diseño; el razonamiento está en §8.

---

## 3. Observaciones y hallazgos pendientes

Severidad según el impacto sobre el Issue. Cada fila indica responsable, cambio requerido y cómo verificarlo.

| ID | Sev. | Observación y evidencia | Responsable | Cambio requerido | Verificación |
|---|---|---|---|---|---|
| **CR-01** | Alta (condición) | `spec.md` no estuvo disponible para ningún rol. Los CA de §2 son derivados del texto de las tareas, y la parte «revisar contra la spec» de 2.1 no se ha hecho (`user_story.md`, P-1, T-1). | Arquitecto + persona de Producto | Contrastar la sección 4 de `user_story.md` con `spec.md`. Corregir los CA que difieran y propagar el cambio a Backend, Frontend y Pruebas. | Checklist M-0 firmado por una persona: cada CA mapeado a un requisito de la spec. Si algún CA cambia, repetir la Fase 2 de pruebas. |
| **CR-02** | Alta (condición) | 2.8 exige una «salida analítica mensual». `monthly_analytics()` existe y está probada, pero **ningún endpoint, CLI ni archivo la expone**. Ningún endpoint escribe `spend`, así que el gasto atribuido es **0** por construcción (B-6, P-6, P-8, T-10). | Backend + persona de Producto | Decidir el formato y destino de la salida (P-8) y la definición de «usuario activo nuevo», «gasto atribuido» y zona horaria. O bien aceptar por escrito que la función con gasto 0 satisface 2.8 en esta entrega. | Si se añade un punto de salida, prueba nueva que lo invoque. Si se acepta tal cual, registro de la aceptación en el PR. |
| **CR-03** | Alta si hay despliegue compartido; Media en mock aislado (SEC-01) | La identidad es la cabecera `X-Owner-Id`, validada solo por formato. Quien conozca un identificador accede a su estado y puede reiniciarlo. Es una decisión de diseño declarada (S-2, B-3, P-9). La corrección propuesta (`POST /session` y token firmado) **cambia el contrato aprobado** y excede el Issue. | Seguridad + Producto (decisión); Backend y Frontend (implementación si se acepta) | Decisión por escrito: (a) aceptar el riesgo con despliegue solo local o de pruebas aislado, o (b) adoptar un mecanismo emitido por el servidor. En (b), actualizar `user_story.md`, `conftest.py` (`Api.headers`), `MockApiService` e `IdentificarComponent`. | PoC antes/después (comandos en `security_report.md` SEC-01) y las 4 pruebas propuestas, **no ejecutadas**. |
| **CR-04** | Media (SEC-02) | Los controles mock (elegir escenario, decidir el propio KYC, `reset`) están siempre activos. En el mock es el comportamiento pedido por 2.4 y 2.7, pero nada impide reutilizarlos fuera de pruebas. | Backend; confirma Seguridad | Evaluar la bandera `ENABLE_MOCK_CONTROLS`, por defecto apagada. Si se adopta, `conftest.py` la activa y las pruebas de `test_h01_kyc.py` y `test_h01_console.py` siguen aplicando. | Prueba «controles apagados → 404» propuesta en SEC-02. |
| **CR-05** | Media (SEC-03) | No hay límite global de propietarios ni rate limit. Cada identificador nuevo crea un directorio y un `state.json`. | Backend + responsable de despliegue | Límite `MAX_OWNERS` con código de error añadido al contrato (el código es decisión de diseño), y rate limit en el proxy. Los umbrales dependen del despliegue, que desconozco (Q-3). | Bucle de 500 propietarios antes/después y la prueba `test_limite_global_de_propietarios` propuesta. |
| **CR-06** | Media (SEC-04) | Los pines (`fastapi==0.115.6`, `starlette==0.41.3`, `uvicorn==0.34.0`, `pydantic==2.10.4`) **no están verificados** contra PyPI ni OSV, y las transitivas no están fijadas. Backend desconoce el `requirements.txt` existente. `requirements-dev.txt` (pytest, httpx) se genera con `pip freeze`. | Backend (pines); Pruebas (ejecución) | Ejecutar `pip check`, `pip-audit` y `pip index versions`. Si hay avisos, cambiar a `paquete==versión` exacto (también `starlette`) y fijar transitivas. Fusionar con el archivo existente sin duplicar líneas. | Salidas reales adjuntas. `test_h01_requirements.py` debe seguir pasando. |
| **CR-07** | Media (condición cheap) | `api/data/` no está en `.gitignore` (B-7, solo recomendado) y `DATA_DIR` por defecto es relativo (SEC-08). Riesgo de versionar datos de prueba. | Backend | Añadir `api/data/` a `.gitignore` en este mismo cambio. Resolver `DATA_DIR` a ruta absoluta y crearlo con `0o700`. | `git check-ignore -v api/data/x` y `stat -c '%a' "$DATA_DIR"` (esperado 700). |
| **CR-08** | Media | El frontend asume mismo origen mediante un proxy de desarrollo que **no forma parte de la entrega**, y el backend no configura CORS (`frontend_spec.md` §10, §11). Sin ese archivo, `ng serve` no alcanza el API. | Frontend | Entregar el archivo de proxy (`--proxy-config`) o documentar el comando exacto. No añadir CORS permisivo, porque invalidaría la conclusión de CSRF de Seguridad. | Recorrido M-2 con el proxy. `curl` a través de `ng serve` devuelve 200 en `/health`. |
| **CR-09** | Media | El spec de pruebas del frontend llegó **truncado**. No se ve el código de las pruebas FE de `ConsolaComponent`, `OnboardingComponent` ni `PagosComponent`, que respaldan CA-2.6a, 2.6b, 2.7a, 2.7b y 2.7c en la UI. Además, `confirmReset()` no comprueba por sí mismo la confirmación previa (solo la plantilla, observación 5 de Pruebas). | Pruebas | Confirmar que `h01-frontend.spec.ts` está completo y contiene esas pruebas. Considerar una guarda en `confirmReset()` o una prueba de plantilla que impida la llamada directa. | `ng test --watch=false --browsers=ChromeHeadless` con la salida real y la lista de pruebas. |
| **CR-10** | Media | Rutas del frontend (`src/app/...`), runner (Jasmine/Karma, T-11) y versión de Angular (17) no están confirmadas (P-2). Persistencia en archivos JSON no confirmada (P-5). Ninguna decisión de Datos aprobada. | Arquitecto + persona del equipo | Confirmar por escrito: raíz Angular, runner, y que JSON por propietario es aceptable para el mock. | Revisión del árbol real. `grep -rnE "class \w*Session\w*" src/app` devuelve solo `SessionService`. |
| **CR-11** | Baja | La tabla de errores de `user_story.md` §3.3 no incluye `LIMIT_REACHED` (409), `BAD_REQUEST` (400) ni `METHOD_NOT_ALLOWED` (405), añadidos por Backend (B-8). El frontend no define mensajes por defecto para 400 y 405 (solo se usa el `message` del API). | Arquitecto (documento); Frontend (mensajes por defecto, opcional) | Actualizar `user_story.md` con la tabla real. Añadir 400 y 405 a `DEFAULT_MESSAGES` si se desea. | Revisión cruzada de `errors.py` y `middleware.py` contra la tabla. |
| **CR-12** | Baja | Una verificación `PENDING` creada **antes** del registro deja la wallet en `KYC_PENDING` (observación 1 de Pruebas). La spec no lo define. | Producto + Backend | Confirmar si es el comportamiento deseado. | Prueba que fije la decisión, o ajuste de `_wallet_status`. |
| **CR-13** | Baja | Exclusión mutua solo dentro del proceso (SEC-07, S-8). Con varios workers hay pérdida de actualizaciones y se puede superar el tope de verificaciones. | Backend + responsable de despliegue | Documentar y hacer cumplir un solo worker (por ejemplo, comprobar `WEB_CONCURRENCY` al arrancar), o añadir bloqueo de archivo. Ajustar las pruebas «leer no escribe» si se adopta `flock`. | Prueba con `multiprocessing` (no determinista; repetir). |
| **CR-14** | Baja | Endurecimientos menores: SEC-05 (log con `request.url.path`, usar `%r`), SEC-06 (`/docs` y `/openapi.json` expuestos; la prueba de línea base depende de `/openapi.json`), SEC-09 (validar tipos al leer; analítica frágil ante datos mal formados), SEC-10 (`Cache-Control: no-store`, `X-Content-Type-Options`). | Backend | Aplicar el cambio de una línea de SEC-05. Evaluar el resto. Si se adopta `ENABLE_DOCS`, la prueba de línea base debe activarlo. | Pruebas propuestas en `security_report.md` por cada hallazgo. |
| **CR-15** | Baja | Sensibilidades del entorno de pruebas: `test_valor_por_defecto_del_limite` falla si `MAX_BODY_BYTES` está definida (T-8). `test_directorio_del_propietario_es_privado` solo vale en POSIX (T-9). `Allow` en el 405 depende de la versión de Starlette. | Pruebas | Ejecutar con las variables sin definir (`unset …`). Si el CI es Windows, documentar el descarte de la prueba POSIX (no usar `skip`, T-13). | Salida de pytest con `skipped="0"`. |

---

## 4. Disposición de los hallazgos de Seguridad

Ninguno fue verificado en ejecución. Todas las correcciones son **propuestas, no aplicadas**.

| Hallazgo | Sev. | Disposición del Chapter |
|---|---|---|
| SEC-01 Identidad sin secreto | Alta | **Decisión humana requerida** (CR-03). El diseño la declara como credencial de mock y la corrección cambia el contrato. Si el despliegue es compartido o accesible desde internet, pasa a bloqueante. |
| SEC-02 El usuario decide su propio KYC | Media | Comportamiento pedido por el Issue en el mock. Evaluar la bandera (CR-04). |
| SEC-03 Sin límite global de propietarios | Media | Mitigar antes de cualquier despliegue compartido (CR-05). |
| SEC-04 Dependencias sin verificar | Media | **Condición previa al merge**: ejecutar `pip check` y `pip-audit` (CR-06). |
| SEC-05 Log sin neutralizar | Baja | Cambio de una línea, recomendado (CR-14). |
| SEC-06 `/docs` y `/openapi.json` | Baja | Evaluar (CR-14). Ajustar la prueba de línea base si se aplica. |
| SEC-07 Un solo proceso | Baja | Documentar y hacer cumplir (CR-13). |
| SEC-08 `DATA_DIR` y `.gitignore` | Baja | **Requerido en este cambio** (CR-07). |
| SEC-09 Validación del estado persistido | Baja | Recomendado (CR-14). |
| SEC-10 Cabeceras de respuesta | Info/Baja | Recomendado (CR-14). |

Los controles que Seguridad revisó sin hallazgo (SQL, recorrido de rutas, IDOR, validación, errores, límite de cuerpo, XSS, escritura atómica) se apoyan en lectura estática y no están verificados en ejecución.

---

## 5. Pruebas pendientes

**Todo está NO EJECUTADO.** Una persona debe correr los comandos y adjuntar la salida literal. Los comandos vienen de `testing_report.md` §7 y de `security_report.md`.

| # | Responsable | Fase y comando exacto | Evidencia a adjuntar |
|---|---|---|---|
| 1 | Persona de QA | **Fase 0.** `cd api && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pip install pytest httpx && pip check && unset MAX_BODY_BYTES MAX_VERIFICATIONS_PER_OWNER DATA_DIR` | `pip check` limpio; `pip freeze` |
| 2 | Persona de QA | **Fase 1a, existentes.** `python -m pytest tests --ignore=tests/h01 -rs -q --basetemp=.pytest_tmp --junitxml=../evidencia/f1a_existentes.xml` | `f1a_existentes.xml` y `.txt` |
| 3 | Persona de QA | **Fase 1b, todas.** `python -m pytest tests -rs -v --basetemp=.pytest_tmp --junitxml=../evidencia/f1b_todas.xml` y luego `grep -o 'skipped="[0-9]*"' ../evidencia/f1b_todas.xml` (debe ser 0) y `test ! -e data` | `f1b_todas.xml` con `skipped="0"` |
| 4 | Persona de QA | **Fase 1c, vía laboratorio.** `python tools/lab.py test api` | `f1c_lab.txt` |
| 5 | Persona de QA | **Fase 2, por tarea.** `python -m pytest tests/h01/test_h01_kyc.py -v`; `…test_h01_onboarding.py`; `…test_h01_events_analytics.py`; `…test_h01_console.py`; `…test_h01_security.py …test_h01_persistence.py …test_h01_errors.py …test_h01_requirements.py` | `f2_*.txt` |
| 6 | Frontend + QA | **Fase 3.** `grep -rnE "class \w*Session\w*" src/app`; `npx tsc --noEmit -p tsconfig.app.json`; `npx tsc --noEmit -p tsconfig.spec.json`; `ng test --watch=false --browsers=ChromeHeadless` | `f3_frontend.txt` |
| 7 | Frontend + QA | **M-1 y M-2.** Comparar `api.models.ts` con `schemas.py` campo por campo y recorrer `frontend_spec.md` §10 con capturas | Capturas y checklist |
| 8 | Persona de QA | **Fase 4, servidor real.** Bloque de `uvicorn` y `curl` de `testing_report.md` §7, con `DATA_DIR="$(mktemp -d)"`, incluido el `xargs -P` de concurrencia | Salida literal de cada `curl` |
| 9 | Persona de QA + Backend | **Fase 5, dependencias.** `pip check`; `pip index versions fastapi` (repetir para `starlette`, `uvicorn`, `pydantic`); `pip install pip-audit && pip-audit -r requirements.txt` | `f5_*.txt` |
| 10 | Seguridad | **PoC de SEC-01 y SEC-03** sobre el código sin corregir (comandos en `security_report.md`) | `sec_poc_antes.txt` |

Pendiente en el diseño de pruebas: cobertura medida (no incluida), multiproceso, CORS, pagos reales y pruebas visuales o de accesibilidad automatizadas.

---

## 6. Evidencia disponible y ausente

- **Disponible (artefactos de diseño, no resultados):**
  - `user_story.md`, `backend_spec.md` con el código de `api/app/*`, `frontend_spec.md` con el código Angular.
  - `testing_report.md` con las pruebas, parcial en la parte FE por truncamiento.
  - `security_report.md`.
- **Ausente:**
  - Ninguna salida real de `pytest`, `ng test`, `tsc`, `curl`, `pip check` ni `pip-audit`.
  - `spec.md`.
  - Archivo de proxy del frontend.
  - Cobertura medida.
- No hay evidencia de que ninguna prueba haya pasado. Todo lo anterior queda **NO EJECUTADO** hasta que se adjunte la salida real.

---

## 7. Aprobaciones humanas (se conservan; este informe no las sustituye)

Pendientes de una persona:

1. Confirmar los CA derivados contra `spec.md` (CR-01).
2. Decidir el riesgo de identidad y los controles mock según el tipo de despliegue (CR-03, CR-04, CR-05).
3. Aceptar o redefinir la salida de 2.8 y la definición de gasto atribuido (CR-02).
4. Confirmar rutas, campos, escenarios, pasos y estados provisionales (S-4, P-3, P-4), y la persistencia en JSON (P-5).
5. Revisar los textos de los mensajes accionables.
6. Aprobación final del PR, **condicionada a la evidencia ejecutada** de §5.

---

## 8. Veredicto

**Bloqueantes de diseño:** ninguno.

**Motivos**

- **Criterios cubiertos.**
  - Los 22 criterios (2.1, 2.2a a 2.8 y los 4 transversales) tienen diseño y pruebas asociadas. 2.1 es la excepción menor: tiene diseño (`user_story.md`) y verificación manual M-0, pero sin prueba automática, porque su parte de contraste con la spec no se pudo hacer (CR-01).
  - En la parte de UI de 2.6 y 2.7, la prueba FE está declarada pero su código no es visible por truncamiento. Eso no es motivo de rechazo, porque lo visible cubre el resto.
- **Contratos.** No hay contratos ni supuestos que se contradigan entre entregables. Las ampliaciones de Backend (B-8, B-10) están declaradas.
- **Stack.** Es Python + FastAPI en `api/` y Angular en el frontend, sin mezcla ni traducción pendiente. Las referencias Java del Issue están traducidas de forma coherente (supuesto confirmado, §0).
- **Alcance.** No detecté cambios fuera del Issue. Las correcciones de Seguridad que cambian el contrato (token, `/session`) están **propuestas, no aplicadas**, y por eso no se incorporan sin una decisión humana.
- **Entregables.** Ningún entregable está ausente ni contiene marcadores sin resolver del tipo `<VERSIÓN_…>` o `[Pendiente]` en una decisión necesaria. Las preguntas abiertas P-1 a P-10 tienen una resolución conservadora implementada y documentada.
- **Criterios parciales (2.1 y 2.8).** No son bloqueantes de diseño porque cada uno tiene diseño y pruebas, y lo que falta es una decisión humana que no puede cerrarse desde el diseño. Si la persona de Producto descarta esa decisión (spec que contradiga los CA, o 2.8 que exija una salida accesible), el veredicto debe reabrirse.
- **Riesgos de seguridad.** SEC-01 (Alta) y SEC-02/03 (Media) son riesgos de un mock con identidad por cabecera declarada como decisión de diseño (S-1, S-2, B-3). No son defectos de diseño del Issue, pero **pasan a bloqueantes si el servicio se despliega en un entorno compartido o accesible desde internet** (Q-2 de Seguridad).

**Condiciones previas al merge** (no son motivo de rechazo por sí solas)

1. Ejecutar las fases 0 a 5 de §5 y adjuntar las salidas reales, con `skipped="0"`. Responsable: persona de QA.
2. Una persona confirma los CA contra `spec.md` (CR-01) y decide el alcance de 2.8 (CR-02). Responsable: Arquitecto y Producto.
3. Decisión escrita de Seguridad y Producto sobre SEC-01, SEC-02 y SEC-03, con confirmación de que el despliegue es local o aislado (CR-03 a CR-05).
4. Resultado de `pip check` y `pip-audit`, con pines exactos confirmados (CR-06). Responsable: Backend.
5. Añadir `api/data/` a `.gitignore` y fijar `DATA_DIR` absoluto (CR-07). Responsable: Backend.
6. Entregar o documentar el proxy de desarrollo (CR-08). Responsable: Frontend.
7. Confirmar el spec FE completo de pruebas (CR-09) y las rutas, runner y persistencia (CR-10). Responsable: Pruebas y Arquitecto.

**Correcciones solicitadas** (no bloqueantes): CR-11 a CR-15, más las mejoras de SEC-05, 06, 09 y 10 a criterio de Backend.

**La aprobación final depende de la evidencia ejecutada y de las aprobaciones humanas de §7.** Este informe no ejecutó nada y no sustituye ninguna aprobación.

VEREDICTO: APROBADO