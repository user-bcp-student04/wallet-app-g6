# user_story.md

## Historia de usuario H01: Pruebas del onboarding

**Como** persona del equipo que mantiene el onboarding de la wallet,
**quiero** una cobertura básica de pruebas por endpoint (camino feliz y un camino de error) y de las reglas del flujo de onboarding en el cliente,
**para** detectar regresiones en el registro y la activación de la wallet y adjuntar al PR evidencia real de su ejecución.

**Fuentes del Issue:**
- Spec: `openspec/changes/registro-activacion-wallet/specs/wallet-onboarding/spec.md`
- Tareas: `openspec/changes/registro-activacion-wallet/tasks.md` (grupo 3, tareas 3.1 a 3.12)
- La tabla de `design.md` se cita como referencia, pero **su contenido no está en el contexto**.

**Convención usada en este documento:**
- **[Explícito]**: dato tomado del Issue.
- **[Supuesto]**: decisión conservadora mía, no fijada por el Issue, que debe confirmarse.
- **[Pregunta]**: información faltante, con la decisión provisional indicada.

---

## 1. Resumen del cambio y alcance

### 1.1 Resumen
- **[Explícito]** El cambio consiste en añadir pruebas, no funcionalidad. Cada endpoint recibe un camino feliz y un camino de error, y se cubren las reglas del onboarding visibles en el cliente.
- **[Explícito]** El Issue mezcla pruebas de API y de cliente. Son del cliente: "latencia inválida bloqueada en cliente" (3.1), "documento sin `TEST-` bloqueado" (3.3), "cancelar la confirmación no llama a la API" (3.8) y los pasos y el bloqueo del onboarding (3.10).
- **[Explícito]** Endpoints en alcance:
  - `GET /health`
  - `GET /scenarios`
  - `POST /kyc/verifications`
  - `GET /kyc/verifications/{id}`
  - `POST /kyc/verifications/{id}/decision`
  - `GET /wallets/{id}`
  - `GET /support/cases`
  - `POST /control/reset`

### 1.2 Dentro del alcance
- Pruebas automatizadas del API (Python/FastAPI) en `api/tests/`.
- Pruebas automatizadas del cliente Angular para las reglas descritas en 3.1, 3.2, 3.3, 3.8, 3.10 y 3.11.
- Verificación del manejador de errores común (3.9).
- Ejecución de las pruebas por una persona y adjunto de la salida real al PR (3.12).

### 1.3 Fuera del alcance
- Nuevos endpoints, cambios de contrato o de lógica de negocio. Si una prueba revela una discrepancia con la spec, se **reporta como hallazgo** y no se corrige en este cambio, salvo decisión explícita de una persona.
- Autenticación o identidad de usuario. El Issue no la menciona **[Supuesto]**, ver sección 5.
- Actualización de dependencias. El Issue **no la pide**, así que no hay pines de versión ni comparación de endpoints contra PyPI/OSV. Si faltan `pytest` o `httpx` para `TestClient`, ver pregunta P-9.

### 1.4 Archivos que cambian
- **API [Supuesto]:** solo archivos nuevos en `api/tests/`.
  - `conftest.py`
  - `test_health.py`
  - `test_scenarios.py`
  - `test_kyc_verifications.py`
  - `test_kyc_decision.py`
  - `test_wallets.py`
  - `test_support_cases.py`
  - `test_control_reset.py`
  - `test_error_handler.py`
- **Frontend:** archivos `*.spec.ts` nuevos. La ruta no está indicada (P-2).
- **No se modifican** `api/app/main.py`, `routers/`, `services.py`, `schemas.py` ni `config.py`.

---

## 2. Componentes afectados, responsabilidades y límites

| Componente | Ubicación | Responsabilidad en este cambio | Límite |
|---|---|---|---|
| Suite de pruebas del API | `api/tests/` **[Supuesto]** | Verificar status, `code` y forma del cuerpo de cada endpoint con `TestClient` de FastAPI | No modifica código bajo `api/app/` |
| Fixture de aislamiento | `api/tests/conftest.py` **[Supuesto]** | Dar a cada prueba un estado limpio (cliente nuevo o llamada a `POST /control/reset`) | No introduce persistencia nueva |
| Routers | `api/app/routers/` | Bajo prueba, sin cambios | Sin cambios |
| `services.py` | `api/app/services.py` | Bajo prueba (decisión sobre `PENDING`, casos `KYC_REVIEW`, saldos) | Sin cambios |
| `schemas.py` | `api/app/schemas.py` | Define los cuerpos que las pruebas verifican | Sin cambios |
| Manejador de errores común | `api/app/main.py` **[Supuesto]** | Bajo prueba: convierte errores en `{"code","message"}` | Sin cambios; si no existe, es una brecha (P-5) |
| Cliente Angular, validaciones y estado del onboarding | Ruta por confirmar (P-2) | Probar bloqueos (latencia, `TEST-`, datos faltantes o inválidos), pasos visibles, estado activo y confirmación de reset | Pruebas con API simulada, sin red real |
| Servicio de eventos y métricas | Ubicación por confirmar (P-6) | Probar eventos `completo` y `abandonado` y el cálculo de mediana | Según P-6 |
| PR | Repositorio | Contiene la salida real de las pruebas, ejecutadas por una persona | La salida no puede fabricarse ni resumirse |

---

## 3. Contrato de API relevante

El Issue y `tasks.md` solo fijan estados y códigos. **No se dispone** de `spec.md` ni de `design.md`, así que los cuerpos de petición y respuesta completos no pueden determinarse. No se inventan nombres de campo. Los ejemplos usan únicamente valores citados en el Issue, y los campos no confirmados se marcan.

### 3.1 Formato de error único **[Supuesto, decisión cerrada]**

```json
{ "code": "KYC_UNAVAILABLE", "message": "Texto accionable en español" }
```

Los códigos HTTP del Issue son 400, 404, 409, 413, 429 y 503. Solo dos `code` están dados por el Issue. Los demás son **propuesta conservadora a confirmar contra `design.md`**:

| HTTP | `code` | Origen | Endpoints donde aparece según el Issue |
|---|---|---|---|
| 400 | `BAD_REQUEST` | Supuesto | Entrada inválida (3.9) |
| 404 | `NOT_FOUND` | Supuesto | `GET /kyc/verifications/{id}` (3.4), `GET /wallets/{id}` (3.6) |
| 409 | `DECISION_CONFLICT` | **Explícito** | `POST /kyc/verifications/{id}/decision` (3.5) |
| 413 | `PAYLOAD_TOO_LARGE` | Supuesto | Tamaño excedido (3.9); endpoint por confirmar |
| 429 | `RATE_LIMITED` | Supuesto | Límite de peticiones (3.9); endpoint por confirmar |
| 503 | `KYC_UNAVAILABLE` | **Explícito** | `POST /kyc/verifications` (3.3) |

**Nota:** FastAPI devuelve por defecto `422` en errores de validación. El Issue pide `400`, así que hace falta un manejador de `RequestValidationError` que lo convierta (P-5).

### 3.2 Endpoints

| Endpoint | Entrada | Éxito **[Explícito]** | Error **[Explícito]** |
|---|---|---|---|
| `GET /health` | Ninguna | `200` | No definido para el API. La latencia inválida se bloquea en el cliente |
| `GET /scenarios` | Ninguna | `200`, lista que llena el selector | Error de red en el cliente con mensaje legible |
| `POST /kyc/verifications` | Cuerpo con documento. Campos por confirmar (P-3) | `201` con estado `APPROVED`, `REJECTED` o `MANUAL_REVIEW` | `503 KYC_UNAVAILABLE`. Documento sin prefijo `TEST-` bloqueado (en cliente, ver P-4) |
| `GET /kyc/verifications/{id}` | `id` en la ruta | `200` | `404` |
| `POST /kyc/verifications/{id}/decision` | `id` en la ruta y cuerpo de decisión (campos por confirmar) | `200` sobre una verificación `PENDING` | `409 DECISION_CONFLICT` si no está `PENDING` |
| `GET /wallets/{id}` | `id` en la ruta | `200` con saldos en 0 | `404` |
| `GET /support/cases` | Ninguna | `200` con caso `KYC_REVIEW` en estado `OPEN`, o lista vacía | Sin error definido |
| `POST /control/reset` | Ninguna | `200`, limpia estado | Sin error definido |

### 3.3 Ejemplos
Los ejemplos incluyen solo valores citados en el Issue. Los demás campos de los cuerpos son **por confirmar** y no se muestran.

**Error de conflicto** (`POST /kyc/verifications/{id}/decision`, la verificación ya no está `PENDING`):
```http
HTTP/1.1 409 Conflict
Content-Type: application/json

{"code": "DECISION_CONFLICT", "message": "La verificación ya fue decidida y no puede modificarse."}
```

**Servicio KYC no disponible** (`POST /kyc/verifications`):
```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{"code": "KYC_UNAVAILABLE", "message": "El servicio de verificación no está disponible. Intente de nuevo más tarde."}
```
El texto de `message` es **ilustrativo [Supuesto]**; el Issue solo exige que sea accionable.

**Verificación creada** (`POST /kyc/verifications`):
```http
HTTP/1.1 201 Created
```
El cuerpo contiene un estado entre `APPROVED`, `REJECTED` y `MANUAL_REVIEW`. El nombre exacto del campo (¿`status`?) está **por confirmar** (P-3).

### 3.4 Qué falta para cerrar el contrato
Los `schemas.py` reales y `design.md` (P-1, P-3, P-5, P-7).

---

## 4. Trazabilidad de criterios de aceptación

Comando propuesto **[Supuesto]**: `cd api && python -m pytest tests -v`. Para el cliente: `ng test --watch=false`. El ejecutor de pruebas del frontend (Karma o Jest) no está confirmado (P-2).

| ID | Criterio | Componente responsable | Cómo se comprueba |
|---|---|---|---|
| 3.1 | `GET /health` devuelve `200`; latencia inválida bloqueada en cliente | API (health) y validación del cliente | API: `GET /health` y se afirma el status 200. Cliente: con latencia inválida el envío queda bloqueado y el espía del servicio HTTP registra 0 llamadas |
| 3.2 | `GET /scenarios` llena el selector; error de red con mensaje legible | API (scenarios) y componente selector | API: `200` y lista no vacía. Cliente: con respuesta simulada el selector muestra las opciones. Con fallo de red simulado se muestra un mensaje legible y no un error técnico |
| 3.3 | `POST /kyc/verifications` devuelve `201` en `APPROVED`, `REJECTED` y `MANUAL_REVIEW`; `503 KYC_UNAVAILABLE`; documento sin `TEST-` bloqueado | API (KYC) y validación del cliente | API: prueba parametrizada de los 3 estados con status 201. Caso 503 con cuerpo `{"code":"KYC_UNAVAILABLE",...}`. Cliente: documento sin `TEST-` y 0 llamadas al API. El mecanismo para provocar cada estado y el 503 se define en P-3 |
| 3.4 | `GET /kyc/verifications/{id}` devuelve `200` y `404` | API (KYC) | Se crea una verificación, se consulta por su id y se afirma `200`. Con id inexistente se afirma `404` con `code` y `message` |
| 3.5 | `POST .../decision` devuelve `200` sobre `PENDING` y `409 DECISION_CONFLICT` | API (KYC, decisión) | Se obtiene una verificación `PENDING` (vía `MANUAL_REVIEW`, ver P-3) y se decide: `200`. Una segunda decisión sobre la misma devuelve `409` con `code` `DECISION_CONFLICT` |
| 3.6 | `GET /wallets/{id}` devuelve `200` con saldos 0 y `404` | API (wallets) | Se consulta una wallet existente: `200` y todos los saldos iguales a 0. Con id inexistente: `404` |
| 3.7 | `GET /support/cases` devuelve caso `KYC_REVIEW` `OPEN` y lista vacía | API (support) | Con estado limpio: lista vacía. Tras una verificación que genera revisión: un caso de tipo `KYC_REVIEW` con estado `OPEN`. Qué lo genera: P-7 |
| 3.8 | `POST /control/reset` devuelve `200` y limpia estado local; cancelar la confirmación no llama a la API | API (control) y cliente | API: se crea estado, se llama al reset y se verifica `200` y estado vacío con `GET /support/cases`. Cliente: se confirma y se afirma 1 llamada más limpieza del estado local. Se cancela y se afirma 0 llamadas con el estado intacto |
| 3.9 | Manejador de errores común: `400`, `404`, `409`, `413`, `429`, `503` con mensaje accionable | Manejador de errores (API) y manejo de errores del cliente | API: por cada código se afirma que el cuerpo es exactamente `{"code","message"}` con `message` no vacío. Cliente: por cada código se simula la respuesta y se verifica que se muestra el `message`. Cómo se provocan 413 y 429: P-5 |
| 3.10 | Pasos visibles, bloqueo con dato faltante o inválido, estado activo solo tras onboarding exitoso (no con incompleto, `PENDING` ni `REJECTED`) | Componentes de onboarding del cliente | Pruebas de componente: se afirman los pasos visibles. Con dato faltante o inválido, el avance queda bloqueado. Tabla parametrizada de estados: solo el onboarding exitoso (`APPROVED`) produce "activo"; incompleto, `PENDING` y `REJECTED` no |
| 3.11 | Eventos (completo y abandonado) y cálculo de mediana | Servicio de eventos/métricas (ubicación en P-6) | Se emiten ambos eventos y se verifica su registro. Mediana con cantidad impar (valor central) y par (**[Supuesto]** promedio de los dos centrales). Caso vacío según P-6 |
| 3.12 | Adjuntar al PR la salida real de las pruebas ejecutadas por una persona | Proceso (persona responsable del PR) | La descripción del PR incluye la salida completa, con fecha, de `python -m pytest tests -v` y de `ng test --watch=false`. Nadie la redacta ni la resume a mano |

**Brecha declarada:** no se sabe qué pruebas existentes cubren POST con cuerpo válido (P-8). Hasta confirmarlo, se asume que **no hay cobertura previa** y 3.3 y 3.5 la crean desde cero. Una persona debe aceptar o corregir esta suposición.

---

## 5. Supuestos y preguntas pendientes

### 5.1 Supuestos y decisiones conservadoras

| # | Supuesto |
|---|---|
| S-1 | Las pruebas del API van en `api/tests/` y no modifican `api/app/`. |
| S-2 | Los errores siguen un único cuerpo `{"code","message"}`. Los `code` fuera de `KYC_UNAVAILABLE` y `DECISION_CONFLICT` son propuestos (3.1). |
| S-3 | **Identidad:** el Issue no menciona identidad ni propietario. Este cambio no introduce identidad ni directorios de propietario. Si una prueba requiere identidad, se resolverá con una dependencia de FastAPI, nunca con un valor enviado por el cliente. En ese caso el directorio del propietario se derivaría con SHA-256 del identificador, y ningún valor derivado se expondría en respuestas. El `401` del ejemplo general no aplica porque el Issue no lo pide. |
| S-4 | **Persistencia y concurrencia:** el estado se supone en memoria, ya que `POST /control/reset` lo limpia. Riesgos y mitigaciones: (a) *concurrencia del mismo usuario*: las pruebas corren en serie y cada una limpia el estado en `conftest.py`; no se usa `pytest-xdist`. (b) *estado preexistente*: se resetea al inicio de cada prueba, sin depender del orden. (c) *migración*: no aplica, no hay esquema ni archivos nuevos. Si el estado resulta ser en archivos, hay que reevaluar (P-1). |
| S-5 | Mediana con cantidad par: promedio de los dos valores centrales. |
| S-6 | Las pruebas del cliente usan un servicio HTTP simulado, no red real. |
| S-7 | Frente a una discrepancia con la spec, la prueba se reporta como hallazgo y no se corrige la lógica en este cambio. |

### 5.2 Preguntas pendientes

| # | Pregunta | Decisión provisional |
|---|---|---|
| P-1 | ¿Dónde están los archivos reales del API y del estado (en memoria o en disco)? | Memoria, con reset por prueba |
| P-2 | ¿Cuál es la ruta del frontend y su ejecutor de pruebas (Karma o Jest)? | `*.spec.ts` junto a cada componente; `ng test --watch=false` |
| P-3 | ¿Cuáles son los campos exactos de `POST /kyc/verifications` y de `.../decision`? ¿Cómo se provoca cada resultado (`APPROVED`, `REJECTED`, `MANUAL_REVIEW`) y el `503`: con el escenario elegido, con el documento o con un parámetro? | No se inventan campos. Hasta responder, 3.3 y 3.5 quedan sin cuerpo fijado |
| P-4 | ¿El prefijo `TEST-` también debe rechazarse en el servidor o solo en el cliente? | Solo cliente, como dice el Issue |
| P-5 | ¿Existe ya un manejador común de errores que produzca `{"code","message"}` y convierta 422 en 400? ¿Qué endpoints devuelven 413 y 429 y cómo se provocan? | Se verifica el manejador existente. Si falta, es una brecha que una persona debe decidir |
| P-6 | ¿Dónde vive el cálculo de mediana y los eventos (cliente o API)? ¿Qué debe devolver con lista vacía? ¿Qué mide la mediana? | Cliente; se prueba como función pura. Caso vacío: se omite hasta definirlo |
| P-7 | ¿Qué crea el caso `KYC_REVIEW` `OPEN`? | Una verificación en `MANUAL_REVIEW` |
| P-8 | ¿Qué pruebas existentes cubren POST con cuerpo válido? | Ninguna (brecha declarada, sección 4) |
| P-9 | ¿Están `pytest` y `httpx` ya en `requirements*.txt`? | Si no, se requeriría un cambio en `requirements*.txt` con versiones exactas (`paquete==versión`, incluido `starlette==`), confirmadas con PyPI y OSV. No se proponen números sin esos datos. Este es el único caso en que cambiaría un requirements |
| P-10 | ¿Qué contiene la tabla de `design.md` que el Issue cita como base? | Se usa solo lo literal de `tasks.md` |