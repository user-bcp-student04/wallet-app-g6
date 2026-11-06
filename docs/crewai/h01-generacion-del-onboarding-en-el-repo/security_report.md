# security_report.md

**Feature:** [H01] Generación del onboarding en el repo destino (tareas 2.2 a 2.8)
**Fecha:** 2026-11-06
**Rol:** Revisor de seguridad de aplicaciones

---

## 0. Estado de verificación (leer primero)

> **No se ejecutó nada.** Esta revisión es **estática**: leí el código entregado en `backend_spec.md`, `frontend_spec.md` y `testing_report.md`. No corrí `pytest`, `ng test`, `curl`, `uvicorn`, `pip check` ni `pip-audit`. Tampoco tengo el árbol real del repositorio, ni `spec.md` (P-1), ni la parte final del spec de pruebas del frontend, que llegó truncada.
>
> Por eso este informe separa tres categorías, y ninguna cuenta como ejecutada:
>
> | Categoría | Significado en este informe |
> |---|---|
> | **Detectado** | Riesgo visto al leer el código, con la evidencia citada. No se reprodujo en ejecución. |
> | **Propuesto** | Corrección o prueba que escribo aquí. No está aplicada ni compilada. |
> | **Verificado (ejecutado)** | **Ninguno.** Los resultados marcados «esperado» no son resultados. |
>
> Las ubicaciones se dan como **archivo + símbolo**, sin números de línea, porque trabajé con el texto entregado y no con el árbol.
> Las tareas 2.2 a 2.8 siguen sin marcar y este informe no cambia su estado.

**Escala de severidad:**

| Nivel | Criterio |
|---|---|
| Alta | Acceso o modificación de datos de otra persona sin barrera efectiva. |
| Media | Elusión de un control de negocio, o agotamiento de recursos sin autenticación fuerte. |
| Baja | Endurecimiento, o riesgo que requiere condiciones adicionales. |
| Info | Observación sin acción obligatoria. |

---

## 1. Resumen priorizado

| ID | Sev. | Hallazgo | Archivo principal | Estado |
|---|---|---|---|---|
| SEC-01 | **Alta** | La identidad es una cabecera sin secreto: cualquiera suplanta a cualquier propietario | `api/app/services.py` (`get_current_owner`) | Detectado, corrección propuesta, no verificado |
| SEC-02 | **Media** (Alta si el código sale del modo mock) | El usuario elige su propio resultado KYC, se autoaprueba y puede reiniciar su estado | `api/app/routers/kyc.py`, `console.py` | Detectado, corrección propuesta, no verificado |
| SEC-03 | **Media** | Creación ilimitada de propietarios y estado en disco, sin límite global ni rate limit | `api/app/storage.py`, `middleware.py` | Detectado, corrección propuesta, no verificado |
| SEC-04 | **Media** | Dependencias sin verificar contra PyPI/OSV y dependencias transitivas sin fijar | `api/requirements.txt` | Detectado, comprobación propuesta, no ejecutada |
| SEC-05 | Baja | Ruta de la solicitud (controlada por el cliente) en el log sin neutralizar | `api/app/errors.py` (`_unhandled_handler`) | Detectado, no verificado |
| SEC-06 | Baja | Documentación OpenAPI (`/docs`, `/openapi.json`) expuesta por defecto | `api/app/main.py` | Detectado, no verificado |
| SEC-07 | Baja | Exclusión mutua solo dentro del proceso: con varios workers se pierden actualizaciones y se salta el límite | `api/app/storage.py` (`OwnerStore`) | Detectado (ya declarado como S-8), no verificado |
| SEC-08 | Baja | `DATA_DIR` relativo, permisos solo en el directorio hoja y riesgo de versionar datos | `api/app/config.py`, `storage.py` | Detectado, no verificado |
| SEC-09 | Baja | Estado persistido validado solo por claves, y analítica sin tolerancia a datos mal formados | `api/app/storage.py` (`_parse_state`), `services.py` (`monthly_analytics`) | Detectado, no verificado |
| SEC-10 | Info/Baja | Respuestas con datos del usuario sin `Cache-Control: no-store` ni `X-Content-Type-Options` | `api/app/main.py` | Detectado, no verificado |

---

## 2. Hallazgos detallados

### SEC-01. Identidad sin secreto: suplantación de cualquier propietario (Alta)

**Archivo y ubicación**
- `api/app/services.py`, función `get_current_owner`.
- `api/app/config.py`, constantes `OWNER_HEADER` y `OWNER_ID_PATTERN`.
- `src/app/identificar/identificar.component.ts` (formulario libre).
- `src/app/core/session.service.ts` (guarda el identificador en `sessionStorage`).
- `src/app/core/mock-api.service.ts` (`options()` lo envía como `X-Owner-Id`).

**Evidencia (código entregado)**
```python
def get_current_owner(x_owner_id: Optional[str] = Header(default=None, alias=config.OWNER_HEADER)) -> str:
    if x_owner_id is None or _OWNER_RE.fullmatch(x_owner_id) is None:
        raise ApiError(401, "UNAUTHENTICATED", ...)
    return x_owner_id
```
La dependencia solo comprueba el **formato** de la cabecera (`[A-Za-z0-9._-]{1,128}`). No hay secreto, firma ni sesión emitida por el servidor.

El aislamiento entre propietarios (`test_aislamiento_entre_propietarios_en_kyc`, `test_owner_en_cuerpo_se_rechaza`) solo demuestra que dos cabeceras distintas dan estados distintos. **No demuestra que quien envía una cabecera sea su dueño.** El resto de las pruebas de seguridad del informe de Pruebas comprueban formato y ausencia, no autenticidad.

El directorio de datos es `sha256(owner_id)`, que cualquiera puede calcular a partir del identificador. El hash protege la ruta del sistema de archivos pero no sirve como control de acceso.

**Impacto**
- Quien conozca o adivine un identificador (`demo-user-1`, `usuario-1`, correos, DNI, etc.) puede:
  - leer su estado de wallet y sus casos de soporte;
  - consultar y decidir sus verificaciones KYC;
  - avanzar sus pasos;
  - borrar todo su progreso con `POST /control/reset`.
- Esto es acceso a recursos de otra persona (CWE-287, CWE-639).
- El frontend lo facilita: el formulario «Identifícate» acepta cualquier cadena y el guardia `ownerGuard` solo comprueba presencia.
- Aunque sea un mock, el patrón se copia: la spec lo llama «credencial de mock» (B-3, P-9) sin condicionarlo a un entorno.
- Si el valor se usara como identificador real, un XSS lo leería de `sessionStorage`.

**Corrección propuesta (no aplicada)**

Idea: el servidor **emite** un token firmado por sesión y deriva de él un `owner_id` aleatorio e inimitable. El cliente no elige quién es.

```python
# api/app/config.py  (añadir)
def session_secret() -> bytes:
    secret = os.environ.get("SESSION_SECRET", "").encode("utf-8")
    if len(secret) < 32:
        raise RuntimeError("SESSION_SECRET debe tener al menos 32 bytes y venir del entorno.")
    return secret
```

```python
# api/app/services.py  (sustituir get_current_owner)
import hashlib, hmac, secrets

_TOKEN_RE = re.compile(r"[0-9a-f]{32}\.[0-9a-f]{64}")

def _sign(owner_id: str) -> str:
    return hmac.new(config.session_secret(), owner_id.encode("utf-8"), hashlib.sha256).hexdigest()

def issue_session_token() -> str:
    owner_id = secrets.token_hex(16)          # 128 bits, no elegible por el cliente
    return f"{owner_id}.{_sign(owner_id)}"

def get_current_owner(authorization: Optional[str] = Header(default=None)) -> str:
    unauth = ApiError(401, "UNAUTHENTICATED", "No se pudo identificar al usuario.")
    if authorization is None or not authorization.startswith("Bearer "):
        raise unauth
    token = authorization[len("Bearer "):]
    if _TOKEN_RE.fullmatch(token) is None:
        raise unauth
    owner_id, _, signature = token.partition(".")
    if not hmac.compare_digest(signature, _sign(owner_id)):
        raise unauth
    return owner_id
```

```python
# api/app/routers/console.py  (añadir; sin identidad, no escribe en disco)
@router.post("/session", response_model=SessionResponse)
def create_session() -> SessionResponse:
    return SessionResponse(token=issue_session_token())
```
Con `class SessionResponse(BaseModel): token: str` en `schemas.py`.

`create_app()` debe llamar a `config.session_secret()` para fallar al arrancar si falta el secreto.

Frontend:
- `api.models.ts`: añadir `SessionResponse { token: string }`.
- `MockApiService`: añadir `createSession()` y enviar `Authorization: Bearer <token>` en lugar de `X-Owner-Id`.
- `IdentificarComponent`: sustituir el campo libre por un botón «Iniciar sesión de pruebas» que llama a `createSession()`.
- `SessionService`: guardar el token. `sessionStorage` solo es aceptable en modo mock. Con credenciales reales, usar cookie `HttpOnly; Secure; SameSite`.
- `app.component.html`: no mostrar el identificador.

Restos que quedan, para decidir:
- Sin expiración ni revocación. Añadir `iat` firmado y TTL.
- `SESSION_SECRET` solo por entorno: nunca en el repositorio, en `.env` versionado ni en logs.
- Este cambio **modifica el contrato** de S-2/P-9 (cabecera y rutas). Hay que confirmarlo con Producto y actualizar `user_story.md`, `conftest.py` (el helper `Api.headers`) y las pruebas.

**Comprobación reproducible (NO EJECUTADA)**

Antes de corregir, la prueba de concepto (esperado: el atacante **tiene éxito**):
```bash
cd api && DATA_DIR="$(mktemp -d)" uvicorn app.main:app --port 8000 &
B=http://127.0.0.1:8000
# "Víctima" crea progreso
curl -s -H 'X-Owner-Id: usuario-1' -H 'Content-Type: application/json' \
  -d '{"document_number":"TEST-0001"}' $B/onboarding/steps/registro
# "Atacante" (otro cliente, sin ningún secreto) usa el mismo identificador
curl -s -H 'X-Owner-Id: usuario-1' $B/onboarding        # esperado hoy: 200 con el estado de la víctima
curl -s -X POST -H 'X-Owner-Id: usuario-1' $B/control/reset   # esperado hoy: 200 {"status":"reset"}
```

Después de corregir, pruebas pytest propuestas (archivo nuevo `api/tests/h01/test_h01_auth_token.py`; requiere `SESSION_SECRET` de ≥32 bytes vía `monkeypatch.setenv` en un fixture autouse):
```python
def test_x_owner_id_ya_no_autentica(client):
    r = client.get("/onboarding", headers={"X-Owner-Id": "usuario-1"})
    assert r.status_code == 401 and r.json()["code"] == "UNAUTHENTICATED"

def test_token_falsificado_o_alterado_se_rechaza(client):
    tok = client.post("/session").json()["token"]
    owner, _, sig = tok.partition(".")
    for malo in (f"{owner}.{'0'*64}", f"{'a'*32}.{sig}", owner, ""):
        r = client.get("/onboarding", headers={"Authorization": f"Bearer {malo}"})
        assert r.status_code == 401

def test_sesiones_aisladas(client):
    a = client.post("/session").json()["token"]
    b = client.post("/session").json()["token"]
    ha, hb = {"Authorization": f"Bearer {a}"}, {"Authorization": f"Bearer {b}"}
    assert client.post("/onboarding/steps/registro", headers=ha, json={"document_number": "TEST-0001"}).status_code == 200
    assert client.get("/onboarding", headers=hb).json()["wallet_status"] == "NOT_STARTED"

def test_la_sesion_no_escribe_en_disco(client, data_dir):
    assert client.post("/session").status_code == 200
    assert not data_dir.exists()
```
Resultado esperado (no ejecutado): las 4 pruebas pasan, y la PoC de arriba devuelve 401.

---

### SEC-02. El propio usuario decide el resultado de su KYC (Media; Alta si el código sale del mock)

**Archivo y ubicación**
- `api/app/routers/kyc.py`:
  - `create_verification` acepta `scenario` del cliente.
  - `decide_verification` (`POST /kyc/verifications/{id}/decision`) lo puede llamar el mismo usuario.
- `api/app/routers/console.py`: `POST /control/reset`.
- `api/app/services.py`: `create_verification`, `decide_verification`, `_assert_not_blocked`, `_wallet_status`.

**Evidencia**
- Con `{"scenario":"APPROVED"}` el servicio crea la verificación ya `APPROVED`, con `decided_at` inmediato.
- Con `PENDING`, el mismo usuario llama a `/decision` con `APPROVED`.
- `_assert_not_blocked` confía en el estado de la última verificación, y `low_amount_payments_enabled == (wallet_status == ACTIVE)` depende de ese estado.
- Ningún rol distingue al solicitante del decisor.
- `POST /control/reset` borra `events` y `closed_at`, lo que permite eliminar el rastro que alimenta la analítica 2.8.

**Impacto**
- En el mock es el comportamiento buscado (escenarios simulados).
- Si este código se reutiliza fuera de un entorno de pruebas, **cualquier usuario evita la verificación de identidad** y habilita el acceso a pagos de bajo monto (autorización rota, CWE-285).
- Nada en el código ni en la spec fuerza que esto solo exista en el mock: no hay ninguna bandera de entorno.

**Corrección propuesta (no aplicada)**

Los controles mock solo se exponen con una bandera explícita, y por defecto están apagados:
```python
# api/app/config.py
ENABLE_MOCK_CONTROLS: bool = os.environ.get("ENABLE_MOCK_CONTROLS", "0") == "1"
```
```python
# api/app/services.py
def require_mock_controls() -> None:
    if not config.ENABLE_MOCK_CONTROLS:
        raise ApiError(404, "NOT_FOUND", "El recurso solicitado no existe.")
```
```python
# api/app/routers/kyc.py
router = APIRouter(prefix="/kyc", tags=["kyc"], dependencies=[Depends(require_mock_controls)])
# api/app/routers/console.py: añadir dependencies=[Depends(require_mock_controls)] a /control/reset
```
- En un entorno no mock, la decisión debe exigir un **rol distinto** (soporte). Esto requiere un modelo de roles que hoy no existe (P-9).
- Fijar `ENABLE_MOCK_CONTROLS=1` solo en dev y test, y que `conftest.py` use `monkeypatch.setattr(config, "ENABLE_MOCK_CONTROLS", True)`.
- Documentar en el README que el servicio es un mock.

**Comprobación reproducible (NO EJECUTADA)**
```python
def test_controles_mock_apagados_por_defecto(client, monkeypatch):
    from app import config
    monkeypatch.setattr(config, "ENABLE_MOCK_CONTROLS", False)
    h = <cabecera de sesión válida>
    assert client.post("/kyc/verifications", headers=h, json={"document_number": "TEST-0001", "scenario": "APPROVED"}).status_code == 404
    assert client.post("/kyc/verifications/x/decision", headers=h, json={"decision": "APPROVED"}).status_code == 404
    assert client.post("/control/reset", headers=h).status_code == 404
```
Esperado (no ejecutado): 404 `NOT_FOUND` en los tres. Con la bandera en `True`, las pruebas actuales de `test_h01_kyc.py` y `test_h01_console.py` siguen aplicando sin cambios.

---

### SEC-03. Propietarios y estado en disco sin límite global ni rate limit (Media)

**Archivo y ubicación**
- `api/app/storage.py`: `OwnerStore.write` (`mkdir` y `mkstemp` para cada propietario nuevo).
- `api/app/middleware.py`: solo limita el tamaño del cuerpo.
- `api/app/config.py`: solo existe `MAX_VERIFICATIONS_PER_OWNER`.

**Evidencia**
- El límite de 50 verificaciones es por propietario, y el número de propietarios no está acotado.
- Con SEC-01, cada cabecera nueva crea un directorio y un `state.json`.
- Cada escritura hace `fsync` bajo uno de solo 64 locks, así que un volumen alto de escrituras degrada a los demás propietarios de esa franja.
- No hay rate limiting en ningún archivo entregado.

**Impacto**
- Un cliente anónimo puede agotar disco o inodos y degradar la latencia (CWE-770).
- `iter_states` (analítica 2.8) recorre todos los directorios, así que crece con ellos.

**Corrección propuesta (no aplicada)**
- Límite global: `MAX_OWNERS` (por ejemplo 1000, ajustable). Al crear un directorio nuevo, comprobar el tope y responder 503 `CAPACITY_REACHED`. Código y mensaje son decisión de diseño que hay que añadir al contrato de errores.
  ```python
  if not directory.exists() and sum(1 for _ in os.scandir(self._root)) >= config.MAX_OWNERS:
      raise OwnerLimitError()   # servicio → ApiError(503, "CAPACITY_REACHED", ...)
  ```
  El conteo es aproximado con locks por franja y está acotado a efectos prácticos. Si hace falta exactitud, usar un contador con un lock global.
- Rate limiting por IP y por token en el proxy inverso (por ejemplo `limit_req` de nginx) o con una librería. La elección y los umbrales dependen del despliegue, que desconozco.
- La corrección de SEC-01 reduce el abuso (un token emitido por el servidor en lugar de cualquier cadena), pero `POST /session` sigue siendo anónimo, por lo que el límite de propietarios hace falta igualmente.

**Comprobación reproducible (NO EJECUTADA)**

Antes de corregir, para medir el efecto (esperado: se crean todos):
```bash
export DATA_DIR="$(mktemp -d)"; (cd api && uvicorn app.main:app --port 8000 &) ; sleep 2
for i in $(seq 1 500); do
  curl -s -o /dev/null -H "X-Owner-Id: dos-$i" -H 'Content-Type: application/json' \
    -d '{"document_number":"TEST-0001"}' http://127.0.0.1:8000/onboarding/steps/registro
done
ls "$DATA_DIR" | wc -l      # esperado hoy: 500
```
Después de corregir (prueba propuesta):
```python
def test_limite_global_de_propietarios(monkeypatch, api):
    from app import config
    monkeypatch.setattr(config, "MAX_OWNERS", 3)
    for i in range(3):
        assert api.post("/onboarding/steps/registro", owner=f"o-{i}", json={"document_number": "TEST-0001"}).status_code == 200
    r = api.post("/onboarding/steps/registro", owner="o-3", json={"document_number": "TEST-0001"})
    assert r.status_code == 503 and r.json()["code"] == "CAPACITY_REACHED"
    # propietario existente sigue operando
    assert api.get("/onboarding", owner="o-0").status_code == 200
```

---

### SEC-04. Dependencias sin verificar y transitivas sin fijar (Media)

**Archivo y ubicación:** `api/requirements.txt`.
```text
fastapi==0.115.6
starlette==0.41.3
uvicorn==0.34.0
pydantic==2.10.4
```

**Evidencia**
- El propio Backend declara que los pines **no están verificados** contra PyPI ni OSV (§9 de `backend_spec.md`).
- Las dependencias transitivas (`anyio`, `pydantic-core`, `typing-extensions`, `h11`, `click`, etc.) no están fijadas, así que la instalación no es reproducible.
- No hay verificación de hashes.
- Tampoco se ha ejecutado `pip-audit`.

**Impacto**
- Es posible que existan avisos publicados para estas versiones (Starlette los ha tenido en el manejo de formularios multipart y de rangos en archivos estáticos). **Lo menciono de memoria y no lo he verificado.**
- La aplicación no usa formularios ni `StaticFiles`/`FileResponse`, así que la exposición probable es baja, pero eso debe confirmarse con la salida real de `pip-audit`.
- No puedo indicar versiones corregidas: sin datos de PyPI/OSV en el contexto, cualquier cifra sería inventada.

**Corrección propuesta (no aplicada)**
1. Ejecutar la comprobación de abajo y adjuntar la salida.
2. Si hay avisos, actualizar con `paquete==versión` **exacto** (también `starlette`). Cada versión candidata debe confirmarse con `pip index versions` y `pip-audit` antes de aceptarla, y fastapi y starlette deben ser compatibles entre sí.
3. Fijar también las transitivas: `pip-compile --generate-hashes` (pip-tools) o `pip freeze` en un archivo de bloqueo, e instalar con `--require-hashes`.
4. Ejecutar `pip-audit` en CI.

**Comprobación reproducible (NO EJECUTADA, requiere red)**
```bash
cd api && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip check
pip freeze > ../evidencia/sec_freeze.txt        # estado real de transitivas
pip install pip-audit && pip-audit -r requirements.txt | tee ../evidencia/sec_pipaudit.txt
pip index versions starlette                    # repetir para fastapi, uvicorn, pydantic
```
Criterio de aceptación: `pip check` limpio, `pip-audit` sin hallazgos o con hallazgos documentados con justificación, y `test_h01_requirements.py` sigue pasando.

---

### SEC-05. Ruta de solicitud sin neutralizar en el log (Baja)

**Archivo y ubicación:** `api/app/errors.py`, `_unhandled_handler`.
```python
logger.exception("Error no controlado en %s %s", request.method, request.url.path)
```

**Evidencia:** `request.url.path` proviene del cliente. Según la versión de Starlette, puede contener caracteres decodificados, incluidos saltos de línea (`%0a`). No lo he comprobado en ejecución.

**Impacto:** inyección de líneas falsas en el log del servidor (CWE-117). Solo se activa cuando hay un 500, y su efecto es bajo.

**Corrección propuesta:** usar `%r`, que escapa los caracteres de control:
```python
logger.exception("Error no controlado en %s %r", request.method, request.url.path)
```

**Comprobación reproducible (NO EJECUTADA)**
```python
def test_log_de_500_escapa_saltos_de_linea(client, caplog):
    client.app.add_api_route("/__boom/{x}", lambda x: 1 / 0, methods=["GET"])
    client.get("/__boom/a%0aFALSO%20ERROR%20linea")
    assert "\nFALSO" not in caplog.text
```
Esperado tras corregir: la prueba pasa. Antes de corregir, ejecutarla una vez para saber si el riesgo realmente existe en la versión instalada.

---

### SEC-06. Documentación de la API expuesta por defecto (Baja)

**Archivo y ubicación:** `api/app/main.py`, `FastAPI(title=..., version=...)`.

**Evidencia:** FastAPI publica `/docs`, `/redoc` y `/openapi.json` salvo que se desactiven. Además, `test_openapi_expone_las_rutas_del_contrato` de la línea base depende de `/openapi.json`.

**Impacto:** facilita la enumeración del contrato (CWE-200). Es información que el frontend ya conoce, por lo que el riesgo es bajo, pero es innecesaria en producción.

**Corrección propuesta**
```python
# config.py
ENABLE_DOCS: bool = os.environ.get("ENABLE_DOCS", "0") == "1"
# main.py
kwargs = {} if config.ENABLE_DOCS else {"docs_url": None, "redoc_url": None, "openapi_url": None}
application = FastAPI(title="Wallet Onboarding Mock API", version="0.1.0", **kwargs)
```
Ajustar la prueba de línea base para activar `ENABLE_DOCS` en su fixture.

**Comprobación reproducible (NO EJECUTADA):** con `ENABLE_DOCS` sin definir, `curl -s -o /dev/null -w '%{http_code}' $B/openapi.json` y `$B/docs` deben dar 404.

---

### SEC-07. Exclusión mutua solo dentro del proceso (Baja)

**Archivo y ubicación:** `api/app/storage.py`, `OwnerStore.locked` (usa `threading.Lock`).

**Evidencia:** Backend declara el supuesto de un solo proceso (S-8, B-7). Nada en el código lo hace cumplir.

**Impacto:** con `uvicorn --workers N` o varias réplicas, dos procesos pueden hacer el ciclo leer → modificar → escribir sobre el mismo `state.json`:
- se pierden actualizaciones;
- se duplican eventos;
- se puede superar `MAX_VERIFICATIONS_PER_OWNER`.

La escritura atómica evita archivos corruptos, pero no actualizaciones perdidas. Es un riesgo de integridad.

**Corrección propuesta (POSIX)**
- Opción mínima: documentar y verificar al arrancar que `WEB_CONCURRENCY` sea 1 o no esté definido.
- Opción robusta: bloqueo de archivo además del lock de hilos.
  ```python
  import fcntl
  @contextmanager
  def locked(self, owner_id):
      with self._locks[index]:
          d = self._owner_dir(owner_id); d.mkdir(mode=0o700, parents=True, exist_ok=True)
          with open(d / ".lock", "a") as fh:
              fcntl.flock(fh, fcntl.LOCK_EX)
              try: yield
              finally: fcntl.flock(fh, fcntl.LOCK_UN)
  ```
  Esto crea el directorio incluso en lecturas, lo que interactúa con SEC-03 y con las pruebas que afirman que leer no escribe. Hay que ajustarlas antes de adoptarlo.

**Comprobación reproducible (NO EJECUTADA):** prueba con `multiprocessing` (4 procesos × 10 creaciones sobre el mismo propietario y el mismo `DATA_DIR`). Esperado tras corregir: exactamente 40 verificaciones o 409 `LIMIT_REACHED`, sin pérdidas. Antes de corregir se espera que a veces haya menos de 40. La prueba no es determinista y debe repetirse varias veces.

---

### SEC-08. `DATA_DIR` relativo y permisos parciales (Baja)

**Archivo y ubicación:** `api/app/config.py` (`DATA_DIR`, por defecto `data`), `storage.py` (`mkdir(mode=0o700, parents=True, ...)`).

**Evidencia**
- La ruta por defecto es relativa al directorio de trabajo, por lo que puede acabar dentro del árbol del repositorio.
- `Path.mkdir(mode=0o700, parents=True)` aplica el modo solo al directorio hoja. Los intermedios, incluido `DATA_DIR`, se crean con permisos por defecto.
- El `state.json` queda en `0600` gracias a `mkstemp`, así que el archivo está protegido.
- El `.gitignore` está solo recomendado (B-7), no entregado.

**Impacto:** riesgo bajo de versionar por accidente datos de prueba, o de listar los hashes de propietarios en un directorio legible por otros usuarios del sistema.

**Corrección propuesta**
- Exigir ruta absoluta por entorno o resolverla con `Path(...).resolve()`.
- Crear `DATA_DIR` explícitamente con `0o700` al arrancar.
- Añadir `api/data/` a `.gitignore` en el mismo cambio.

**Comprobación reproducible (NO EJECUTADA)**
```bash
git check-ignore -v api/data/x && echo "ignorado"
stat -c '%a' "$DATA_DIR"        # esperado tras corregir: 700
```

---

### SEC-09. Estado persistido validado solo por claves; analítica frágil (Baja)

**Archivo y ubicación:** `api/app/storage.py` (`_parse_state`), `api/app/services.py` (`monthly_analytics`).

**Evidencia**
- `_parse_state` comprueba `schema_version` y la presencia de seis claves, pero no los **tipos**. Un `verifications` que sea una cadena produce un `TypeError` y acaba como 500.
- `monthly_analytics` hace `datetime.fromisoformat(closed_at)` e `int(item["amount_cents"])` **fuera** del `try` de `iter_states`. Un valor mal formado lanza `ValueError` y rompe toda la analítica.
- Si `closed_at` fuera una fecha sin zona horaria, `.astimezone(timezone.utc)` la interpretaría como hora local del servidor y cambiaría el mes.

**Impacto**
- Requiere poder escribir en `DATA_DIR`, por lo que es de integridad y disponibilidad, no de acceso remoto.
- Aun así, un estado alterado o dañado deja la agregación mensual sin resultado.

**Corrección propuesta**
- Validar la forma con un modelo Pydantic estricto al leer (`extra="forbid"`, tipos y `schema_version` literal).
- En `monthly_analytics`, capturar `ValueError`, `TypeError` y `KeyError` por estado y omitirlo con un `logger.warning`, igual que `iter_states`.
- Exigir zona horaria: `dt = datetime.fromisoformat(closed_at); if dt.tzinfo is None: continue`.

**Comprobación reproducible (NO EJECUTADA)**
```python
def test_analitica_omite_estado_con_tipos_invalidos(service, store, data_dir):
    store.write("ok", _estado_cerrado("2026-01-10T10:00:00+00:00"))
    malo = data_dir / "zz"; malo.mkdir()
    s = _estado_cerrado("no-es-fecha"); (malo / "state.json").write_text(json.dumps(s))
    assert [f.new_active_users for f in service.monthly_analytics()] == [1]
```
Esperado hoy: falla con `ValueError`. Esperado tras corregir: pasa.

---

### SEC-10. Cabeceras de respuesta (Info/Baja)

**Archivo y ubicación:** `api/app/main.py` (sin middleware de cabeceras).

**Evidencia:** las respuestas con estado del usuario no llevan `Cache-Control: no-store` ni `X-Content-Type-Options: nosniff`.

**Impacto:** un proxy o navegador compartido podría cachear `GET /onboarding` o `GET /support/cases`. Riesgo bajo, y más relevante si en el futuro hay autenticación real.

**Corrección propuesta:** middleware ASGI mínimo que añada `Cache-Control: no-store` y `X-Content-Type-Options: nosniff` a todas las respuestas JSON. TLS y HSTS corresponden al proxy o despliegue, que no tengo.

**Comprobación reproducible (NO EJECUTADA):** `curl -sI -H '<identidad>' $B/onboarding | grep -iE 'cache-control|x-content-type'`.

---

## 3. Controles revisados sin hallazgo (solo lectura, no verificados en ejecución)

| Área | Observación |
|---|---|
| Inyección SQL | No hay SQL ni ORM en el feature. |
| Inyección de comandos o deserialización | No hay `subprocess`, `eval`, `pickle` ni `yaml.load`. |
| Recorrido de rutas | El directorio sale solo de `sha256(owner_id)`. `verification_id` y `step_id` nunca forman parte de rutas de archivo. `step_id` se compara contra una lista cerrada. |
| IDOR entre recursos | Las verificaciones se buscan solo dentro del estado del propietario autenticado y devuelven 404, no 403, para ajenas. Ese control es sólido, y SEC-01 es el que lo anula. |
| Identificadores | `verification_id` es `uuid4().hex` (122 bits aleatorios), no enumerable. |
| Validación de entradas | `extra="forbid"`, longitudes y enumeraciones con Pydantic. `fullmatch` en las expresiones regulares evita el problema del salto de línea final de `$` en Python. El documento se valida antes de tocar disco. |
| Reflejo de entrada | El valor del documento no se refleja en errores. Del 422 solo se devuelven nombres de campo saneados y truncados (el nombre de una clave desconocida controlada por el cliente puede aparecer, pero con caracteres restringidos y escapado por Angular en la interfaz). |
| Manejo de errores | Formato único `{code,message}` y 500 genérico sin traza. |
| Límite de cuerpo | `Content-Length` temprano y conteo real de bytes, aplicado antes de la identidad. No hay subida de archivos. |
| CSRF | Se requiere una cabecera personalizada, no se configura CORS y, por la lectura del manejo de `Content-Type` de FastAPI 0.115, un cuerpo no JSON se trata como bytes y falla la validación. Con esto, un formulario o `fetch` de otro origen no debería poder realizar acciones. **Si alguien añade CORS permisivo, esta conclusión deja de valer.** |
| Frontend: XSS | No hay `innerHTML`, `bypassSecurityTrust*` ni `eval` en el código entregado. Toda interpolación usa el escape de Angular. |
| Frontend: URLs | `encodeURIComponent` en `verification_id` y `step_id`. `API_BASE_URL` es fija y vacía. |
| Secretos | Ninguno incrustado en el código entregado. El `X-Owner-Id` no es un secreto (ver SEC-01). |
| Logs | No se registran valores de documento ni identificadores de propietario. Los logs de `storage.py` solo registran el tipo de excepción. |
| Escritura | Atómica (`mkstemp` + `fsync` + `os.replace`) con limpieza del temporal. El estado corrupto devuelve 500 sin sobrescribirse. |

---

## 4. Matriz: detectado, propuesto y ejecutado

| ID | Detectado (lectura) | Corrección propuesta (en este informe) | Comprobación propuesta | **Ejecutado** |
|---|---|---|---|---|
| SEC-01 | Sí | Token firmado emitido por el servidor | PoC + 4 pruebas pytest | **No** |
| SEC-02 | Sí | Bandera `ENABLE_MOCK_CONTROLS`, rol de soporte | Prueba de 404 con la bandera apagada | **No** |
| SEC-03 | Sí | `MAX_OWNERS` + rate limit | Bucle de 500 propietarios + prueba pytest | **No** |
| SEC-04 | Sí | Auditoría, pines exactos, bloqueo con hashes | `pip check`, `pip-audit`, `pip index versions` | **No** |
| SEC-05 | Sí | `%r` en el log | Prueba con `caplog` | **No** |
| SEC-06 | Sí | `ENABLE_DOCS` | `curl` a `/docs` y `/openapi.json` | **No** |
| SEC-07 | Sí | `flock` o fijar un solo worker | Prueba con `multiprocessing` | **No** |
| SEC-08 | Sí | Ruta absoluta, `0o700`, `.gitignore` | `git check-ignore`, `stat` | **No** |
| SEC-09 | Sí | Modelo Pydantic al leer, captura en analítica | Prueba con estado mal formado | **No** |
| SEC-10 | Sí | Middleware de cabeceras | `curl -I` | **No** |

La columna «Ejecutado» es **No** en todas las filas. El informe de Pruebas tampoco aporta salida real (todo figura como NO EJECUTADO), así que **no hay evidencia de que ninguna de las pruebas de seguridad existentes haya pasado**.

---

## 5. Orden recomendado de comprobación

1. **Fase 1, línea base** (según `testing_report.md` §7). Ejecutar la suite actual y adjuntar la salida real.
2. **Fase 2, PoC de SEC-01 y SEC-03** sobre el código **sin corregir**, para confirmar el riesgo con evidencia (los comandos están en cada hallazgo).
3. **Fase 3, aplicar correcciones** en este orden, con revisión humana: SEC-01 → SEC-02 → SEC-03 → SEC-09 → SEC-05/06/08/10 → SEC-07.
4. **Fase 4, repetir** las pruebas propuestas y adjuntar la salida.
5. **Fase 5, dependencias** (SEC-04): ejecutar antes de cualquier cambio de pines, y de nuevo después.

Evidencia a adjuntar: `evidencia/sec_poc_antes.txt`, `sec_poc_despues.txt`, `sec_freeze.txt`, `sec_pipaudit.txt` y la salida de pytest con JUnit (`skipped="0"`).

---

## 6. Supuestos, limitaciones y preguntas abiertas

**Supuestos**
- El servicio es un mock de pruebas (S-1). Si se publica con datos reales, SEC-01 y SEC-02 pasan a Alta/Crítica.
- Las rutas, los campos y los escenarios son los provisionales de Backend (S-4, P-3, P-4).
- Las correcciones de SEC-01 y SEC-02 cambian el contrato provisional (cabecera de identidad, `POST /session`, banderas de entorno). Hay que confirmarlas con Producto antes de implementar.

**Limitaciones**
- No vi `spec.md`, el árbol real, las pruebas existentes ni `tools/lab.py`.
- El final del spec de pruebas del frontend llegó truncado, y no revisé las pruebas de `ConsolaComponent` ni de `OnboardingComponent`.
- No evalué el despliegue (TLS, proxy, workers, redes), que condiciona SEC-03, SEC-07 y SEC-10.
- No revisé ningún secreto fuera del código entregado (variables de CI, archivos `.env`).

**Preguntas abiertas**
- **Q-1 (P-9).** ¿Cuál es el mecanismo de identidad real o aceptable en este entorno (token emitido, sesión, cabecera de un gateway)? ¿Se acepta el token propuesto en SEC-01?
- **Q-2.** ¿Este mock se desplegará en algún entorno compartido o accesible desde internet? Si es así, SEC-01 y SEC-03 son bloqueantes.
- **Q-3.** ¿Cuántos workers y réplicas se usarán (SEC-07), y qué proxy hay delante para el rate limit (SEC-03)?
- **Q-4 (P-6).** Cuando existan pagos reales, ¿quién decide un KYC? Eso define el rol de soporte de SEC-02.