# security_report.md

**Feature:** [H01] Pruebas del onboarding (`registro-activacion-wallet`, grupo 3 de `tasks.md`)
**Rol:** Revisor de seguridad de aplicaciones
**Fecha de redacción:** 2026-11-06

---

## 0. Estado de este informe

| Categoría | Qué significa aquí | Estado |
|---|---|---|
| **Riesgo detectado** | Lo observé leyendo el código y las especificaciones entregadas por Arquitectura, Backend, Frontend y Pruebas. | Revisión estática, sin ejecución |
| **Corrección propuesta** | Código o configuración que sugiero. | **No aplicada** y sin probar |
| **Verificación ejecutada** | Salida real de un comando, pytest, curl o pip-audit. | **Ninguna.** No tengo herramientas de ejecución en este paso y no fabrico salidas |

Todas las comprobaciones de este informe están **NO EJECUTADAS**. Son procedimientos para que una persona los corra y adjunte la salida íntegra al PR (tarea 3.12). Las frases "resultado esperado" son predicciones, no resultados.

**Límites de la revisión (información que no tuve):**
- `spec.md`, `design.md`, el `schemas.py` real y el contenido de `tools/lab.py` no están en el contexto.
- No sé si `api/app/` ya existía en el repositorio. Reviso el código que entregó Backend; si existe otro, prevalece y estos hallazgos deben recontrastarse (A-1 de Backend).
- El frontend entregó "Sin cambios" y no hay código Angular ni `*.spec.ts`. **No revisé el cliente.**
- No hay entrega de un rol de Seguridad previo en el contexto.
- No dispongo de números de línea. La ubicación se da por archivo y símbolo (función, constante o clase).

**Criterio de severidad.** Se califica suponiendo que el API es alcanzable por más de una persona (red compartida del laboratorio o un entorno desplegado). Si corre aislado en `localhost`, cada hallazgo baja aproximadamente un nivel.

**Alcance del Issue.** H01 añade pruebas y no funcionalidad, y S-7 dice que las discrepancias se reportan y no se corrigen sin decisión explícita. **Ninguna corrección de este informe debe aplicarse dentro de H01 sin esa decisión.** Varias cambian el contrato (por ejemplo, añaden `401`).

---

## 1. Resumen ejecutivo y priorización

| ID | Severidad | Hallazgo | Archivo principal |
|---|---|---|---|
| SEC-01 | **Alta** | Ningún endpoint autentica ni autoriza. Cualquiera puede aprobar una revisión KYC ajena y leer todos los casos de soporte. | `api/app/routers/kyc.py`, `support.py`, `services.py` |
| SEC-02 | **Alta** | `POST /control/reset` borra todo el estado sin credenciales y está habilitado por defecto. | `api/app/config.py`, `routers/control.py` |
| SEC-03 | Media | El cliente decide el resultado KYC (`scenario`) y la restricción `TEST-` es solo de cliente. Aceptable en un simulador, grave si se reutiliza. | `api/app/schemas.py`, `services.py` |
| SEC-04 | Media | El estado en memoria crece sin límite, no hay limitación de tasa y `decide_verification` recorre todos los casos. Hay riesgo de agotar memoria o CPU. | `api/app/services.py`, `repository.py`, `main.py` |
| SEC-05 | Baja | Los pines de dependencias no están verificados contra PyPI/OSV (A-11 de Backend). | `api/requirements*.txt` |
| SEC-06 | Baja | `/docs`, `/redoc` y `/openapi.json` quedan expuestos por defecto. El esquema OpenAPI además documenta `422` aunque el API devuelve `400`. | `api/app/main.py` |
| SEC-07 | Baja | Posible falsificación de líneas de log (log forging) con `request.url.path` en el handler 500. | `api/app/errors.py` |
| HIP-1 a HIP-3 | A verificar | Hipótesis de validación de entrada no confirmadas (sección 5). | varios |

**Orden recomendado:** SEC-01 y SEC-02 juntos (misma dependencia de operador), luego SEC-04, SEC-03 (decisión de diseño de una persona), SEC-05, y SEC-06 y SEC-07 como higiene.

---

## 2. Qué se revisó y qué no

| Área | Resultado de la revisión estática | Cobertura |
|---|---|---|
| Autenticación | No existe (S-3 de Arquitectura: el Issue no menciona identidad). Ver SEC-01. | Revisado |
| Autorización y acceso a recursos de otra persona | No hay propietario en los registros y no hay control de acceso. Ver SEC-01. | Revisado |
| Validación de entradas | Buena en `documentNumber`, `scenario`, `decision` e ids de ruta. Ver sección 4 y las hipótesis de la sección 5. | Revisado |
| Inyección | No se observa vector. No hay SQL, shell, plantillas, deserialización insegura ni acceso a archivos con rutas del usuario. | Revisado |
| Secretos | No encontré secretos en el código entregado. Los valores `SECRETO valor!` y `secreto-interno-xyz` son datos de prueba ficticios. | Revisado, por lectura |
| Datos sensibles | `documentNumber` no se persiste ni se registra. Los errores no devuelven trazas ni eco de valores. | Revisado |
| Dependencias | Pines sin verificar. Ver SEC-05. | Parcial, sin red |
| Frontend (XSS, almacenamiento de tokens, render de `message`) | **No revisado**, no hay código. Ver sección 6. | **Sin cobertura** |
| Suite de pruebas | Cubre bien la validación, pero no hay pruebas de autorización porque no existe autorización. | Revisado |

---

## 3. Controles que funcionan según el código (observado, no ejecutado)

| Control | Ubicación | Observación |
|---|---|---|
| El documento no se almacena | `repository.VerificationRecord`, `services.create_verification` | `documentNumber` se valida, pero el registro no tiene campo para guardarlo. No hay PII persistida. |
| Validación estricta de `documentNumber` | `schemas.DocumentNumber` | `strip_whitespace`, 1 a 32 caracteres y patrón ASCII `^[A-Za-z0-9-]+$`. |
| Validación de ids de ruta | `schemas.ResourceId` y `config.RESOURCE_ID_PATTERN` | Patrón ASCII acotado a 64 caracteres, evaluado antes de consultar el almacén. |
| Sin asignación masiva | `schemas.VerificationCreate` y `DecisionIn` | Solo declaran los campos esperados. Los campos extra se ignoran y no llegan a los registros. |
| Mensajes de error sin detalle interno | `errors.http_exception_handler` | Ignora `exc.detail` y usa un mensaje fijo por código. |
| 500 genérico | `errors.unhandled_exception_handler` | La traza va solo al log, nunca al cliente. |
| 422 convertido en 400 con solo nombres de campo | `errors.validation_exception_handler` | No repite los valores recibidos. |
| Límite de cuerpo antes del parseo | `middleware.BodySizeLimitMiddleware` | Comprueba `Content-Length` y cuenta bytes en chunked. |
| Ids no predecibles | `services._new_id` | `uuid4` usa `os.urandom` y aporta 64 bits tras el truncado a 16 hex. Es suficiente como identificador no adivinable, pero no sustituye una autorización. |
| Atomicidad de la decisión | `services.decide_verification` | Comprobación de `PENDING` y cambio de estado bajo el mismo `RLock`. |
| Sin escritura en disco | todo `api/app/` | No hay subidas ni rutas derivadas del usuario. |

---

## 4. Hallazgos

### SEC-01. Sin autenticación ni autorización: decisión KYC y casos de soporte accesibles a cualquiera

- **Severidad:** Alta (control de acceso roto a nivel de objeto y de función).
- **Estado:** Detectado por revisión estática. Corrección propuesta, no aplicada. Verificación no ejecutada.
- **Archivos y ubicación:**
  - `api/app/routers/kyc.py`: `decide_verification()`, `get_verification()`.
  - `api/app/routers/support.py`: `list_cases()`.
  - `api/app/routers/wallets.py`: `get_wallet()`.
  - `api/app/services.py`: `decide_verification()`, `list_support_cases()`.
  - `api/app/repository.py`: `VerificationRecord`, `WalletRecord` y `CaseRecord` no tienen campo de propietario.
- **Impacto:**
  1. Cualquier cliente sin credenciales puede **aprobar o rechazar** revisiones manuales de otras personas. Ejecuta la acción de operador "decidir KYC", que abre la wallet.
  2. `GET /support/cases` devuelve el `verificationId` de **todos** los casos. Con eso se completa la cadena de ataque sin adivinar nada: listar, decidir y abrir wallet.
  3. Quien crea una verificación en `MANUAL_REVIEW` puede aprobarla él mismo. No hay separación de funciones.
  4. Los ids de verificación y wallet, que son el único "secreto", quedan filtrados por la lista de casos. Ese control es hoy la única barrera, y se rompe.
  5. En un laboratorio aislado y de un solo usuario es comportamiento de simulador. Si el servicio es alcanzable por otras personas, es un bypass completo del flujo de aprobación.
- **Evidencia (fragmentos entregados por Backend):**
  ```python
  # routers/kyc.py
  @router.post("/{verification_id}/decision", response_model=VerificationOut, ...)
  def decide_verification(verification_id: ResourceId, payload: DecisionIn,
                          store: InMemoryStore = Depends(get_store)) -> VerificationOut:
      return services.decide_verification(store, verification_id, payload.decision)

  # routers/support.py
  @router.get("/cases", response_model=list[SupportCaseOut])
  def list_cases(store: InMemoryStore = Depends(get_store)) -> list[SupportCaseOut]:
      return services.list_support_cases(store)
  ```
  Las únicas dependencias inyectadas son `get_store`; no hay `Depends` de autenticación. `SupportCaseOut` incluye `verificationId`. Backend §6 lo declara: "no se implementa autenticación ni aislamiento".
- **Corrección propuesta (mínima, compatible con S-3).**
  Como el Issue no define identidad, propongo en dos niveles. Ambos cambian el contrato y requieren decisión de una persona.

  **Nivel 1, operador (resuelve decisión, casos y reset, ver SEC-02).** Un token de operador leído del entorno y comparado en tiempo constante. Si no está configurado, la operación queda cerrada (falla cerrado):
  ```python
  # api/app/config.py  (añadir)
  OPERATOR_TOKEN: str = os.getenv("OPERATOR_TOKEN", "")
  ```
  ```python
  # api/app/security.py  (nuevo)
  import hmac
  from typing import Optional

  from fastapi import Header

  from . import config
  from .errors import ApiError


  def require_operator(x_operator_token: Optional[str] = Header(default=None)) -> None:
      expected = config.OPERATOR_TOKEN
      supplied = x_operator_token or ""
      # Falla cerrado si no hay token configurado; compare_digest evita fugas por tiempo.
      if not expected or not hmac.compare_digest(supplied.encode(), expected.encode()):
          raise ApiError(401, "UNAUTHORIZED", "Se requiere autenticación para esta operación.")
  ```
  ```python
  # routers/kyc.py: solo en la decisión
  from fastapi import Depends
  from ..security import require_operator

  @router.post("/{verification_id}/decision", ..., dependencies=[Depends(require_operator)])
  ```
  ```python
  # routers/support.py
  router = APIRouter(prefix="/support", tags=["support"], dependencies=[Depends(require_operator)])
  ```
  `401` y su `code` `UNAUTHORIZED` ya existen en `errors.STATUS_CODES`. El token nunca se escribe en el repositorio: se define por variable de entorno.

  **Nivel 2, propiedad (si una persona decide introducir identidad).** Añadir `owner_id` a `VerificationRecord` y `WalletRecord`, tomado de una dependencia `current_user` (nunca del cuerpo ni de un parámetro del cliente). Filtrar en `get_verification` y `get_wallet` y responder `404` (no `403`) cuando el recurso exista pero sea de otra persona, para no confirmar su existencia. En tanto no exista identidad, el Nivel 1 más ids no adivinables es lo máximo que se puede exigir.

  **Efecto en la suite:** `decision`, `support/cases` y `control/reset` pasarán a requerir cabecera. El fixture `client` de `conftest.py` debería fijar `monkeypatch.setattr(config, "OPERATOR_TOKEN", "token-de-prueba-largo")` y enviar `headers={"X-Operator-Token": ...}` por defecto. Hay que añadir también las pruebas negativas de abajo. Esto no se hace en H01 sin decisión (S-7).
- **Comprobación reproducible (NO EJECUTADA).**

  *Antes de la corrección (confirma el hallazgo).* Con el API levantado (`cd api && uvicorn app.main:app`):
  ```bash
  BASE=http://127.0.0.1:8000
  # 1. Se crea una revisión manual, sin credenciales
  curl -s -X POST $BASE/kyc/verifications -H 'Content-Type: application/json' \
       -d '{"documentNumber":"TEST-0001","scenario":"MANUAL_REVIEW"}'
  # 2. Sin credenciales, se listan los casos y se toma un verificationId ajeno
  VID=$(curl -s $BASE/support/cases | python -c "import sys,json;print(json.load(sys.stdin)[0]['verificationId'])")
  # 3. Sin credenciales, se aprueba
  curl -i -X POST $BASE/kyc/verifications/$VID/decision \
       -H 'Content-Type: application/json' -d '{"decision":"APPROVED"}'
  ```
  El hallazgo queda **confirmado** si el paso 3 devuelve `200` con `walletId` no nulo.

  *Después de la corrección.* Con `OPERATOR_TOKEN=prueba-larga uvicorn app.main:app`:
  - Los pasos 2 y 3 sin cabecera deben dar `401 {"code":"UNAUTHORIZED",...}`.
  - Con `-H 'X-Operator-Token: prueba-larga'` deben dar `200`.
  - Con un token incorrecto deben dar `401`.
  - Sin `OPERATOR_TOKEN` configurado, también `401` (falla cerrado).

  *Prueba automatizada propuesta (NO EJECUTADA):*
  ```python
  # api/tests/onboarding/test_h01_autorizacion.py
  import pytest
  from app import config

  OPERADOR = [
      ("GET", "/support/cases", None),
      ("POST", "/control/reset", None),
      ("POST", "/kyc/verifications/ver_0000000000000000/decision", {"decision": "APPROVED"}),
  ]

  @pytest.mark.parametrize("metodo,ruta,cuerpo", OPERADOR)
  @pytest.mark.parametrize("cabeceras", [{}, {"X-Operator-Token": "otro"}, {"X-Operator-Token": ""}])
  def test_operador_exige_token_valido(client, monkeypatch, afirmar_error, metodo, ruta, cuerpo, cabeceras):
      monkeypatch.setattr(config, "OPERATOR_TOKEN", "token-de-prueba-largo")
      afirmar_error(client.request(metodo, ruta, json=cuerpo, headers=cabeceras), 401, "UNAUTHORIZED")

  def test_sin_token_configurado_falla_cerrado(client, monkeypatch, afirmar_error):
      monkeypatch.setattr(config, "OPERATOR_TOKEN", "")
      afirmar_error(client.get("/support/cases", headers={"X-Operator-Token": ""}), 401, "UNAUTHORIZED")

  def test_token_correcto_permite_la_operacion(client, monkeypatch):
      monkeypatch.setattr(config, "OPERATOR_TOKEN", "token-de-prueba-largo")
      r = client.get("/support/cases", headers={"X-Operator-Token": "token-de-prueba-largo"})
      assert r.status_code == 200
  ```
  Criterio de aceptación: pytest con código 0, sin `SKIPPED`, `XFAIL` ni `XPASS`.

---

### SEC-02. `POST /control/reset` sin credenciales y habilitado por defecto

- **Severidad:** Alta si el API es alcanzable por terceros. Media en un laboratorio aislado.
- **Estado:** Detectado por revisión estática. Corrección propuesta, no aplicada. Verificación no ejecutada.
- **Archivos y ubicación:**
  - `api/app/config.py`: `ENABLE_CONTROL_RESET = _bool_env("ENABLE_CONTROL_RESET", True)`.
  - `api/app/routers/control.py`: `reset()`.
  - `api/app/services.py`: `reset_state()`.
- **Impacto:** Cualquier cliente borra todas las verificaciones, wallets y casos con una sola petición. Es una destrucción de integridad y de disponibilidad. En un laboratorio compartido, una persona borra el estado de otra. Combinado con SEC-01, un atacante puede borrar pruebas de su propia decisión.
- **Evidencia:**
  ```python
  # config.py
  ENABLE_CONTROL_RESET: bool = _bool_env("ENABLE_CONTROL_RESET", True)
  # routers/control.py
  @router.post("/reset", response_model=ResetOut, responses={404: {"model": ErrorOut}})
  def reset(store: InMemoryStore = Depends(get_store)) -> ResetOut:
      services.reset_state(store)
  ```
  Backend lo reconoce en A-9: "Por defecto activo, por ser entorno de laboratorio. Su política en producción es pendiente."
- **Corrección propuesta:**
  1. Invertir el valor por defecto: `ENABLE_CONTROL_RESET = _bool_env("ENABLE_CONTROL_RESET", False)`. Los entornos de laboratorio y las pruebas lo activan explícitamente. El fixture `entorno_aislado` ya lo fija con `monkeypatch`, así que la suite no cambia.
  2. Exigir además `require_operator` (SEC-01): `router = APIRouter(prefix="/control", tags=["control"], dependencies=[Depends(require_operator)])`.
- **Comprobación reproducible (NO EJECUTADA).**
  - *Valor por defecto tras la corrección:*
    ```bash
    cd api && env -u ENABLE_CONTROL_RESET python -c "from app import config; print(config.ENABLE_CONTROL_RESET)"
    ```
    Resultado esperado: `False`.
  - *Comportamiento HTTP:*
    ```bash
    env -u ENABLE_CONTROL_RESET uvicorn app.main:app &
    curl -i -X POST http://127.0.0.1:8000/control/reset   # esperado: 404 NOT_FOUND o 401 (con token requerido)
    ```
  - *Antes de la corrección*, el mismo `curl` sin variables devolvería `200 {"status":"reset"}`, lo que confirmaría el hallazgo.
  - *Prueba pytest propuesta:* con `ENABLE_CONTROL_RESET=True` y `OPERATOR_TOKEN` fijados por `monkeypatch`, `POST /control/reset` sin cabecera debe devolver `401` y el estado debe conservarse (`GET /kyc/verifications/{id}` sigue en `200` tras el intento).

---

### SEC-03. El cliente decide el resultado KYC y la restricción `TEST-` es solo de cliente

- **Severidad:** Media. Es diseño de simulador. Pasa a Alta si el código o el patrón se reutilizan en un flujo real.
- **Estado:** Detectado por revisión estática. Es una decisión de diseño que corresponde a una persona (P-3 y P-4).
- **Archivos y ubicación:**
  - `api/app/schemas.py`: `Scenario` y `VerificationCreate.scenario`.
  - `api/app/services.py`: `create_verification()`.
  - `api/app/config.py`: `ENFORCE_TEST_DOC_PREFIX = _bool_env(..., False)`.
- **Impacto:**
  1. El resultado de la verificación (`APPROVED`, `REJECTED`, `MANUAL_REVIEW`) lo elige quien llama. En un KYC real esto equivale a "elegir tu propio veredicto". En el simulador es intencional.
  2. La regla "documento con prefijo `TEST-`" existe solo en el cliente. Quien llame directamente al API puede enviar documentos con otro formato, incluidos números reales. **Mitigación observada:** el servidor no persiste ni registra `documentNumber`, así que el riesgo de exposición de PII queda acotado.
  3. Nada impide desplegar el simulador en un entorno donde se confunda con un servicio real.
- **Evidencia:**
  ```python
  Scenario = Literal["APPROVED", "REJECTED", "MANUAL_REVIEW", "KYC_UNAVAILABLE"]
  class VerificationCreate(BaseModel):
      documentNumber: DocumentNumber
      scenario: Scenario
  # services.create_verification
  status=payload.scenario
  if config.ENFORCE_TEST_DOC_PREFIX and not payload.documentNumber.startswith("TEST-"): ...
  ```
- **Corrección propuesta (a decidir por una persona):**
  1. Marcar el servicio como simulador y negarse a arrancar en producción:
     ```python
     # config.py
     APP_ENV: str = os.getenv("APP_ENV", "lab")
     # main.py, antes de crear la app
     if config.APP_ENV == "production":
         raise RuntimeError("Este API es un simulador de laboratorio y no debe ejecutarse en producción.")
     ```
  2. Activar `ENFORCE_TEST_DOC_PREFIX=true` en los entornos compartidos. Esto contradice P-4 ("solo cliente"), por eso es una decisión humana. La suite ya fija la bandera con `monkeypatch`, así que no se rompe.
  3. Si en el futuro hay un KYC real, el resultado debe venir de un proveedor o servicio interno y `scenario` debe desaparecer del contrato público.
- **Comprobación reproducible (NO EJECUTADA).**
  ```bash
  cd api
  APP_ENV=production python -c "import app.main"; echo "exit=$?"   # esperado: RuntimeError y exit distinto de 0
  APP_ENV=lab python -c "import app.main"; echo "exit=$?"          # esperado: exit=0
  ```
  Con la restricción de prefijo activa:
  ```bash
  ENFORCE_TEST_DOC_PREFIX=true uvicorn app.main:app &
  curl -i -X POST http://127.0.0.1:8000/kyc/verifications -H 'Content-Type: application/json' \
       -d '{"documentNumber":"DOC-123","scenario":"APPROVED"}'   # esperado: 400 BAD_REQUEST
  ```
  Las pruebas `test_post_con_prefijo_obligatorio_activado_*` de `test_h01_kyc_verifications.py` ya cubren este caso, pero siguen **NO EJECUTADAS**.

---

### SEC-04. Estado en memoria sin límite y sin limitación de tasa (riesgo de agotamiento de recursos)

- **Severidad:** Media.
- **Estado:** Detectado por revisión estática. Corrección propuesta, no aplicada. Verificación no ejecutada.
- **Archivos y ubicación:**
  - `api/app/services.py`: `create_verification()` y `decide_verification()` (el bucle `for case in store.cases.values()`).
  - `api/app/repository.py`: `InMemoryStore`, diccionarios sin tope.
  - `api/app/main.py`: no hay limitador de tasa. Backend A-6 confirma que ningún endpoint genera `429`.
- **Impacto:**
  - Cada `POST /kyc/verifications` válido añade registros en memoria sin tope. El límite de 16 KB por petición no limita el *número* de peticiones, y un cliente puede agotar memoria.
  - `decide_verification` recorre todos los casos bajo el `RLock`. Con muchos casos, cada decisión retiene el lock más tiempo y degrada todas las operaciones, porque todas comparten ese lock.
  - Sin autenticación (SEC-01), no hay nadie a quien limitar por identidad.
- **Evidencia:**
  ```python
  # services.decide_verification
  for case in store.cases.values():          # O(n) bajo store.lock
      if case.verification_id == record.id:
          case.status = "CLOSED"
  # repository
  self.verifications: dict[str, VerificationRecord] = {}   # sin tope
  ```
- **Corrección propuesta:**
  1. Un tope de registros por entorno que además dé sentido al código `429` ya previsto:
     ```python
     # config.py
     MAX_STORE_RECORDS: int = _int_env("MAX_STORE_RECORDS", 10000)
     # services.create_verification, dentro de `with store.lock:` y antes de crear el registro
     if len(store.verifications) >= config.MAX_STORE_RECORDS:
         raise ApiError(429, "RATE_LIMITED",
                        "Se alcanzó el límite de registros de este entorno. Reinicie el estado o espere.")
     ```
  2. Un índice `verification_id -> case_id` para que `decide_verification` sea O(1) en lugar de recorrer los casos.
  3. Limitación de tasa por IP o por token en el proxy o gateway delante del API. No propongo una librería concreta porque no hay versiones verificadas.
- **Comprobación reproducible (NO EJECUTADA).**
  ```python
  # api/tests/onboarding/test_h01_limites.py
  from app import config

  def test_tope_de_registros_devuelve_429_y_no_crece(client, crear, store, monkeypatch, afirmar_error):
      monkeypatch.setattr(config, "MAX_STORE_RECORDS", 3)
      for _ in range(3):
          assert crear("MANUAL_REVIEW").status_code == 201
      afirmar_error(crear("MANUAL_REVIEW"), 429, "RATE_LIMITED")
      assert len(store.verifications) == 3
  ```
  Manual, para confirmar el hallazgo antes de corregir:
  ```bash
  for i in $(seq 1 20000); do
    curl -s -o /dev/null -X POST http://127.0.0.1:8000/kyc/verifications \
         -H 'Content-Type: application/json' -d '{"documentNumber":"TEST-1","scenario":"MANUAL_REVIEW"}'
  done
  ps -o rss= -p <PID_uvicorn>   # el RSS crece de forma monótona; tras la corrección debe estabilizarse
  ```
  El hallazgo se confirma si todas las peticiones devuelven `201`.

---

### SEC-05. Dependencias con versiones fijadas pero no verificadas

- **Severidad:** Baja, pendiente de verificación. No afirmo que exista ninguna vulnerabilidad.
- **Estado:** Riesgo declarado por Backend (A-11) y por Pruebas (R-7). No verificado en esta revisión.
- **Archivos y ubicación:** `api/requirements.txt` (`fastapi==0.115.6`, `starlette==0.41.3`, `pydantic==2.10.3`, `uvicorn==0.34.0`) y `api/requirements-dev.txt` (`pytest==8.3.4`, `httpx==0.28.1`).
- **Impacto:** Con la fecha actual (2026-11-06) casi seguro existen versiones posteriores. Puede haber avisos de seguridad en las fijadas. **Sin acceso a red no consulté PyPI ni OSV.** De memoria, y sin poder confirmarlo, recuerdo avisos publicados en 2025 para Starlette sobre multipart y sobre `Range`/`FileResponse`. El código entregado no usa formularios ni `StaticFiles`/`FileResponse`, así que la exposición probable es baja. Esto debe confirmarse con OSV y no lo trato como verificado.
- **Evidencia:** los pines de arriba, sin hashes ni lockfile.
- **Corrección propuesta:**
  1. Ejecutar la comprobación de abajo y adjuntar la salida.
  2. Si hay avisos aplicables, actualizar. `fastapi` acota el rango de `starlette`, así que ambos deben actualizarse juntos y con **versiones elegidas a partir de la consulta real**. No propongo números sin esos datos.
  3. Documentar una excepción con justificación para cada aviso que no aplique.
  4. Opcional: un lockfile con hashes y `pip install --require-hashes`.
- **Comprobación reproducible (NO EJECUTADA).**
  ```bash
  cd api
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements-dev.txt
  pip check
  pip install pip-audit            # herramienta externa, no está en requirements-dev.txt
  pip-audit -r requirements.txt
  pip-audit -r requirements-dev.txt
  # Alternativa por paquete (OSV):
  curl -s -X POST https://api.osv.dev/v1/query \
       -d '{"package":{"name":"starlette","ecosystem":"PyPI"},"version":"0.41.3"}'
  ```
  Repetir para `fastapi`, `pydantic`, `uvicorn`, `httpx` y `pytest`. Criterio de aceptación: `pip check` sin conflictos y `pip-audit` sin avisos, o con una excepción escrita para cada uno.

---

### SEC-06. Documentación interactiva y esquema OpenAPI expuestos por defecto

- **Severidad:** Baja.
- **Estado:** Detectado por revisión estática. Corrección propuesta, no aplicada. Verificación no ejecutada.
- **Archivo y ubicación:** `api/app/main.py`: `app = FastAPI(title="Wallet onboarding API", version="0.1.0")`.
- **Impacto:** `/docs`, `/redoc` y `/openapi.json` quedan activos por defecto y facilitan el reconocimiento de todos los endpoints, incluidos los de operador y reset. En un laboratorio aislado esto es una ventaja de desarrollo. Aparte, el esquema generado documenta `422` para validación, pero el API responde `400`. Eso es una inconsistencia de contrato, no una vulnerabilidad.
- **Evidencia:** ausencia de `docs_url=`, `redoc_url=` y `openapi_url=` en la creación de la app.
- **Corrección propuesta:**
  ```python
  # config.py
  ENABLE_DOCS: bool = _bool_env("ENABLE_DOCS", True)   # por defecto activo en laboratorio
  # main.py
  app = FastAPI(
      title="Wallet onboarding API", version="0.1.0",
      docs_url="/docs" if config.ENABLE_DOCS else None,
      redoc_url="/redoc" if config.ENABLE_DOCS else None,
      openapi_url="/openapi.json" if config.ENABLE_DOCS else None,
  )
  ```
- **Comprobación reproducible (NO EJECUTADA).**
  ```bash
  cd api
  ENABLE_DOCS=false python - <<'EOF'
  from fastapi.testclient import TestClient
  from app.main import app
  c = TestClient(app, raise_server_exceptions=False)
  for ruta in ("/docs", "/redoc", "/openapi.json"):
      print(ruta, c.get(ruta).status_code)
  EOF
  ```
  Resultado esperado: `404` para las tres rutas. Antes de la corrección devolverían `200`.

---

### SEC-07. Falsificación de líneas de log con el path de la petición

- **Severidad:** Baja.
- **Estado:** Detectado por revisión estática. Corrección propuesta, no aplicada. Verificación no ejecutada.
- **Archivo y ubicación:** `api/app/errors.py`: `unhandled_exception_handler()`.
- **Impacto:** `request.url.path` llega decodificado. Si el servidor falla con una excepción no controlada en una petición cuyo path contiene `%0A`, el log tendría una línea falsa inyectada (log forging). Solo ocurre al fallar una ruta con path libre, y hoy las rutas con parámetros validan el id antes de ejecutar lógica, así que la probabilidad es baja.
- **Evidencia:**
  ```python
  logger.error("Error no controlado en %s %s", request.method, request.url.path, exc_info=exc)
  ```
- **Corrección propuesta:** usar `%r` para que los saltos de línea queden escapados:
  ```python
  logger.error("Error no controlado en %s %r", request.method, request.url.path, exc_info=exc)
  ```
- **Comprobación reproducible (NO EJECUTADA).** Ampliar la app aislada de `test_h01_error_handler.py` con una ruta `/explotar/{valor}` que lance `RuntimeError`, y añadir:
  ```python
  def test_log_500_escapa_saltos_de_linea(cliente_aislado, caplog):
      with caplog.at_level("ERROR", logger="app.errors"):
          r = cliente_aislado.get("/explotar/a%0AFALSO")
      assert r.status_code == 500
      mensaje = caplog.records[0].getMessage()
      assert "\n" not in mensaje
  ```
  Antes de la corrección esta prueba debería fallar, y eso confirmaría el hallazgo.

---

## 5. Hipótesis no confirmadas (sin hallazgo hasta verificar)

Son sospechas razonables que no puedo afirmar sin ejecutar. Si alguna se confirma, pasa a hallazgo.

| ID | Hipótesis | Comprobación (NO EJECUTADA) | Resultado que confirmaría un problema |
|---|---|---|---|
| HIP-1 | El patrón `^[A-Za-z0-9_-]{1,64}$` podría aceptar un `\n` final si el motor de regex tratara `$` a la manera de Python `re`. Con el motor por defecto de Pydantic v2 (Rust) no debería ocurrir, pero no lo he confirmado. | `curl -i http://127.0.0.1:8000/wallets/wlt_ffffffffffffffff%0A` | Si responde `404` en lugar de `400`, el patrón tolera el salto final. |
| HIP-2 | El middleware toma solo la primera cabecera `Content-Length`. Si llegaran dos con valores distintos, el comportamiento depende del servidor (uvicorn/h11). | `printf 'POST /kyc/verifications HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\nContent-Length: 5\r\nContent-Length: 99999\r\n\r\n{}' \| nc 127.0.0.1 8000` | Un `201`, un `500` o una conexión colgada. Lo esperado es un rechazo `400` del servidor. |
| HIP-3 | Un `Content-Length` menor que el cuerpo real podría dejar bytes sin procesar. | Enviar un cuerpo de 200 bytes con `Content-Length: 20` usando `nc`. | Respuesta `2xx` con el cuerpo truncado, o un `500`. |

---

## 6. Frontend: sin cobertura

El Desarrollador frontend entregó "Sin cambios" y no hay código Angular en el contexto, así que no puedo revisar el cliente. Los siguientes puntos **quedan sin revisar**:

- Cómo se muestra el `message` del servidor. Angular escapa la interpolación por defecto, pero un `[innerHTML]` o un `bypassSecurityTrust*` lo anularían.
- Dónde se guardan tokens o estado, si existen.
- Las validaciones de cliente (latencia, `TEST-`, datos faltantes) son solo de experiencia de usuario. **No son un control de seguridad.** El servidor valida todo salvo `TEST-` (SEC-03).

Cuando exista el código del cliente, una persona debe ejecutar y adjuntar:
```bash
grep -rnE "innerHTML|bypassSecurityTrust|localStorage|sessionStorage|eval\(|document\.write" src/
```
Cualquier coincidencia debe revisarse caso por caso. También debe quedar evidencia de `ng test --watch=false`.

Existe además una comprobación de secretos por lectura. Debe repetirse sobre el repositorio real:
```bash
grep -rnEi "(secret|password|passwd|token|api[_-]?key|BEGIN (RSA|PRIVATE))" api/ --include=*.py --include=*.txt --include=*.env* --include=*.toml --include=*.yml
```
Resultado esperado: solo datos ficticios de prueba (`secreto-interno-xyz`, `SECRETO valor!`) y, si se aplica SEC-01, el nombre de variable `OPERATOR_TOKEN` sin valor.

---

## 7. Verificaciones: lo ejecutado y lo pendiente

### 7.1 Verificaciones realmente ejecutadas por mí

**Ninguna.** No ejecuté pytest, uvicorn, curl, pip, pip-audit ni OSV. Lo anterior sale de la lectura de los textos entregados.

### 7.2 Estado de las verificaciones de la suite del Ingeniero de pruebas

Todas las filas de su `testing_report.md` están en `NO EJECUTADO`. No puedo afirmar que pasen, ni cobertura, ni número de pruebas. Las medidas de endurecimiento que esa suite verificaría, si se ejecuta con éxito, son:

| Control | Archivo de prueba | Estado |
|---|---|---|
| Ids inválidos dan 400 sin eco | `test_h01_endurecimiento.py` | NO EJECUTADO |
| Documentos peligrosos rechazados y no reflejados | `test_h01_endurecimiento.py` | NO EJECUTADO |
| Mensajes sin trazas y 500 genérico | `test_h01_error_handler.py` | NO EJECUTADO |
| Límite de cuerpo (413, chunked, `Content-Length` inválido) | `test_h01_kyc_verifications.py` | NO EJECUTADO |
| Reset desactivable | `test_h01_control_reset.py` | NO EJECUTADO |
| Atomicidad de la decisión concurrente | `test_h01_kyc_decision.py` | NO EJECUTADO |

**Brecha de cobertura de seguridad:** no hay pruebas de autorización (nadie debería poder decidir ni listar casos sin credenciales). No existen porque la funcionalidad no existe, y se proponen en SEC-01 y SEC-02.

### 7.3 Verificaciones propuestas en este informe (todas NO EJECUTADAS)

| ID | Qué comprueba | Cómo |
|---|---|---|
| SEC-01 | Decisión y casos sin credenciales; luego `401` con la corrección | Secuencia `curl` y `test_h01_autorizacion.py` |
| SEC-02 | Valor por defecto del reset y respuesta HTTP | `python -c` con `env -u`, y `curl` |
| SEC-03 | Arranque en producción rechazado y prefijo `TEST-` en servidor | `APP_ENV=production python -c "import app.main"` y `curl` |
| SEC-04 | Tope de registros y crecimiento de memoria | `test_h01_limites.py` y bucle `curl` con `ps` |
| SEC-05 | Vulnerabilidades de dependencias | `pip check`, `pip-audit`, OSV |
| SEC-06 | Documentación desactivable | `ENABLE_DOCS=false` y `TestClient` |
| SEC-07 | Log sin saltos de línea | prueba con `caplog` |
| HIP-1 a HIP-3 | Hipótesis de la sección 5 | `curl` y `nc` |

### 7.4 Qué debe adjuntar la persona al PR (tarea 3.12)

La persona pega la salida íntegra, sin editar ni resumir:
```text
Fecha/hora de ejecución: <completar>
Commit: <git rev-parse HEAD>
Python: <python --version>
pip freeze (fastapi|starlette|pydantic|uvicorn|httpx|pytest): <salida>
Comando: python tools/lab.py test api                              -> salida íntegra
Comando: cd api && python -m pytest tests -v -rA --strict-markers -> salida íntegra
grep SKIPPED/XFAIL/XPASS: <vacío | contenido>   # un skip cuenta como NO cumplido
pip check / pip-audit / OSV (SEC-05): <salida íntegra>
Secuencia curl de SEC-01 (antes y después, si se corrige): <salida íntegra>
Comprobaciones HIP-1 a HIP-3: <salida íntegra>
Ejecución de cliente (ng test --watch=false): <NO EJECUTADO | salida íntegra>
Hallazgos confirmados / descartados / pendientes de decisión: <completar>
```

---

## 8. Decisiones y preguntas abiertas para una persona

| # | Pregunta | Relación |
|---|---|---|
| D-1 | ¿Se acepta introducir un token de operador (SEC-01 Nivel 1) o se deja como riesgo aceptado en laboratorio aislado? Ambas opciones deben quedar escritas. | SEC-01, SEC-02 |
| D-2 | ¿El API será alcanzable por más de una persona o desde fuera de `localhost`? Esto fija la severidad real de SEC-01 y SEC-02. | SEC-01, SEC-02 |
| D-3 | ¿Se introduce identidad de usuario? Si sí, se aplica el Nivel 2 de SEC-01 con `owner_id` tomado de una dependencia. | SEC-01 |
| D-4 | ¿Se acepta el reset desactivado por defecto y el bloqueo de arranque en producción? | SEC-02, SEC-03 |
| D-5 | ¿El prefijo `TEST-` debe exigirse también en el servidor? (P-4 dice solo cliente.) | SEC-03 |
| D-6 | ¿Se implementa limitación de tasa en el API o en el gateway? Hoy ningún endpoint produce `429` (A-6). | SEC-04 |
| D-7 | ¿Dónde está el código real del cliente? Se necesita para revisar XSS y almacenamiento de datos. | sección 6 |
| D-8 | ¿Existe ya `api/app/` en el repositorio? Si es así, los hallazgos deben recontrastarse con ese código. | todos |

---

## 9. Conclusión

La implementación entregada valida bien la entrada, no persiste el documento y no filtra detalles internos en los errores. **No se observa ningún vector de inyección.** El riesgo principal es de control de acceso: ningún endpoint autentica, cualquiera puede aprobar revisiones KYC y borrar el estado (SEC-01, SEC-02). Esto puede ser aceptable en un simulador local de un solo usuario, pero no si el API es alcanzable por otras personas. Ninguna corrección está aplicada y ninguna comprobación se ha ejecutado. Hasta que una persona decida (D-1 a D-8) y ejecute las comprobaciones de la sección 7, el estado de estos hallazgos es **detectado y sin verificar**.