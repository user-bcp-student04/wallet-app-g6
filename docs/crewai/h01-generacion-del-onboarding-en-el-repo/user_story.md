# user_story.md — [H01] Generación del onboarding en el repo destino

> **Fuentes.** Solo dispongo del título del Issue, la ruta de la spec (`openspec/changes/registro-activacion-wallet/specs/wallet-onboarding/spec.md`) y la lista de tareas del grupo 2. **El contenido de la spec no está en mi contexto.** Por eso los criterios de aceptación (CA) de la sección 4 se derivan literalmente del texto de cada tarea y están marcados como *derivados*. Todo lo que no figura en el Issue se marca como **Supuesto (S-n)** o **Pregunta (P-n)** en la sección 5.
> **Dependencias.** El Issue no pide actualizar paquetes, así que no se toca ningún `requirements*.txt` (ver 2.4).

---

## 1. Resumen del cambio y alcance

**Historia de usuario (redacción derivada de las tareas).**
Como persona usuaria nueva de la wallet, quiero un flujo de onboarding guiado, con pasos visibles, paso actual, validación con bloqueo y verificación KYC, para activar mi wallet y acceder a pagos de bajo monto. Como equipo de producto y soporte, quiero eventos de onboarding, una consola de servicios y una salida analítica mensual para medir la activación y operar el mock.

**Dentro del alcance (explícito en las tareas 2.2 a 2.8):**
- 2.2 Servicio tipado `MockApiService`, con interfaces de request y response por endpoint, y un único `SessionService`.
- 2.3 Estado de wallet y validación de pasos con bloqueo, documento con prefijo `TEST-` y mensajes accionables.
- 2.4 `POST /kyc/verifications` con cuatro escenarios, consulta y decisión sobre `PENDING`.
- 2.5 Registro de eventos de inicio, paso y cierre, y cálculo de duración.
- 2.6 Interfaz: flujo guiado y acceso a pagos de bajo monto según el estado de la wallet.
- 2.7 Consola de servicios: `GET /health`, `GET /scenarios`, `GET /support/cases`, ejecución individual, errores legibles y `POST /control/reset` con confirmación.
- 2.8 Salida analítica mensual de nuevos usuarios activos y gasto atribuido.

**Fuera del alcance:**
- La tarea 2.1, ya completada (`[x]`). Su parte «revisar contra la spec» queda abierta, porque la spec no está en mi contexto (P-1).
- Autenticación real, pagos reales y KYC real. El contexto habla de un *mock* y de documentos `TEST-` (S-1).
- Cualquier endpoint de pagos: el Issue solo exige *acceso* a pagos de bajo monto según el estado de la wallet (P-6).
- Actualización de dependencias.

---

## 2. Componentes afectados, responsabilidades y límites

Stack cerrado: Python + FastAPI (Starlette) para el API y Angular para el frontend. Las rutas del backend son las definidas por la decisión de arquitectura; las del frontend no están en el contexto (P-2).

| Componente | Ubicación | Responsabilidad | Límite (qué NO hace) |
|---|---|---|---|
| Arranque y manejo de errores | `api/app/main.py` | Crea la app, registra los routers y define los *exception handlers*. Todo error sale como `{"code","message"}`, incluidos los de validación de FastAPI (`RequestValidationError`). Aplica el límite de tamaño de cuerpo. | Sin lógica de negocio. |
| Configuración | `api/app/config.py` | Directorio de datos, límite de cuerpo en bytes, ventana de pasos y parámetros del mock, leídos de entorno. | Sin lógica; solo valores. |
| Esquemas | `api/app/schemas.py` | Modelos Pydantic de request, response y error de cada endpoint. Son la fuente del contrato que `MockApiService` refleja en TypeScript. | No expone ningún valor derivado del propietario. |
| Router de servicios (consola) | `api/app/routers/` (p. ej. `console.py`) | `GET /health`, `GET /scenarios`, `GET /support/cases`, `POST /control/reset`. | No contiene reglas de onboarding. |
| Router KYC | `api/app/routers/` (p. ej. `kyc.py`) | `POST /kyc/verifications`, consulta y decisión sobre `PENDING`. | No decide el estado de la wallet; delega en `services.py`. |
| Router de onboarding | `api/app/routers/` (p. ej. `onboarding.py`) | Estado de wallet, avance de pasos y validación con bloqueo (rutas en P-4). | No calcula analítica. |
| Servicios de dominio | `api/app/services.py` | Dependencia de identidad `get_current_owner`, almacén por propietario (lock, escritura atómica), reglas de pasos y bloqueo, validación `TEST-`, escenarios KYC, registro de eventos, duración y salida analítica mensual (2.8). | No lee identidad del cuerpo ni de parámetros del cliente. |
| Pruebas | `api/tests/` | Pruebas de contrato y de reglas por endpoint (sección 4). | — |
| Frontend: `MockApiService` | Ruta Angular a confirmar (P-2) | Cliente tipado: una interfaz de request y una de response por endpoint, espejo de `schemas.py`. Mapea `{"code","message"}` a mensajes accionables. | No contiene reglas de negocio. |
| Frontend: `SessionService` | Ruta Angular a confirmar (P-2) | Servicio único (*singleton*) con la sesión del flujo (paso actual, estado de wallet cacheado). | No hay segunda fuente de sesión. |
| Frontend: flujo guiado y consola | Ruta Angular a confirmar (P-2) | Pasos visibles y paso actual, acceso a pagos de bajo monto según el estado de la wallet, ejecución individual de servicios y confirmación antes de `POST /control/reset`. | No llama al API sin pasar por `MockApiService`. |

**Convención de identidad (decisión cerrada, ver S-2).** El propietario nunca llega en el cuerpo ni en la URL. Lo resuelve la dependencia `get_current_owner` en `api/app/services.py`. El identificador es una cadena opaca de 1 a 128 caracteres `[A-Za-z0-9._-]`. El directorio de datos es `DATA_DIR/<sha256(owner_id en UTF-8).hexdigest()>/`. Ni el identificador ni el hash aparecen en respuestas, mensajes de error ni logs de cliente.

---

## 3. Contrato de API relevante

### 3.1 Endpoints nombrados explícitamente en el Issue

| Endpoint | Entrada | Éxito | Notas |
|---|---|---|---|
| `GET /health` | Ninguna | 200 | Cuerpo no definido en el Issue (S-3). |
| `GET /scenarios` | Ninguna | 200 | Lista los escenarios ejecutables desde la consola. Estructura no definida (P-3). |
| `GET /support/cases` | Ninguna | 200 | Estructura no definida (P-3). |
| `POST /kyc/verifications` | Cuerpo JSON con el documento y el escenario (campos en P-3) | Creación con estado de verificación, posiblemente `PENDING` | Cuatro escenarios; sus nombres no están en el contexto (P-3). |
| `POST /control/reset` | Ninguna (S-5) | 200 | La confirmación es de interfaz (S-5). |

### 3.2 Endpoints sin nombre en el Issue (provisionales)

El Issue exige las capacidades (consulta y decisión sobre `PENDING`, estado de wallet, avance de pasos), pero no fija sus rutas. Propongo nombres coherentes con `/kyc/verifications` solo para poder diseñar y probar. **Son supuestos (S-4) y deben confirmarse antes de implementar:**

- `GET /kyc/verifications/{verification_id}`: consulta de una verificación.
- `POST /kyc/verifications/{verification_id}/decision`: decisión sobre una verificación en `PENDING`.
- `GET /onboarding`: estado de wallet y paso actual del propietario.
- `POST /onboarding/steps/{step_id}`: envío y validación de un paso.

Los eventos de inicio, paso y cierre (2.5) **no tienen endpoint público**. Se registran en el servidor como efecto de las transiciones de `services.py` (S-6).

### 3.3 Formato de error único

Todo error responde con este cuerpo, sin campos adicionales:

```json
{"code": "STEP_BLOCKED", "message": "Completa la verificación KYC antes de continuar."}
```

| HTTP | `code` | Cuándo (decisión conservadora, S-7) |
|---|---|---|
| 401 | `UNAUTHENTICATED` | La dependencia `get_current_owner` no obtiene identidad válida. |
| 404 | `NOT_FOUND` | Verificación o paso inexistente. |
| 409 | `STEP_BLOCKED` | Se intenta un paso cuyo requisito previo no está cumplido. |
| 409 | `VERIFICATION_NOT_PENDING` | Se decide sobre una verificación que no está en `PENDING`. |
| 413 | `PAYLOAD_TOO_LARGE` | El cuerpo supera `config.MAX_BODY_BYTES`. Valor conservador: 16384, ajustable. |
| 422 | `VALIDATION_ERROR` | El cuerpo no cumple el esquema (reemplaza el formato por defecto de FastAPI). |
| 422 | `DOCUMENT_NOT_TEST` | El documento no tiene prefijo `TEST-`. |
| 500 | `INTERNAL_ERROR` | Error no controlado, con mensaje genérico sin detalles internos. |

### 3.4 Ejemplos (ilustrativos; campos y escenarios por confirmar en P-3)

Documento rechazado:
```http
POST /kyc/verifications
Content-Type: application/json

{"document_number": "12345678", "scenario": "<escenario>"}
```
```http
HTTP/1.1 422
{"code": "DOCUMENT_NOT_TEST", "message": "El documento debe comenzar con 'TEST-' en este entorno de pruebas."}
```

Sin identidad:
```http
HTTP/1.1 401
{"code": "UNAUTHENTICATED", "message": "No se pudo identificar al usuario."}
```

El ejemplo de éxito de `POST /kyc/verifications` no puede escribirse sin inventar campos y escenarios. Falta el listado de campos y de los cuatro escenarios (P-3).

### 3.5 Riesgos de persistencia (S-8)

Si el estado del mock se guarda en archivos por propietario (a confirmar en P-5):
- **Concurrencia del mismo usuario.** Hay un `threading.Lock` por propietario dentro de `services.py` para la secuencia leer, validar y escribir. Las escrituras son atómicas (archivo temporal + `os.replace`). Con varios workers se necesitaría un bloqueo de archivo, y se asume un solo proceso.
- **Archivos preexistentes.** Si el directorio del hash ya existe, se reutiliza. Un JSON ilegible o corrupto devuelve `INTERNAL_ERROR` y no se sobrescribe silenciosamente. `POST /control/reset` solo borra el estado del propietario autenticado.
- **Migración.** No aplica: no hay datos previos. Cada archivo lleva un campo `schema_version` para migraciones futuras.

---

## 4. Trazabilidad de criterios de aceptación

Los CA son *derivados* del texto de cada tarea. La spec debe confirmarlos o corregirlos (P-1). Pruebas bajo `api/tests/` con `pytest` y `TestClient` de FastAPI. Las pruebas del frontend usan el runner Angular existente (a confirmar en P-2).

| CA (derivado) | Componente responsable | Cómo verificarlo |
|---|---|---|
| **CA-2.2a** Existe una interfaz de request y otra de response por cada endpoint del mock. | Frontend `MockApiService`; espejo de `schemas.py` | Prueba unitaria Angular: cada método tipa su request y response. Revisión cruzada de los campos contra `schemas.py`. |
| **CA-2.2b** Hay un único `SessionService`. | Frontend `SessionService` | Prueba Angular: dos inyecciones devuelven la misma instancia. Búsqueda en el código: no hay otro proveedor de sesión. |
| **CA-2.3a** El estado de wallet se calcula y expone de forma consistente. | `services.py`, router de onboarding | `api/tests/test_onboarding.py`: `GET /onboarding` por cada transición de estado. |
| **CA-2.3b** Un paso con requisito previo incumplido se bloquea. | `services.py`, router de onboarding | Prueba: enviar el paso N+1 sin completar N responde 409 `STEP_BLOCKED`. |
| **CA-2.3c** Solo se aceptan documentos con prefijo `TEST-`. | `services.py`, `schemas.py` | Prueba parametrizada: `TEST-123` pasa y `123`, `test-123` y vacío responden 422 `DOCUMENT_NOT_TEST` o `VALIDATION_ERROR`. |
| **CA-2.3d** Los mensajes de error son accionables. | `services.py` (texto), frontend (presentación) | Prueba: `message` no vacío e indica la acción a seguir. Prueba Angular: se muestra el `message` del API. |
| **CA-2.4a** `POST /kyc/verifications` soporta los cuatro escenarios. | Router KYC, `services.py` | Prueba parametrizada con los cuatro escenarios, ya enumerados (P-3). |
| **CA-2.4b** Una verificación se puede consultar. | Router KYC | Prueba: crear y luego consultar; un id inexistente responde 404 `NOT_FOUND`. |
| **CA-2.4c** Una verificación `PENDING` admite decisión. | Router KYC, `services.py` | Prueba: decidir sobre `PENDING` es exitoso; decidir sobre una no pendiente responde 409 `VERIFICATION_NOT_PENDING`. |
| **CA-2.5a** Se registran eventos de inicio, paso y cierre. | `services.py` | Prueba: tras un flujo completo, el almacén contiene los tres tipos de evento en orden. |
| **CA-2.5b** La duración se calcula. | `services.py` | Prueba unitaria con reloj inyectado: duración = cierre − inicio (unidad en P-7). |
| **CA-2.6a** Se muestran los pasos y el paso actual. | Frontend (flujo guiado) | Prueba de componente Angular: el paso actual queda marcado. |
| **CA-2.6b** El acceso a pagos de bajo monto depende del estado de la wallet. | Frontend + estado de `GET /onboarding` | Prueba de componente: acceso habilitado o deshabilitado según cada estado. |
| **CA-2.7a** La consola ejecuta `GET /health`, `GET /scenarios` y `GET /support/cases`. | Router de servicios, frontend (consola) | Pruebas de contrato en `api/tests/test_console.py` (200) y prueba de componente por ejecución individual. |
| **CA-2.7b** Los errores se muestran legibles. | Frontend (consola) | Prueba: un `{"code","message"}` se muestra como texto, no como JSON crudo. |
| **CA-2.7c** `POST /control/reset` requiere confirmación. | Frontend (consola); API: reset del propietario | Prueba Angular: sin confirmar no se llama al API. Prueba API: tras reset, `GET /onboarding` vuelve al estado inicial. |
| **CA-2.8** Salida mensual de nuevos usuarios activos y gasto atribuido. | `services.py` (función de agregación) | Prueba unitaria con eventos fijos en dos meses: conteos y sumas esperados. Formato de salida en P-8. |
| **CA-transversal-1** Sin identidad, 401 `UNAUTHENTICATED`; la identidad no viene del cliente. | `get_current_owner` | Prueba: sin identidad responde 401; un `owner` enviado en el cuerpo se ignora o se rechaza. |
| **CA-transversal-2** Cuerpo demasiado grande, 413 `PAYLOAD_TOO_LARGE`. | `main.py`, `config.py` | Prueba: cuerpo de `MAX_BODY_BYTES + 1` responde 413 con el formato único. |
| **CA-transversal-3** Ninguna respuesta expone el identificador ni el hash del propietario. | Todos los routers, `schemas.py` | Prueba: el hash y el `owner_id` no aparecen en ningún cuerpo de respuesta. |
| **CA-transversal-4** Dos solicitudes concurrentes del mismo usuario no corrompen el estado. | `services.py` | Prueba con hilos: N envíos simultáneos dejan un JSON válido y eventos consistentes. |

---

## 5. Supuestos y preguntas pendientes

### Supuestos (decisiones conservadoras)

- **S-1.** La API es un mock de pruebas y los datos no son reales. Se infiere del prefijo `TEST-` y del nombre `MockApiService`.
- **S-2.** La identidad la resuelve una dependencia de FastAPI, `get_current_owner`, en `services.py`. El origen concreto de la credencial (cabecera o sesión) se fija al confirmar P-9. El directorio del propietario es el SHA-256 de su identificador y nunca se expone.
- **S-3.** `GET /health` devuelve 200 con un cuerpo mínimo (p. ej. `{"status":"ok"}`) a confirmar. No requiere identidad (a confirmar en P-9).
- **S-4.** Las rutas de consulta y decisión de KYC y las de onboarding de 3.2 son provisionales.
- **S-5.** `POST /control/reset` no lleva cuerpo. La confirmación es de interfaz y el reset afecta solo al propietario autenticado.
- **S-6.** Los eventos de inicio, paso y cierre se registran en el servidor, sin endpoint de escritura público.
- **S-7.** La tabla de errores y el límite de 16384 bytes son decisiones de diseño. El Issue no los fija.
- **S-8.** El estado se persiste en JSON por propietario bajo `DATA_DIR`, con las medidas de 3.5, y se asume un solo proceso.
- **S-9.** Dependencias: ningún `requirements*.txt` cambia. Si se pidiera actualizar paquetes, la regla sería `paquete==versión` exacto, también para `starlette`. Sin datos de PyPI/OSV en el contexto, no cito versiones. Se indicaría la candidata más reciente que cumpla las restricciones del Issue, marcada «candidata a confirmar con PyPI y OSV», con `pip index versions <paquete>` y `pip-audit -r api/requirements.txt` como comandos de confirmación. Para `POST` con cuerpo válido, no sé qué pruebas existentes los cubren (brecha de P-10).

### Preguntas pendientes

- **P-1.** ¿Puede aportarse el contenido de `spec.md`? Sin él no puedo cerrar la revisión de 2.1 ni confirmar los CA derivados.
- **P-2.** ¿Cuáles son las rutas del frontend Angular, su runner de pruebas y su convención de nombres?
- **P-3.** ¿Cuáles son los campos de request y response de `POST /kyc/verifications`, los nombres de los cuatro escenarios y las estructuras de `GET /scenarios` y `GET /support/cases`?
- **P-4.** ¿Se confirman o se cambian las rutas de 3.2, y cuáles son los pasos del onboarding y los estados de la wallet?
- **P-5.** ¿El estado se persiste en archivos o puede ser solo memoria?
- **P-6.** ¿Existe algún endpoint de pagos de bajo monto, qué umbral define «bajo monto» y qué estado de wallet lo habilita?
- **P-7.** ¿En qué unidad se expresa la duración y se mide solo en el servidor?
- **P-8.** ¿En qué formato y dónde se entrega la salida analítica 2.8 (archivo, endpoint o consulta)? ¿Cómo se definen «usuario activo nuevo» y «gasto atribuido», y en qué zona horaria se corta el mes?
- **P-9.** ¿De dónde sale la identidad en este entorno (cabecera, sesión, token) y `GET /health` debe ser anónimo?
- **P-10.** ¿Qué pruebas existentes cubren los `POST` con cuerpo válido? Si no existen, ¿se acepta esa brecha o se añaden pruebas nuevas en `api/tests/`?