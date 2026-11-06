# chapter_review.md

**Issue:** [H01] Pruebas del onboarding (`registro-activacion-wallet`, grupo 3 de `tasks.md`, tareas 3.1 a 3.12)
**Revisor:** Chapter, revisor transversal
**Fecha:** 2026-11-06
**Estado de la revisión:** análisis estático de los entregables de Arquitectura, Backend, Frontend, Pruebas y Seguridad. **No se ejecutó nada.** Todo resultado de pruebas figura como NO EJECUTADO. Este informe **no sustituye ninguna aprobación humana** (sección 9).

---

## 1. Material revisado y límites

| Entregable | Recibido | Observación |
|---|---|---|
| Arquitectura (`user_story.md`) | Sí | Fija el alcance: solo pruebas, sin tocar `api/app/`. Deja abiertas P-1 a P-10. |
| Backend (`backend_spec.md` y código) | Sí | Entrega un `api/app/` completo y `requirements*.txt`. |
| Frontend | Sí | "Sin cambios". Traslada los `*.spec.ts` al rol de Pruebas. |
| Pruebas (`testing_report.md` y código) | Sí | Suite del API en `api/tests/onboarding/`. Casos de cliente C-01 a C-16 solo diseñados. |
| Seguridad (`security_report.md`) | Sí | 7 hallazgos (2 Altos), 3 hipótesis y correcciones **no aplicadas**. |

**Límites:**
- `spec.md`, `design.md` (la tabla de cobertura por endpoint), los `schemas.py` reales y `tools/lab.py` **no están en el contexto de ningún rol**. El contrato probado es el que Backend asumió, no uno confirmado.
- No hay truncamiento en el material recibido. Lo visible basta para emitir veredicto.
- Los resultados esperados que aparecen en los entregables son predicciones, no evidencia.

### 1.1 Stack (supuesto confirmado, no es motivo de rechazo)

El API es Python con FastAPI en `api/`. Las equivalencias legadas del Issue quedan traducidas de forma explícita y coherente:

| Referencia legada | Traducción | Dónde |
|---|---|---|
| `PreparedStatement` | No aplica: no hay base de datos ni SQL. El estado es un almacén en memoria. | Backend §7; Pruebas T-4 |
| `mvn test` | `python tools/lab.py test api` o `cd api && python -m pytest tests -v` | Arquitectura §4; Backend §C; Pruebas §6 |
| `auth/src/main/java` | `api/app/` (código) y `api/tests/` (pruebas) | Arquitectura §1.4; Backend §2 |

Ningún entregable mezcla ambos stacks ni implementa otro distinto.

---

## 2. Cobertura por criterio de aceptación

Leyenda: ✔ cubierto en diseño y con prueba escrita (NO EJECUTADA) · ◐ parcial · ✖ sin prueba ni implementación del cliente.

| ID | Arquitectura | Persistencia | Implementación | Pruebas | Seguridad | Estado |
|---|---|---|---|---|---|---|
| 3.1 `GET /health` 200; latencia inválida bloqueada en cliente | §4 asigna API y cliente | N/A | `routers/health.py` | API: `test_h01_health.py` (3 pruebas). Cliente: C-01 solo diseñado | La validación de cliente no es un control de seguridad (SEC §6) | ◐ **Cliente sin prueba** |
| 3.2 `GET /scenarios` llena el selector; error de red legible | §4 | N/A | `routers/scenarios.py` | API: `test_h01_scenarios.py` (4 pruebas). Cliente: C-02 solo diseñado | Sin hallazgos | ◐ **Cliente sin prueba** |
| 3.3 `POST /kyc/verifications`: 201 ×3, 503, documento sin `TEST-` bloqueado | §4; P-3 y P-4 abiertas | Memoria; el 503 no escribe (prueba `..._503_sin_efectos`) | `routers/kyc.py`, `services.create_verification` | API: 201 ×3, 503, bordes y 413. El bloqueo `TEST-` del servidor solo se prueba con una bandera opcional. Cliente: C-03 a C-05 solo diseñados | SEC-03 (Media): `scenario` lo elige el cliente | ◐ **Bloqueo `TEST-` (criterio de cliente) sin prueba** |
| 3.4 `GET /kyc/verifications/{id}` 200 y 404 | §4 | Lectura en memoria | `routers/kyc.py` | `test_get_verificacion_200`, `..._inexistente_404`, bordes de id | SEC-01: sin autorización por objeto | ✔ |
| 3.5 `.../decision` 200 sobre `PENDING` y 409 `DECISION_CONFLICT` | §4; S-B1 de Backend concilia `MANUAL_REVIEW` y `PENDING` | Atomicidad bajo `RLock` | `services.decide_verification` | `test_h01_kyc_decision.py` (200, 409 ×3, 404, 400, 413, concurrencia) | SEC-01 Alta (cualquiera puede decidir) | ✔ |
| 3.6 `GET /wallets/{id}` 200 con saldos 0 y 404 | §4 | Wallet creada en memoria | `routers/wallets.py` | `test_h01_wallets.py` | SEC-01 | ✔ |
| 3.7 `GET /support/cases`: `KYC_REVIEW` `OPEN` y lista vacía | §4; P-7 (qué crea el caso) | Casos en memoria | `services.list_support_cases` | `test_h01_support_cases.py` | SEC-01: la lista expone todos los `verificationId` | ✔ |
| 3.8 `POST /control/reset` 200; cancelar no llama a la API | §4 | `store.reset()` | `routers/control.py` | API: `test_h01_control_reset.py`. Cliente (limpieza local y cancelación): C-06 y C-07 solo diseñados | SEC-02 Alta: reset sin credenciales y activo por defecto | ◐ **Cliente sin prueba** |
| 3.9 Manejador común: 400, 404, 409, 413, 429, 503 | §3.1 propone los `code`; P-5 abierta | N/A | `errors.py`, `middleware.py` | API: `test_h01_error_handler.py`. El 429 solo se prueba en una app aislada (ningún endpoint real lo genera, A-6). Cliente (mostrar `message`): C-08 solo diseñado | Mensajes fijos, sin trazas ni eco de valores | ◐ **Cliente sin prueba; 429 solo a nivel de handler** |
| 3.10 Pasos visibles, bloqueo con dato faltante o inválido, estado activo | §4 asigna "componentes del cliente"; ruta desconocida (P-2) | N/A | **No hay código de cliente** | Solo un sustituto de API: `test_wallet_activa_solo_tras_aprobacion`. Cliente: C-09 a C-12 solo diseñados | Sin revisión (SEC §6) | ✖ **Sin cobertura del criterio real** |
| 3.11 Eventos (completo y abandonado) y mediana | §4; ubicación y caso vacío abiertos (P-6) | N/A | **No hay código ni ubicación** | Solo C-13 a C-16 diseñados | Sin revisión | ✖ **Sin cobertura** |
| 3.12 Salida real adjunta al PR | §4 y §7 de Pruebas | N/A | N/A | Procedimiento definido; evidencia inexistente | Lista pegable en SEC §7.4 | Pendiente humano (condición previa al merge, no bloqueante) |

**Lectura de la tabla:** el lado API de 3.1 a 3.9 tiene diseño y prueba escrita, todo NO EJECUTADO. Las reglas del cliente (3.1 latencia, 3.2 red, 3.3 `TEST-`, 3.8 confirmación, 3.9 mensajes, 3.10 y 3.11 completos) no tienen ninguna prueba automatizada. Son exactamente las partes que el Issue sitúa en el cliente.

---

## 3. Contratos incompatibles y supuestos que se contradicen

| # | Contradicción | Entregables | Efecto |
|---|---|---|---|
| K-1 | Arquitectura excluye modificar `api/app/` (§1.3 y §1.4 listan `main.py`, `routers/`, `services.py`, `schemas.py` y `config.py` como "sin cambios"). Backend entrega un `api/app/` completo, incluidos `errors.py`, `middleware.py` y `repository.py` nuevos, más `requirements*.txt`. Backend reconoce el conflicto (A-1) y lo deja a una persona. | Arquitectura ↔ Backend | Cambio fuera del alcance. Si `api/app/` ya existe, el código entregado lo sobrescribiría o divergiría de él. **Bloqueante B-2.** |
| K-2 | Las pruebas se escribieron contra campos que Backend asumió (`documentNumber`, `scenario`, `status`, `decisionStatus`, `walletId`, `balances`, `verificationId`) y contra `code` propuestos. Arquitectura los mantiene como no confirmados (P-3, P-5, P-10). | Backend ↔ Pruebas ↔ Arquitectura | Las pruebas pueden fallar por diferencias de nombres con el `schemas.py` real. Pruebas lo trata como hallazgo (R-4). Se resuelve junto con K-1. |
| K-3 | Frontend dice que los `*.spec.ts` son del rol de Pruebas. Pruebas dice que no escribe `*.spec.ts` porque no tiene código, ruta ni ejecutor del cliente. Arquitectura asigna los `*.spec.ts` al "Frontend" sin dueño explícito. | Arquitectura ↔ Frontend ↔ Pruebas | Responsabilidad circular y entregable ausente. **Bloqueante B-1.** |
| K-4 | Pruebas ubica los archivos en `api/tests/onboarding/test_h01_*.py`. Arquitectura propone `api/tests/test_*.py` planos. Pruebas lo declara (T-3). | Arquitectura ↔ Pruebas | Menor. Se resuelve al cerrar K-1 actualizando la ruta en Arquitectura. |
| K-5 | Seguridad propone `401 UNAUTHORIZED`, `OPERATOR_TOKEN`, `APP_ENV`, `MAX_STORE_RECORDS` y el reset desactivado por defecto. Arquitectura (S-3) y el Issue no incluyen identidad, y el criterio 3.8 espera `POST /control/reset` → 200. | Seguridad ↔ Arquitectura ↔ criterio 3.8 | Las correcciones **no están aplicadas** y el propio informe pide no aplicarlas sin decisión (S-7). No contradicen nada hoy. Aplicarlas obligaría a modificar los fixtures y la spec. Ver OBS-07. |
| K-6 | Pruebas T-8 dice no haber recibido la entrega de Seguridad. Seguridad entregó después y sus pruebas propuestas (`test_h01_autorizacion.py`, `test_h01_limites.py`) no están integradas. | Pruebas ↔ Seguridad | Documental. Corresponde actualizar T-8 y R-3. Las pruebas de Seguridad solo aplican si se decide D-1. |
| K-7 | Pruebas cita la "sección 8" para el código, y está en la sección 9. | Pruebas | Errata menor. |

No hay contradicción de stack. No hay marcadores sin resolver del tipo `<VERSIÓN_...>`. Los pines de `requirements*.txt` son concretos y están **sin verificar** (condición previa al merge, OBS-06).

---

## 4. Bloqueantes de diseño (motivo de RECHAZADO)

### B-1. Las reglas del cliente de los criterios 3.1, 3.2, 3.3, 3.8, 3.9, 3.10 y 3.11 no tienen prueba ni código asociado

**Evidencia:**
- Frontend: "Sin cambios", sin `*.spec.ts`.
- Pruebas §0 y §4.2: "no escribo `*.spec.ts` con nombres inventados" y "no cuentan como cobertura". Estado `NO AUTOMATIZADO – BLOQUEADO` para 3.10 y 3.11, y para las partes de cliente de 3.1, 3.2, 3.3, 3.8 y 3.9.
- Arquitectura P-2 (ruta y ejecutor del frontend) y P-6 (ubicación de eventos y mediana, caso vacío, qué mide la mediana) siguen abiertas.
- Nadie es dueño explícito de escribir los `*.spec.ts` (K-3).

**Por qué bloquea:**
- El Issue trata de pruebas. Los entregables de prueba del cliente son parte del Issue y están ausentes.
- 3.10 y 3.11 solo tienen casos diseñados sin una unidad de código identificada.
- Hay decisiones necesarias sin resolver (P-2, P-6).
- El criterio 3.3 "documento sin `TEST-` bloqueado" no queda verificado por la prueba del servidor. Esa prueba solo comprueba una bandera opcional del API (`ENFORCE_TEST_DOC_PREFIX`), mientras que el criterio es del cliente (P-4).

### B-2. Contradicción de alcance entre Arquitectura y Backend, con pruebas ligadas a un contrato no confirmado

**Evidencia:** K-1 y K-2.
- Backend entrega código de aplicación y dependencias que Arquitectura declara fuera del alcance.
- La decisión de qué prevalece (código existente o el entregado) sigue pendiente.
- Las pruebas dependen de los nombres de campo del entregable de Backend.

**Por qué bloquea:**
- Es un cambio fuera del alcance (Issue solo de pruebas).
- Los supuestos se contradicen entre entregables.
- El contrato probado no está confirmado contra `schemas.py` ni `design.md`.

---

## 5. Observaciones, responsables y verificación

### OBS-01 (bloqueante B-1). Entregar las pruebas del cliente o resolver explícitamente su ausencia

- **Responsable:** Arquitectura (decide P-2 y P-6 y asigna dueño). Pruebas (escribe los `*.spec.ts` C-01 a C-16). Frontend (indica dónde vive cada regla, o la registra como hallazgo si no existe, según S-7).
- **Cambio requerido:**
  1. Confirmar con el repositorio la ruta del frontend, el ejecutor (Karma o Jest) y la ubicación de las reglas de latencia, `TEST-`, confirmación de reset, pasos y bloqueo, estado activo, eventos y mediana.
  2. Definir mediana con cantidad par (S-5) y con lista vacía (P-6), y qué mide.
  3. Entregar `*.spec.ts` con API simulada (S-6) que cubran C-01 a C-16, con un caso feliz y uno de error cuando aplique. Cada caso debe indicar archivo y función en la tabla de trazabilidad.
  4. Para cada regla inexistente en el cliente, registrar un hallazgo para decisión humana. No se implementa en H01.
- **Verificación:**
  - Revisión estática: cada C-xx tiene una prueba con nombre en la trazabilidad.
  - Ejecución por una persona (comando sujeto a P-2): `ng test --watch=false`.
  - Criterio de salida: código 0, cero `SKIPPED`, cero `XFAIL` y cero `XPASS`.

### OBS-02 (bloqueante B-2). Resolver el conflicto `api/app/` existente frente a lo entregado

- **Responsable:** una persona del equipo decide. Arquitectura actualiza el alcance. Backend ajusta su entrega. Pruebas realinea.
- **Cambio requerido:**
  1. Confirmar si `api/app/` ya existe. Comando: `git ls-files api/app api/tests api/requirements*.txt`.
  2. **Si existe:** Backend retira el código y los `requirements*.txt` del entregable y lo sustituye por un contraste de contrato (campos, `code`, mensajes) contra el `schemas.py` y `design.md` reales. Pruebas ajusta nombres a lo real. Cualquier discrepancia se reporta como hallazgo (S-7).
  3. **Si no existe:** Arquitectura corrige §1.3 y §1.4 para admitir la creación de `api/app/`, confirma el contrato (P-3, P-5, P-10) y deja constancia de que el Issue crece de "solo pruebas".
  4. Unificar la ruta de las pruebas (K-4).
  5. Adjuntar la tabla de `design.md` (OBS-10) para contrastar con ella.
- **Verificación:** `git diff --stat <base>..HEAD` debe mostrar solo lo permitido por el alcance acordado (por ejemplo `api/tests/**`, y `requirements-dev.txt` únicamente si P-9 lo exige). Después, `cd api && python -c "import app.main"` sin error.

### OBS-03 (no bloqueante). El 429 solo se prueba a nivel de handler

- **Responsable:** Arquitectura (confirma si el Issue exige un endpoint que lo produzca). Pruebas (mantiene el etiquetado).
- **Cambio requerido:** dejar escrito que "429" en 3.9 se cubre únicamente en el manejador común (A-6, R-2). Si el Issue exige un endpoint real, abrir un hallazgo, porque eso es funcionalidad nueva.
- **Verificación:** `test_codigos_http_generan_codigo_y_mensaje_comunes[429]` y `test_429_conserva_cabecera_retry_after` en la salida real de `pytest`.

### OBS-04 (condición previa al merge). Contenido de `tools/lab.py` desconocido

- **Responsable:** Pruebas y la persona que ejecuta.
- **Cambio requerido:** confirmar qué ejecuta `python tools/lab.py test api` (T-5, R-5). Adjuntar también la salida directa de `pytest`.
- **Verificación:** `sed -n '1,120p' tools/lab.py` y la salida íntegra de ambos comandos (sección 7).

### OBS-05 (no bloqueante). Pruebas de transporte con riesgo de depender del `TestClient`

- **Responsable:** Pruebas.
- **Cambio requerido:** si `test_post_cuerpo_chunked_sobre_el_limite_413` o `test_post_content_length_invalido_400` fallan en la línea base, corregirlas o descartarlas con justificación escrita (T-11, R-6). No atribuirlas al cambio.
- **Verificación:** `cd api && python -m pytest tests/onboarding -v -k "413 or chunked or content_length"`.

### OBS-06 (condición previa al merge). Dependencias sin verificar

- **Responsable:** Seguridad y Backend (si el manifiesto se mantiene tras OBS-02).
- **Cambio requerido:** verificar `fastapi==0.115.6`, `starlette==0.41.3`, `pydantic==2.10.3`, `uvicorn==0.34.0`, `pytest==8.3.4` y `httpx==0.28.1` contra PyPI y OSV. No hay números nuevos propuestos, porque nadie tiene datos reales. Si el repositorio ya tiene manifiesto, prevalece (A-11).
- **Verificación:** `cd api && pip check && pip install pip-audit && pip-audit -r requirements.txt && pip-audit -r requirements-dev.txt`. Criterio: sin avisos, o con una excepción escrita por cada uno.

### OBS-07 (decisión humana previa al merge). SEC-01 y SEC-02, severidad Alta

- **Responsable:** persona del equipo con Seguridad (decisiones D-1, D-2 y D-4).
- **Cambio requerido:**
  1. Dejar por escrito si el API será alcanzable por más de una persona (D-2).
  2. Elegir entre aceptar el riesgo en un laboratorio aislado o registrar un Issue aparte para el token de operador y el reset desactivado por defecto.
  3. **No aplicar** las correcciones dentro de H01 sin esa decisión: cambian el contrato (401) y obligarían a modificar los fixtures y el criterio 3.8.
  4. Si el código de Backend se mantiene (OBS-02), valorar que `ENABLE_CONTROL_RESET` quede activo por defecto.
- **Verificación:** decisión adjunta al PR. Si se corrige en otro Issue, ejecutar la secuencia `curl` de SEC-01 y `test_h01_autorizacion.py` en ese Issue.

### OBS-08 (no bloqueante). SEC-03 a SEC-07 e hipótesis HIP-1 a HIP-3

- **Responsable:** Seguridad ejecuta las comprobaciones. La persona decide sobre D-4, D-5 y D-6.
- **Cambio requerido:** ejecutar las comprobaciones de HIP-1 a HIP-3 y clasificarlas (confirmada, descartada, pendiente). SEC-03 a SEC-07 se tratan como mejoras fuera del alcance de H01, con decisión escrita.
- **Verificación:**
  - `curl -i http://127.0.0.1:8000/wallets/wlt_ffffffffffffffff%0A` (esperado: `400`).
  - Las pruebas propuestas en SEC-04, SEC-06 y SEC-07, si se aceptan.

### OBS-09 (no bloqueante). Documentación de Pruebas desactualizada

- **Responsable:** Pruebas.
- **Cambio requerido:** actualizar T-8 y R-3 (la entrega de Seguridad ya existe), corregir la referencia "sección 8" por 9 (K-7), y marcar las pruebas de Seguridad propuestas como "pendientes de D-1".
- **Verificación:** relectura del `testing_report.md`.

### OBS-10 (parte de B-2). La tabla de `design.md` y `spec.md` no están disponibles

- **Responsable:** Arquitectura.
- **Cambio requerido:** adjuntar la tabla de `design.md` y el `spec.md`, y contrastarla fila por fila con los 8 endpoints, los `code` y los códigos HTTP.
- **Verificación:** matriz endpoint → `design.md` → prueba. Cualquier diferencia se registra como hallazgo (S-7).

---

## 6. Evidencia a favor (lo que sí está bien, según lectura estática)

- Cada criterio de API (3.4 a 3.7) tiene un camino feliz y uno de error con pruebas nombradas, y la trazabilidad de Pruebas coincide con las funciones del código entregado.
- Formato de error único `{"code","message"}`, con 422 convertido en 400, sin eco de valores ni trazas (código de `errors.py` y pruebas `test_400_no_repite_valores_enviados` y `test_500_no_filtra_detalles_internos`).
- Sin persistencia en disco. Aislamiento por prueba con un fixture `autouse`, sin paralelismo (T-7, R-8).
- Ningún entregable afirma haber ejecutado algo ni inventa salidas. Todos usan NO EJECUTADO.
- Seguridad no detecta vectores de inyección ni secretos en el código revisado, y declara que no revisó el cliente.

---

## 7. Pruebas y verificaciones pendientes (todas NO EJECUTADAS)

| # | Qué | Responsable | Comando exacto | Evidencia |
|---|---|---|---|---|
| P1 | Anotar el commit base y el estado | Persona que ejecuta | `git status --short && git rev-parse HEAD` | Salida íntegra |
| P2 | Entorno y dependencias | Persona que ejecuta | `cd api && python --version && python -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt && pip check && pip freeze \| grep -iE "^(fastapi\|starlette\|pydantic\|uvicorn\|httpx\|pytest)=="` | Salida íntegra |
| P3 | Línea base con `lab.py` | Persona que ejecuta | `python tools/lab.py test api 2>&1 \| tee salida_h01_fase1_lab.txt` (desde la raíz) | Archivo adjunto |
| P4 | Suite completa del API | Persona que ejecuta | `cd api && python -m pytest tests -v -rA --strict-markers 2>&1 \| tee ../salida_h01_fase1_pytest.txt` | Archivo adjunto |
| P5 | Solo las pruebas nuevas | Persona que ejecuta | `cd api && python -m pytest tests/onboarding -v -rA --strict-markers 2>&1 \| tee ../salida_h01_fase1_h01.txt` | Archivo adjunto |
| P6 | Cero `SKIPPED`, `XFAIL` y `XPASS` | Persona que ejecuta | `grep -E " (SKIPPED\|XFAIL\|XPASS)" ../salida_h01_fase1_pytest.txt` | Debe no producir salida |
| P7 | Vulnerabilidades de dependencias | Seguridad | `cd api && pip-audit -r requirements.txt && pip-audit -r requirements-dev.txt` | Salida íntegra o excepciones escritas |
| P8 | Pruebas del cliente | Pruebas con la persona que ejecuta | `ng test --watch=false` (sujeto a P-2) | **Bloqueado hasta cerrar OBS-01** |
| P9 | Fase 2 (solo si se aplica código tras la línea base) | Persona que ejecuta | Repetir P3 a P5 con salidas `*_fase2_*.txt` y comparar | Diferencias; si no se aplica nada, "Fase 2: no aplica" |
| P10 | Hipótesis HIP-1 a HIP-3 | Seguridad | Los comandos de SEC §5 | Salida íntegra |
| P11 | Confirmación de SEC-01 antes de corregir (si D-2 lo exige) | Seguridad | La secuencia `curl` de SEC-01 | Salida íntegra |

---

## 8. Condiciones previas al merge (no son motivo de rechazo por sí solas)

1. Ejecutar P1 a P6 y adjuntar la salida real y completa al PR (tarea 3.12). Nadie la redacta ni la resume.
2. Clasificar cada fallo como error de la prueba (se corrige), prueba no verificable (se descarta con justificación) o defecto del API (hallazgo, S-7). Ningún fallo de la línea base se atribuye al cambio.
3. Ejecutar P7 (`pip check` y `pip-audit`) y adjuntar la salida.
4. Ejecutar P8 cuando existan los `*.spec.ts` del cliente.
5. Decisión escrita sobre SEC-01 y SEC-02 (OBS-07) y estado de HIP-1 a HIP-3.
6. Confirmar `tools/lab.py` (OBS-04).
7. Aprobaciones humanas de la sección 9.

---

## 9. Aprobaciones humanas (conservadas; este informe no las sustituye)

| Aprobación | Estado | Quién |
|---|---|---|
| Confirmación del stack Python/FastAPI | **Ya confirmada por una persona** (según instrucciones del flujo) | Equipo |
| Decisión sobre `api/app/` existente frente al entregado (OBS-02) | Pendiente | Persona del equipo |
| Respuestas a P-2, P-3, P-5, P-6 y P-10 | Pendientes | Persona / Arquitectura |
| Aceptación de la suposición "no hay cobertura previa" de POST (P-8) | Pendiente | Persona del equipo |
| Decisiones D-1 a D-8 de Seguridad | Pendientes | Persona del equipo |
| Ejecución de pruebas y adjunto de la salida real al PR (3.12) | Pendiente | Persona responsable del PR |
| Aprobación final del PR | Pendiente; depende de la evidencia ejecutada | Persona revisora |

---

## 10. Correcciones requeridas para una nueva revisión

1. **OBS-01:** cerrar P-2 y P-6, asignar dueño a los `*.spec.ts` y entregar las pruebas del cliente para C-01 a C-16, o registrar como hallazgo cada regla inexistente con decisión humana.
2. **OBS-02 y OBS-10:** resolver el conflicto `api/app/` existente frente a entregado, alinear alcance, ruta de pruebas y contrato con `design.md` y `schemas.py` reales, y adjuntar la tabla de `design.md`.
3. Actualizar el `testing_report.md` (OBS-09) y registrar la decisión de OBS-03 sobre el 429.
4. Con eso, la nueva revisión podría emitir APROBADO, con las condiciones de la sección 8 aún pendientes de ejecución humana.

---

## 11. Veredicto

**Motivos:**
- **B-1:** los criterios 3.10 y 3.11 no tienen implementación ni prueba del cliente. Las partes de cliente de 3.1, 3.2, 3.3, 3.8 y 3.9 tampoco. Los casos C-01 a C-16 son solo diseño, bloqueados por decisiones abiertas (P-2, P-6) y sin dueño asignado entre Frontend y Pruebas.
- **B-2:** Arquitectura y Backend se contradicen sobre si se modifica `api/app/`, hay cambios fuera del alcance (código de aplicación y dependencias) y las pruebas dependen de un contrato no confirmado.

**Lo que no es motivo de rechazo:**
- El stack: equivalencias legadas traducidas de forma coherente, supuesto confirmado.
- Que nada esté ejecutado, y que falten la salida real y las aprobaciones humanas: son condiciones previas al merge (sección 8).
- Los hallazgos de Seguridad no aplicados: requieren decisión humana (OBS-07).

La aprobación final depende de resolver B-1 y B-2 y de la evidencia ejecutada por una persona. En este informe no se afirma que ninguna prueba haya pasado.

VEREDICTO: RECHAZADO — bloqueantes de diseño: B-1 (reglas del cliente de 3.1, 3.2, 3.3, 3.8, 3.9, 3.10 y 3.11 sin prueba ni dueño, con P-2 y P-6 sin resolver) y B-2 (contradicción Arquitectura↔Backend sobre `api/app/`, cambios fuera de alcance y contrato de pruebas no confirmado).