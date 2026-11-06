# security_report.md

**Feature:** [H01] Validación final del cambio, tarea 4.1 (`python tools/verify.py`)
**Cambio:** `registro-activacion-wallet`
**Fecha del informe:** 2026-11-06 (America/Bogota, UTC-05:00)
**Rol:** Revisor de seguridad de aplicaciones

---

## 0. Estado y convenciones (leer primero)

**Estado global: no se ha ejecutado nada.** No he ejecutado comandos, pruebas, `tools/verify.py`, `pip-audit` ni consultas a PyPI/OSV. Todo lo de este informe sale de la **lectura estática** del material entregado por Arquitecto, Backend, Frontend y Pruebas.

| Etiqueta | Significado en este informe |
|---|---|
| **DETECTADO** | Riesgo visible en el código o procedimiento entregado, con evidencia citada. No implica explotación demostrada. |
| **DETECTADO (hipótesis)** | Depende de comportamiento de una librería que no he podido abrir ni ejecutar aquí. Hay que confirmarlo con la comprobación indicada. |
| **PROPUESTO** | Corrección sugerida. No está aplicada ni probada. |
| **VERIFICADO** | Comprobación ejecutada con salida real adjunta. **Ningún hallazgo tiene este estado.** |
| **NO EJECUTADO** | Comprobación definida pero sin salida real. |

**Este informe no es el registro de la tarea 4.1.** Que `python tools/verify.py` se ejecute y su resultado quede en `tasks.md` sigue **NO EJECUTADO** y le corresponde a la persona responsable de la entrega.

---

## 1. Alcance

### Revisado (archivos entregados en el historial)
- `api/app/config.py`, `api/app/errors.py`, `api/app/middleware.py`, `api/app/main.py`
- `api/requirements.txt` (referencia propuesta por Backend)
- Pruebas de Testing: `api/tests/test_h01_*.py`, `openspec/changes/registro-activacion-wallet/tests/test_registro_4_1.py`
- Procedimiento de ejecución y registro (testing_report §5–§6, plantilla de 4.1)

### No revisado, por no haberse recibido
- `openspec/changes/registro-activacion-wallet/specs/wallet-onboarding/spec.md` (P1)
- `tools/verify.py` y qué comprueba (P2)
- `tasks.md` (grupos 1–3), `api/app/routers/`, `services.py`, `schemas.py` y los tests existentes
- El frontend Angular. Frontend declara que no hay cambios, y no he visto diff que lo confirme.

### Consecuencia importante
El Issue **no define endpoints ni persistencia**. Por eso **no puedo evaluar** autenticación, autorización, acceso a recursos de otra persona (IDOR/BOLA), inyección SQL, manejo de secretos de negocio ni exposición de datos de wallet. No hay código que revisar en esas áreas, y no declaro "sin hallazgos" donde no hubo nada que mirar. La sección 5 recoge esas brechas y una lista de comprobación para cuando llegue la spec.

---

## 2. Resumen de hallazgos priorizados

| ID | Severidad | Hallazgo | Archivo | Estado |
|---|---|---|---|---|
| SEC-01 | Media | El límite de cuerpo en `chunked` podría devolver 400 en vez de 413 con cuerpos JSON/Form, y deja la app procesando un cuerpo truncado | `api/app/middleware.py` | DETECTADO (hipótesis) |
| SEC-02 | Media | Pins de dependencias de 2024, sin consulta a PyPI/OSV. Hay riesgo de DoS conocido en Starlette `<0.40.0` (multipart) | `api/requirements.txt` | DETECTADO (no verificado) |
| SEC-03 | Media | La evidencia de 4.1 solo se valida por formato y coherencia. Nada vincula el registro a una ejecución real | `test_registro_4_1.py`, plantilla de 4.1 | DETECTADO |
| SEC-04 | Baja | `Content-Length` se parsea de forma permisiva y los duplicados se ignoran | `api/app/middleware.py` | DETECTADO |
| SEC-05 | Baja | El 422 refleja nombres de campo derivados de la entrada del cliente, sin tope de longitud ni cantidad | `api/app/errors.py` | DETECTADO |
| SEC-06 | Baja | La evidencia (`/tmp/h01_evidencia`) puede contener secretos y se crea con permisos por defecto | testing_report §5–§6 | DETECTADO |
| SEC-07 | Baja | `/docs`, `/redoc` y `/openapi.json` quedan expuestos por defecto | `api/app/main.py` | DETECTADO |
| SEC-08 | Baja (diseño) | El catálogo usa 403 "Acceso denegado", lo que permite enumerar recursos de otros propietarios | `api/app/errors.py`, catálogo | DETECTADO (preventivo) |
| SEC-09 | Info | Observaciones menores: sin tope superior en `MAX_BODY_BYTES`, sin timeout de lectura, dependencias de test sin declarar, prueba débil de "sin escrituras" | varios | DETECTADO |

---

## 3. Hallazgos en detalle

### SEC-01 · Media · El límite de cuerpo puede devolver 400 y no impide el procesamiento de un cuerpo truncado

- **Estado:** DETECTADO (hipótesis). Sin ejecutar.
- **Archivo y ubicación:** `api/app/middleware.py`, `BodySizeLimitMiddleware.__call__`: la función `limited_receive` (`raise BodyTooLarge()`) y el bloque `except BodyTooLarge:`.
- **Evidencia:**
  1. `limited_receive` lanza `BodyTooLarge` **dentro** de la aplicación, cuando el conteo real supera `max_bytes`.
  2. El rechazo solo se emite en el `except` del propio middleware, si `response_started` es falso.
  3. Según mi lectura del código de FastAPI 0.115 (`fastapi/routing.py`, `get_request_handler`), un `Exception` genérico al leer el cuerpo se convierte en `HTTPException(400, "There was an error parsing the body")`. Eso **no lo he abierto ni ejecutado aquí**; lo recuerdo y debe confirmarse. Si es así, el `BodyTooLarge` nunca llega al `except` del middleware.
  4. Con ese comportamiento, `errors.py` respondería `400 BAD_REQUEST` y no `413 PAYLOAD_TOO_LARGE`.
  5. El propio Testing anticipó el riesgo en `test_h01_body_limit.py::test_json_chunked_excede_limite_413`, que espera 413.
  6. Si algún handler futuro hace `try/except Exception` alrededor de `await request.body()`, continuaría con un cuerpo **truncado** sin que el middleware lo note.
- **Impacto:**
  - **Contrato roto.** Los clientes no distinguen "demasiado grande" de "mal formado".
  - **Riesgo de integridad.** La app podría procesar un cuerpo parcial.
  - **Alcance acotado.** El límite sigue cortando la lectura, así que la memoria queda acotada a `max_bytes` más un bloque. Solo afecta a peticiones `chunked`; un `Content-Length` declarado mayor al límite se rechaza antes y sí devuelve 413.
- **Corrección propuesta (PROPUESTO, no aplicada):** que el middleware recuerde que se excedió el límite y **sustituya la respuesta de la app** por el 413. La variante incluye también la corrección de SEC-04 (parseo estricto de `Content-Length`). Reemplaza `api/app/middleware.py` entero:

```python
# api/app/middleware.py  (PROPUESTO)
"""Middleware ASGI que limita los bytes del cuerpo antes de parsearlo."""
import json
import re
from typing import Any, Awaitable, Callable, MutableMapping

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

# Solo dígitos ASCII y longitud acotada: evita '+5', ' 5', '1_0' y el límite
# de dígitos de int() en Python >= 3.11.
_DIGITS = re.compile(rb"[0-9]{1,18}")

_MSG_413 = "El cuerpo excede el tamaño permitido."
_MSG_400 = "Content-Length inválido."


class BodyTooLarge(Exception):
    """Se lanza cuando el cuerpo recibido supera el límite."""


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 1) Content-Length: estricto; varios valores = ambiguo = 400.
        lengths = [v for n, v in scope.get("headers", []) if n == b"content-length"]
        if len(lengths) > 1 or (lengths and not _DIGITS.fullmatch(lengths[0])):
            await self._reject(send, 400, "BAD_REQUEST", _MSG_400)
            return
        if lengths and int(lengths[0]) > self.max_bytes:
            await self._reject(send, 413, "PAYLOAD_TOO_LARGE", _MSG_413)
            return

        # 2) Conteo real (chunked o Content-Length engañoso).
        received = 0
        too_large = False
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received, too_large
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    too_large = True
                    raise BodyTooLarge()
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal response_started
            if too_large:
                # Falla cerrado: lo que la app emita tras exceder el límite
                # (p. ej. un 400 de FastAPI) se descarta; se enviará el 413.
                return
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except BodyTooLarge:
            pass
        if too_large and not response_started:
            await self._reject(send, 413, "PAYLOAD_TOO_LARGE", _MSG_413)

    @staticmethod
    async def _reject(send: Send, status: int, code: str, message: str) -> None:
        body = json.dumps({"code": code, "message": message}).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"connection", b"close"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
```

  Razonamiento sobre las pruebas existentes (**no ejecutado**): con esta versión deberían seguir cumpliéndose los casos de Content-Length inválido (400), declarado mayor (413 sin invocar la app), multi-chunk, Content-Length falso, "respuesta ya iniciada" (un solo `start`, 200) y `lifespan` delegado. Solo se confirma ejecutándolas.

- **Comprobación reproducible (NO EJECUTADO):**

```bash
cd api
# Antes de aplicar la corrección: si la hipótesis es cierta, esta prueba FALLA con 400.
python -m pytest tests/test_h01_body_limit.py::test_json_chunked_excede_limite_413 -v
# Tras aplicar la corrección: debe pasar, junto con todo el archivo.
python -m pytest tests/test_h01_body_limit.py -v -rsxX
```

  Criterio de aceptación: tras la corrección, 0 failed y 0 skipped. El resultado "antes" decide si el hallazgo se confirma o se descarta, y se debe registrar el que salga.

  Prueba adicional propuesta para el riesgo de cuerpo truncado:

```python
# api/tests/test_h01_body_limit.py  (añadir)
def test_handler_que_traga_excepcion_no_procesa_cuerpo_truncado(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX)
    register_error_handlers(app)

    @app.post("/swallow")
    async def swallow(request: Request):
        try:
            data = await request.body()
        except Exception:
            data = b""
        return {"size": len(data)}

    def chunks():
        yield b"x" * 60
        yield b"y" * 60

    resp = TestClient(app, raise_server_exceptions=False).post("/swallow", content=chunks())
    assert resp.status_code == 413   # la respuesta 200 de la app se descarta
```

---

### SEC-02 · Media · Dependencias antiguas y sin consulta a fuentes de vulnerabilidades

- **Estado:** DETECTADO (no verificado). Aplica si se adopta la base de Backend; si el repo ya tiene manifiesto, prevalece el existente.
- **Archivo y ubicación:** `api/requirements.txt`, las 4 líneas: `fastapi==0.115.0`, `starlette==0.38.6`, `uvicorn==0.30.6`, `pydantic==2.9.2`.
- **Evidencia:**
  - Backend declara en S7 que las versiones **no se verificaron contra PyPI ni OSV**.
  - Son versiones de septiembre de 2024, con más de dos años de antigüedad a 2026-11-06.
  - Según mi conocimiento (que puede estar desactualizado y **no he confirmado en OSV**), Starlette `<0.40.0` está afectada por **CVE-2024-47874** (DoS por `multipart/form-data` sin límite de tamaño en partes de formulario).
  - `fastapi==0.115.0` exige `starlette>=0.37.2,<0.39.0` (cita de Backend). Subir Starlette obliga a subir FastAPI en conjunto.
  - Es posible que existan avisos posteriores que desconozco. Debe consultarse OSV.
- **Impacto:**
  - Un endpoint con `Form`/`File` (si `wallet-onboarding` los usa) podría quedar expuesto a agotamiento de recursos.
  - Aunque no los use, un pin viejo sin auditar deja una cadena de suministro sin evidencia.
  - Las dependencias transitivas (`anyio`, `h11`, `pydantic-core`, etc.) no están fijadas, así que el entorno no es reproducible.
  - No hay constancia de que la consulta a PyPI/OSV se haya hecho.
- **Corrección propuesta (PROPUESTO):**
  1. Auditar con `pip-audit` en un entorno limpio.
  2. Elegir de PyPI el par `fastapi`/`starlette` vigente y compatible entre sí.
  3. Fijar **cada** paquete con `==`, incluido `starlette`, y registrar fecha y fuente de la consulta (PyPI/OSV).
  4. Valorar un lock con hashes (`pip-compile --generate-hashes` u otro mecanismo del repo).
  5. Mantener este cambio como un Issue de actualización aparte. El Issue H01 no es una actualización.
  6. Declarar las dependencias de test (`pytest`, `httpx`, `packaging`) en el manifiesto de desarrollo (ver SEC-09).
- **Comprobación reproducible (NO EJECUTADO, requiere red):**

```bash
python -m venv /tmp/audit-venv && . /tmp/audit-venv/bin/activate   # entorno aparte: no contaminar el del proyecto
pip install pip-audit
pip-audit -r api/requirements.txt --progress-spinner off 2>&1 | tee audit.log
echo "exit=${PIPESTATUS[0]}"          # esperado tras corregir: exit=0 y "No known vulnerabilities found"
pip install -r api/requirements.txt && pip check
python -m pytest api/tests/test_h01_requirements.py -v
date --iso-8601=seconds              # registrar fecha de la consulta
```

  Si no hay red, el criterio queda **NO CUMPLIDO**. No se sustituye por otra comprobación.

---

### SEC-03 · Media · La evidencia de la tarea 4.1 no está vinculada a una ejecución real

- **Estado:** DETECTADO.
- **Archivo y ubicación:** `openspec/changes/registro-activacion-wallet/tests/test_registro_4_1.py` (`CAMPOS`, `test_resultado_coherente_con_codigo_salida`, `test_estado_marca_coherente_con_resultado`) y la plantilla de 4.1.
- **Evidencia:**
  - Las pruebas validan que existan seis campos, que no haya `<…>`, que la fecha sea ISO y que `exit==0 ⇔ APROBADO ⇔ [x]`.
  - Nada comprueba que `verify.py` se ejecutó: ni referencia al commit, ni hash del log, ni enlace a CI.
  - Los campos "Código de salida" y "Resultado" se pueden escribir a mano y las pruebas pasan.
  - Testing lo reconoce implícitamente al decir que el código de salida es "la única evidencia".
- **Impacto:** un registro falso o escrito de memoria cumpliría el criterio CA-1. Como la tarea 4.1 sirve para dar el cambio por cerrado, es un riesgo de integridad del proceso.
- **Corrección propuesta (PROPUESTO):**
  1. Añadir a la plantilla dos campos: `Commit: <git rev-parse HEAD>` y `SHA-256 del log: <sha256sum de 21_verify.log>`. Opcionalmente `Enlace CI: <url>`.
  2. Archivar el log completo en el destino que responda P4, y que revise una persona distinta de quien ejecutó.
  3. Preferir la ejecución en CI como fuente de verdad. El hash local solo prueba integridad del log, no autenticidad.
  4. Ampliar las pruebas:

```python
# test_registro_4_1.py (PROPUESTO)
CAMPOS += ["Commit", "SHA-256 del log"]
CAMPO = re.compile(
    r"^- (Fecha/hora|Comando|Versión de Python|Código de salida|Resultado|"
    r"Resumen de la salida|Commit|SHA-256 del log):\s*(.*)$"
)

def test_commit_y_hash_con_formato(registro):
    _, f = registro
    assert re.fullmatch(r"`?[0-9a-f]{40}`?", f["Commit"])
    assert re.fullmatch(r"`?[0-9a-f]{64}`?", f["SHA-256 del log"])
```

- **Comprobación reproducible (NO EJECUTADO):**

```bash
git rev-parse HEAD                                  # debe coincidir con "Commit" de la nota
sha256sum <ruta-archivada>/21_verify.log            # debe coincidir con "SHA-256 del log"
python -m pytest openspec/changes/registro-activacion-wallet/tests/test_registro_4_1.py -v -rsxX
```

  Esta prueba solo es significativa **después** de ejecutar `verify.py` y registrar el resultado real. Hoy no hay registro, y por eso se espera que falle (no es un defecto).

---

### SEC-04 · Baja · Parseo permisivo de `Content-Length`

- **Estado:** DETECTADO. **Corrección incluida en el código de SEC-01.**
- **Archivo y ubicación:** `api/app/middleware.py`, `declared = int(value)` seguido de `break`.
- **Evidencia:**
  - `int()` de Python acepta formas como `+5`, valores con espacios o `1_0` (comportamiento del lenguaje, que **no he ejecutado aquí**).
  - El bucle usa solo la primera cabecera `content-length` y descarta el resto.
  - En Python ≥ 3.11, una cadena de dígitos muy larga hace que `int()` lance `ValueError`, que aquí se traduce en 400. No es un fallo, pero conviene acotarlo explícitamente.
- **Impacto:** discrepancias de interpretación con un proxy o servidor delante (desincronización de peticiones). El riesgo es bajo porque uvicorn/h11 ya valida el protocolo antes. Es defensa en profundidad.
- **Corrección propuesta:** `fullmatch` con `[0-9]{1,18}` y 400 si hay más de una cabecera (código en SEC-01).
- **Comprobación reproducible (NO EJECUTADO):** ampliar la parametrización existente:

```python
# test_h01_body_limit.py
@pytest.mark.parametrize("raw", [b"abc", b"-1", b"1.5", b"", b"+5", b" 5", b"1_0", b"9" * 40])
def test_content_length_invalido_400_sin_invocar_app(raw): ...

def test_content_length_duplicado_400():
    mw = BodySizeLimitMiddleware(_reader_app([]), max_bytes=MAX)
    sent = asyncio.run(_drive(mw, _scope([(b"content-length", b"5"), (b"content-length", b"500")]), []))
    assert sent[0]["status"] == 400
```

---

### SEC-05 · Baja · El 422 refleja nombres de campo controlados por el cliente

- **Estado:** DETECTADO.
- **Archivo y ubicación:** `api/app/errors.py`, `validation_exception_handler`: `loc = ".".join(str(p) for p in err.get("loc", ()))`, concatenado en `message`.
- **Evidencia:**
  - Los tests `test_validacion_422_*` solo cubren modelos con campos fijos (`body.qty`).
  - Para esquemas con claves dinámicas (por ejemplo `dict[str, int]`), Pydantic incluye la **clave enviada** en `loc`. Eso lo conozco por el diseño de Pydantic y **no está ejecutado**.
  - Esa clave termina en `message` sin tope de longitud ni de cantidad.
- **Impacto:**
  - Reflejo de texto arbitrario del cliente en la respuesta y posiblemente en logs.
  - Amplificación de respuesta, acotada por `MAX_BODY_BYTES`.
  - Riesgo de inyección en logs si algún consumidor registra `message`.
  - Al ser JSON, no es XSS directo. Es Baja.
- **Corrección propuesta (PROPUESTO):** sanear y limitar:

```python
import re
_SAFE = re.compile(r"[^A-Za-z0-9_.\-\[\]]")
_MAX_FIELDS, _MAX_LOC_LEN = 10, 64

# dentro del handler:
for err in errors:
    loc = _SAFE.sub("?", ".".join(str(p) for p in err.get("loc", ())))[:_MAX_LOC_LEN]
    if loc and loc not in fields:
        fields.append(loc)
    if len(fields) >= _MAX_FIELDS:
        break
```

- **Comprobación reproducible (NO EJECUTADO):**

```python
# api/tests/test_h01_errors.py (añadir; requiere `from typing import Dict`)
def test_422_clave_dinamica_larga_no_se_refleja(client_with_dict_route):
    # ruta de prueba: @app.post("/map") def m(d: Dict[str, int]): ...
    resp = client_with_dict_route.post("/map", json={"A" * 5000 + "\n<x>": "no-numerico"})
    assert resp.status_code == 422
    msg = resp.json()["message"]
    assert len(msg) < 1000 and "\n" not in msg and "<x>" not in msg
```

---

### SEC-06 · Baja · Manejo de la evidencia y del entorno de ejecución

- **Estado:** DETECTADO.
- **Archivo y ubicación:** testing_report §5 y §6 (`/tmp/h01_evidencia`, `pip freeze`, `git status`, `tee` de `verify.py`, `pip install pip-audit`).
- **Evidencia:**
  - `mkdir -p /tmp/h01_evidencia` usa permisos por defecto del `umask`, en un directorio compartido (`/tmp`).
  - Se guardan en él la salida completa de `verify.py` (**contenido desconocido**, P2), el entorno instalado y el estado de git.
  - Una salida de `verify.py` podría incluir rutas, variables de entorno o tokens.
  - La plantilla pide pegar un "Resumen de la salida" en `tasks.md`, que se versiona.
  - `pip install pip-audit` se hace en el mismo entorno del proyecto.
- **Impacto:** posible fuga de secretos o datos internos a otros usuarios del host o al repositorio. Además, ejecutar un script desconocido con credenciales reales aumenta el riesgo.
- **Corrección propuesta (PROPUESTO):**
  1. Crear la carpeta con `umask 077; EV=$(mktemp -d)` y usar `$EV` en lugar de la ruta fija.
  2. Ejecutar `verify.py` en un entorno **sin credenciales reales** (variables de producción ausentes).
  3. Revisar y **redactar** la salida antes de copiarla a `tasks.md` o a un PR. Si hay un secreto, tratarlo como comprometido y rotarlo.
  4. Instalar `pip-audit` en un venv aparte, como en SEC-02.
- **Comprobación reproducible (NO EJECUTADO):**

```bash
umask 077; EV=$(mktemp -d); stat -c '%a %U' "$EV"      # esperado: 700 <usuario>
python tools/verify.py > "$EV/21_verify.log" 2>&1; echo "exit=$?"
grep -nEi "(token|secret|password|passwd|api[_-]?key|authorization|bearer|BEGIN [A-Z ]*PRIVATE KEY)" "$EV/21_verify.log" \
  || echo "sin coincidencias (búsqueda heurística, no garantiza ausencia de secretos)"
```

---

### SEC-07 · Baja · Documentación interactiva expuesta por defecto

- **Estado:** DETECTADO.
- **Archivo y ubicación:** `api/app/main.py`, `app = FastAPI(title="API")`.
- **Evidencia:** FastAPI publica `/docs`, `/redoc` y `/openapi.json` salvo que se desactiven. No hay configuración en `main.py` ni en `config.py`. No hay prueba que la contemple.
- **Impacto:** cuando se registren routers de `wallet-onboarding`, el esquema completo (rutas, campos, errores) queda visible para cualquiera. Facilita el reconocimiento. Baja gravedad, porque no es un secreto.
- **Corrección propuesta (PROPUESTO):** desactivar por defecto y habilitar solo por variable de entorno en desarrollo.

```python
# config.py
ENABLE_DOCS: bool = os.environ.get("ENABLE_DOCS", "").strip().lower() in {"1", "true"}
# main.py
app = FastAPI(
    title="API",
    docs_url="/docs" if ENABLE_DOCS else None,
    redoc_url="/redoc" if ENABLE_DOCS else None,
    openapi_url="/openapi.json" if ENABLE_DOCS else None,
)
```

- **Comprobación reproducible (NO EJECUTADO):**

```python
# api/tests/test_h01_integration_main.py (añadir)
@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_docs_desactivadas_por_defecto(client, path):
    resp = client.get(path)
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"
```

  Se asume que `ENABLE_DOCS` no está definida en el entorno de la prueba (usar `monkeypatch.delenv`). Si el producto necesita la documentación pública, se descarta el hallazgo por decisión explícita.

---

### SEC-08 · Baja (diseño preventivo) · 403 "Acceso denegado" puede permitir enumerar recursos ajenos

- **Estado:** DETECTADO (preventivo). No hay endpoints, así que no hay explotación posible hoy.
- **Archivo y ubicación:** `api/app/errors.py`, `_CODES[403]` y el mensaje `"Acceso denegado."`. El mismo catálogo está en Arquitecto §3 y Backend §5.
- **Evidencia:** el catálogo ofrece 403 para "Sin permiso" y 404 para "Recurso inexistente". Si un futuro endpoint devuelve 403 al consultar un recurso de otro propietario y 404 cuando no existe, un atacante distingue ambos casos.
- **Impacto:** enumeración de identificadores de wallet o de activaciones ajenas. Es el patrón habitual que acompaña a IDOR/BOLA.
- **Corrección propuesta (PROPUESTO):** regla de diseño. Los recursos se buscan **siempre filtrando por propietario autenticado**, y si el recurso no es del solicitante se responde 404 `NOT_FOUND`, idéntico al caso "no existe". Reservar 403 para permisos por rol sobre recursos propios.
- **Comprobación reproducible (NO EJECUTADO, cuando existan endpoints):** crear un recurso con la identidad A. Con la identidad B, consultar ese id y un id inexistente. Ambas respuestas deben ser iguales en estado, cuerpo y cabeceras relevantes.

---

### SEC-09 · Informativo · Observaciones menores

| Observación | Ubicación | Propuesta |
|---|---|---|
| `MAX_BODY_BYTES` no tiene tope superior. Un valor enorme desactiva el límite en la práctica. Un valor inválido se corrige en silencio al valor por defecto, sin aviso. | `config.py`, `_int_env` | Definir un máximo razonable, y registrar un aviso (sin volcar el valor) cuando se ignore. |
| El middleware no limita el tiempo de lectura del cuerpo (peticiones lentas). | `middleware.py` | Configurar timeouts en el servidor o proxy (uvicorn/ingress). |
| El middleware solo aplica a `scope["type"] == "http"`. Los mensajes WebSocket no tienen límite. | `middleware.py` | Irrelevante hoy (sin WebSocket). Revisar si se añaden. |
| `test_h01_requirements.py` importa `packaging`, y las pruebas usan `httpx` y `pytest`, que no figuran en `requirements.txt`. Podría fallar por entorno y no por defecto. | `api/tests/`, `requirements.txt` | Declararlos en el manifiesto de desarrollo con versiones fijas. |
| `test_sin_escrituras_en_disco` solo ve escrituras dentro de `tmp_path`. Si el código escribe en una ruta absoluta o en otro directorio, no lo detecta. | `test_h01_integration_main.py` | Tratarla como evidencia débil. No cuenta como prueba de ausencia de persistencia. |
| El handler 500 registra solo el tipo de la excepción. Esto es correcto contra fugas, pero reduce la trazabilidad. | `errors.py` | Valorar un identificador de correlación en el log y en la respuesta. |

---

## 4. Áreas revisadas

| Área solicitada | Resultado | Detalle |
|---|---|---|
| Validación de entradas | Parcial | Límite de cuerpo y formato de errores revisados (SEC-01, 04, 05). No hay esquemas de negocio. |
| Exposición de datos sensibles | Parcial | El 500 no devuelve trazas ni texto de la excepción, y el 422 no devuelve valores recibidos. Es lo que **dicen** el código y las pruebas, y no está ejecutado. Quedan SEC-05, SEC-06 y SEC-07. |
| Secretos | Sin secretos en el código entregado | No aparecen credenciales ni tokens en los archivos revisados. No lo he comprobado con un escáner. Ver SEC-06 para el procedimiento. |
| Inyección | No evaluable | No hay SQL, consultas ni comandos construidos con entrada (Backend §7). La prueba de `config` usa `subprocess` con lista de argumentos y sin `shell=True`. |
| Autenticación / autorización / acceso a recursos ajenos | **No evaluable** | No hay endpoints, identidad ni persistencia. Ver §5. |
| Dependencias | Hallazgo | SEC-02. |

---

## 5. Brechas y lista de comprobación para cuando llegue `spec.md`

Hasta que se aporte la spec (P1), estas áreas quedan **sin revisar**. Aceptar esta brecha requiere decisión humana.

1. **Identidad**
   - Debe obtenerse en el servidor con `Depends` y nunca del cuerpo, query o cabeceras que controle el cliente (P6).
   - Probar sin credenciales (401), con credencial inválida o caducada (401) y con una válida.
2. **Aislamiento entre propietarios (IDOR/BOLA)**
   - Cada lectura, activación o modificación filtra por propietario.
   - Prueba con dos identidades A y B sobre cada ruta con id. Debe resultar en 404 idéntico (SEC-08).
3. **Activación de wallet**
   - Códigos o tokens con entropía suficiente (`secrets`), de un solo uso y con caducidad.
   - Límite de intentos y de ritmo, sin diferencias de respuesta que revelen si existe el registro.
   - No registrar tokens en logs ni devolverlos en errores.
4. **Registro**
   - Validación de formato y longitud de cada campo.
   - Respuestas uniformes ante usuario ya existente, para no enumerar cuentas (409 solo si la spec lo exige).
5. **Persistencia en archivos (si aplica)**
   - Directorio derivado de `sha256(owner_id)` con `hexdigest` (sin riesgo de recorrido de rutas).
   - Escritura atómica y lock por propietario.
   - El hash no es un control de acceso, y no debe aparecer en respuestas.
6. **Subida de archivos (si aplica)**
   - Nombres saneados, lista de tipos y extensiones, y límite de tamaño (SEC-01 y SEC-02).
7. **Frontend**
   - Sin secretos en el bundle.
   - No guardar tokens en `localStorage` si la spec admite alternativas.
   - Mensajes de error sin datos internos.
   - Se revisará cuando haya contrato.

---

## 6. Registro de verificaciones

**Ninguna se ejecutó.** Esta tabla indica qué habría que ejecutar y no afirma resultados.

| ID | Comprobación | Hallazgo | Estado | Resultado esperado |
|---|---|---|---|---|
| V-01 | `pytest api/tests/test_h01_body_limit.py::test_json_chunked_excede_limite_413` (antes de corregir) | SEC-01 | NO EJECUTADO | Si la hipótesis es cierta, falla con 400. |
| V-02 | `pytest api/tests/test_h01_body_limit.py` (tras corregir) | SEC-01, 04 | NO EJECUTADO | 0 failed, 0 skipped. |
| V-03 | `pip-audit -r api/requirements.txt` en venv aparte, más `pip check` | SEC-02 | NO EJECUTADO | `exit=0` y sin vulnerabilidades, o lista de IDs con fecha. |
| V-04 | Pruebas de registro ampliadas y cotejo de commit/hash | SEC-03 | NO EJECUTADO | Coinciden `git rev-parse HEAD` y `sha256sum` del log. |
| V-05 | Parametrización ampliada de `Content-Length` | SEC-04 | NO EJECUTADO | 400 en todas las formas inválidas. |
| V-06 | Prueba de clave dinámica larga en 422 | SEC-05 | NO EJECUTADO | Mensaje corto, sin saltos de línea ni caracteres reflejados. |
| V-07 | `stat` del directorio de evidencia y `grep` heurístico del log | SEC-06 | NO EJECUTADO | Permisos `700` y sin coincidencias, o secretos redactados. |
| V-08 | `GET /docs`, `/redoc`, `/openapi.json` | SEC-07 | NO EJECUTADO | 404 con formato único. |
| V-09 | Dos identidades sobre recurso ajeno e inexistente | SEC-08 | NO EJECUTADO (no hay endpoints) | Respuestas idénticas. |
| V-10 | `python tools/verify.py; echo "exit=$?"` | Tarea 4.1 | **NO EJECUTADO** | Código de salida registrado con la plantilla (S2: 0 = éxito). |
| V-11 | `python tools/lab.py test api` y `cd api && python -m pytest tests -v -rsxX` | Regresión | NO EJECUTADO | 0 failed, 0 errors, 0 skipped. |

---

## 7. Supuestos y preguntas pendientes

**Supuestos de este informe**
- **A1.** La base propuesta por Backend (`config.py`, `errors.py`, `middleware.py`, `main.py`, `requirements.txt`) se adopta tal cual. Si el repositorio ya tiene archivos equivalentes, los hallazgos SEC-01, 04, 05, 07 y 09 deben **reevaluarse sobre los archivos existentes**.
- **A2.** Mis afirmaciones sobre el comportamiento de FastAPI/Starlette, Pydantic y `int()` provienen de mi conocimiento y no están verificadas aquí. Cada una tiene su comprobación asociada.
- **A3.** La referencia a CVE-2024-47874 es de memoria y puede estar incompleta o desactualizada. La fuente que decide es OSV/PyPI el día de la consulta.

**Preguntas pendientes**
- **P1.** Contenido de `spec.md`. Sin él quedan sin revisar autenticación, autorización, IDOR y activación.
- **P2.** Qué hace `tools/verify.py`, con qué entorno y credenciales se ejecuta. ¿Llama a `lab.py test api`? ¿Accede a red o a servicios?
- **P3.** Qué pruebas existentes en `api/tests/` cubren los POST con cuerpo válido. Si ninguna, una persona debe aceptar la brecha.
- **P4.** Dónde se archiva la evidencia, y quién la revisa (SEC-03, SEC-06).
- **P6.** Mecanismo de identidad real del producto.
- **P8.** Qué ocurre si `verify.py` falla: bloquear el cierre o abrir un Issue nuevo.
- **P9.** ¿Se adopta la actualización de dependencias dentro de este cambio o en un Issue aparte (SEC-02)?
- **P10.** ¿La documentación `/docs` debe ser pública en algún entorno (SEC-07)?

---

## 8. Conclusión

- **Se puede cerrar la tarea 4.1** solo cuando una persona ejecute `python tools/verify.py` y registre el resultado real con la plantilla, incluyendo los vínculos de SEC-03. Hasta entonces **no hay evidencia de verificación**.
- **Antes de aceptar la base de Backend**, confirmar o descartar SEC-01 con la prueba V-01 y resolver SEC-02 con `pip-audit`.
- **El análisis de autenticación, autorización y acceso a recursos de otra persona queda pendiente** hasta contar con la spec y el código de `wallet-onboarding`. No debe interpretarse como "sin hallazgos".