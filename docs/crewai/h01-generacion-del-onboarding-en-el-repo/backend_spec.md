# backend_spec.md

## 1. Resumen de la solución

Este backend implementa el mock de onboarding de la wallet (H01, tareas 2.2 a 2.8 del lado API), en Python con FastAPI (Starlette). Cubre:

- identidad por dependencia (`get_current_owner`);
- estado de wallet y pasos con bloqueo;
- verificación KYC con cuatro escenarios, consulta y decisión sobre `PENDING`;
- documento `TEST-`;
- eventos de inicio, paso y cierre con cálculo de duración;
- consola (`/health`, `/scenarios`, `/support/cases`, `/control/reset`);
- función de agregación mensual (2.8).

Todo error responde `{"code","message"}`.

**Stack.** El stack es Python + FastAPI, tal como indican el Issue y el Arquitecto. No hay Java, Quarkus ni Maven en ningún documento previo, así que no hay conflicto que anotar.

**Fuera de este entregable (frontend Angular).** Las partes de frontend de 2.2 (`MockApiService`, `SessionService`), 2.6 y 2.7 (UI de consola y confirmación de reset) no son backend. Aquí solo se entrega su contrato en `schemas.py`, que el frontend debe espejar.

**Persistencia.** No hay base de datos en el Issue ni contrato de Datos aprobado en el contexto. **No se emite SQL.** El estado se guarda en un JSON por propietario (ver sección 7).

## 2. Estructura de archivos

```text
api/
├── requirements.txt
├── data/                      # DATA_DIR por defecto (generado en runtime, no versionar)
└── app/
    ├── __init__.py
    ├── config.py              # constantes/entorno (MAX_BODY_BYTES, DATA_DIR, ...)
    ├── errors.py              # ApiError + handlers de error con formato único
    ├── middleware.py          # límite de tamaño de cuerpo (ASGI puro)
    ├── schemas.py             # modelos Pydantic de request/response/error
    ├── storage.py             # capa de acceso a archivos (hash, lock, escritura atómica)
    ├── services.py            # lógica de negocio + dependencia get_current_owner
    ├── main.py                # crea la app, registra middleware, handlers y routers
    └── routers/
        ├── __init__.py
        ├── console.py         # /health, /scenarios, /support/cases, /control/reset
        ├── kyc.py             # /kyc/verifications...
        └── onboarding.py      # /onboarding, /onboarding/steps/{step_id}
```

`get_current_owner` queda en `services.py`, como decidió el Arquitecto. El acceso a archivos va en `storage.py`, capa aparte, como exige el rol.

## 3. Endpoints

Las rutas marcadas (S-4) son las provisionales del Arquitecto. Los nombres de campos, escenarios, pasos y estados de wallet no estaban en el contexto (P-3, P-4). Se eligieron los más conservadores y se listan en la sección 9.

| Método | Ruta | Identidad | Entrada | Respuesta | Errores |
|---|---|---|---|---|---|
| GET | `/health` | No | — | 200 `{"status":"ok"}` | 413/500 |
| GET | `/scenarios` | No (catálogo estático) | — | 200 `{"scenarios":[{"name","description"}]}` | 500 |
| GET | `/support/cases` | Sí | — | 200 `{"cases":[{"verification_id","status","message"}]}` | 401, 500 |
| POST | `/kyc/verifications` | Sí | JSON `{"document_number","scenario"}` | 201 `VerificationResponse` | 401, 409 `LIMIT_REACHED`, 413, 422 `DOCUMENT_NOT_TEST`/`VALIDATION_ERROR`, 500 |
| GET | `/kyc/verifications/{verification_id}` (S-4) | Sí | path | 200 `VerificationResponse` | 401, 404 `NOT_FOUND` |
| POST | `/kyc/verifications/{verification_id}/decision` (S-4) | Sí | JSON `{"decision":"APPROVED"\|"REJECTED"}` | 200 `VerificationResponse` | 401, 404, 409 `VERIFICATION_NOT_PENDING`, 413, 422 |
| GET | `/onboarding` (S-4) | Sí | — | 200 `OnboardingStateResponse` | 401, 500 |
| POST | `/onboarding/steps/{step_id}` (S-4) | Sí | JSON opcional `{"document_number"}` (solo en `registro`) | 200 `OnboardingStateResponse` | 401, 404, 409 `STEP_BLOCKED`, 413, 422 |
| POST | `/control/reset` | Sí | — (sin cuerpo) | 200 `{"status":"reset"}` | 401 |

**Formas de respuesta.**

- `VerificationResponse`: `verification_id`, `document_number`, `scenario`, `status`, `created_at`, `decided_at` (nulo mientras esté `PENDING`).
- `OnboardingStateResponse`: `wallet_status`, `current_step` (nulo al terminar), `steps[{id,order,status}]`, `low_amount_payments_enabled`, `duration_seconds` (nulo hasta el cierre).

**Escenarios KYC (provisionales, P-3).** El nombre del escenario es el estado resultante: `APPROVED`, `REJECTED`, `PENDING`, `EXPIRED`.

**Pasos (provisionales, P-4).** El orden es `registro` → `kyc` → `activacion`.

**Estados de wallet.** `NOT_STARTED`, `IN_PROGRESS`, `KYC_PENDING`, `KYC_FAILED`, `ACTIVE`. El acceso a pagos de bajo monto es `low_amount_payments_enabled = (wallet_status == ACTIVE)` (P-6).

**Reglas de pasos.**

- `registro` exige `document_number` válido y no tiene requisito previo.
- `kyc` exige `registro` completado y que la última verificación esté `APPROVED`.
- `activacion` exige `kyc` completado. Al completarse cierra el onboarding.
- Repetir un paso ya completado es idempotente: responde 200 sin duplicar eventos.

## 4. Reglas de validación (en servidor)

| Campo | Regla | Resultado si falla |
|---|---|---|
| Cuerpo JSON | `extra="forbid"`: un campo desconocido (p. ej. `owner`) se rechaza | 422 `VALIDATION_ERROR` |
| `document_number` | `str`, 1 a 64 caracteres | 422 `VALIDATION_ERROR` |
| `document_number` | Debe empezar por `TEST-` (sensible a mayúsculas) | 422 `DOCUMENT_NOT_TEST` |
| `document_number` | Tras el prefijo, 1 a 59 caracteres `[A-Za-z0-9-]` (sin espacios ni caracteres de control) | 422 `VALIDATION_ERROR` |
| `scenario` | Uno de `APPROVED`, `REJECTED`, `PENDING`, `EXPIRED` | 422 `VALIDATION_ERROR` |
| `decision` | `APPROVED` o `REJECTED` | 422 `VALIDATION_ERROR` |
| `step_id` | Debe ser `registro`, `kyc` o `activacion` | 404 `NOT_FOUND` |
| `verification_id` | Se busca solo dentro del estado del propietario, nunca se usa como ruta de archivo | 404 `NOT_FOUND` |
| `X-Owner-Id` | Cabecera obligatoria, `[A-Za-z0-9._-]{1,128}` | 401 `UNAUTHENTICATED` |
| Cuerpo | Máximo `MAX_BODY_BYTES` (16384 por defecto) | 413 `PAYLOAD_TOO_LARGE` |
| `Content-Length` | Debe ser solo dígitos | 400 `BAD_REQUEST` |

El valor del documento nunca se refleja en los mensajes de error. La validación del documento ocurre antes de tocar disco.

## 5. Manejo de errores

Hay un único formato `{"code","message"}`. Los handlers están en `errors.py` y se registran en `main.py`:

- `ApiError` (subclase de `HTTPException`): usa su `code` y `message`.
- `HTTPException` de Starlette: se traduce a código y mensaje fijos por estado (401, 404, 405, 409, 413 y otros).
- `RequestValidationError`: responde 422 `VALIDATION_ERROR`. Solo menciona nombres de campo saneados y truncados, nunca valores.
- `Exception`: responde 500 `INTERNAL_ERROR` con mensaje genérico. La traza solo va al log del servidor.

`ApiError` hereda de `HTTPException` por una razón concreta. FastAPI convierte cualquier otra excepción lanzada al leer el cuerpo en un 400 genérico. Heredar permite que el 413 del middleware atraviese FastAPI intacto.

## 6. Límites de tamaño

Una configuración obligatoria del contrato: `MAX_BODY_BYTES` en `api/app/config.py`.

- `BodyLimitMiddleware` es ASGI puro y no usa `BaseHTTPMiddleware`.
- Si `Content-Length` supera el límite, responde 413 sin leer el cuerpo.
- Si el encabezado falta o es falso (chunked), envuelve `receive`, cuenta los bytes recibidos y corta con 413 al superar el límite, antes de que se complete el parseo.
- No hay subida de archivos en este feature. El único cuerpo es JSON pequeño y no se usa `await file.read()`.

## 7. Persistencia, concurrencia y transacciones

**Origen.** No hay base de datos ni migraciones; por eso **no hay bloque SQL**. Si Datos aprueba un contrato más adelante, `storage.py` es el único punto a sustituir.

**Almacén.** El estado va en `DATA_DIR/<sha256(owner_id).hexdigest()>/state.json`. El nombre del directorio sale solo del hash. Nada que envíe el cliente determina la ruta. Dos usuarios no comparten archivo. Ni el identificador ni el hash aparecen en respuestas ni en mensajes de error.

**Contenido del JSON.** `schema_version`, `started_at`, `closed_at`, `steps_completed`, `verifications`, `events`, `spend`.

**Transacción.** No hay transacciones de BD. Cada operación de negocio es una secuencia leer → validar → modificar → escribir bajo un lock, y se confirma con una única escritura atómica.

- Se usa un conjunto fijo de 64 `threading.Lock` indexado por el hash del propietario. La memoria queda acotada aunque llegue un número ilimitado de identificadores.
- Los endpoints son `def` síncronos, así que FastAPI los ejecuta en su pool de hilos.
- La escritura usa un archivo temporal en el mismo directorio, `fsync` y `os.replace`. El temporal se borra si algo falla.
- Se asume un solo proceso. Con varios workers haría falta un bloqueo de archivo (pendiente).

**Archivos preexistentes.**

- Si el directorio del hash existe, se reutiliza.
- Un `state.json` ilegible, corrupto o con `schema_version` distinta produce 500 `INTERNAL_ERROR` y **no se sobrescribe**.
- Un temporal `.state-*.tmp` huérfano por caída del proceso no se limpia automáticamente. Es inofensivo, porque no se lee.
- `POST /control/reset` borra solo el `state.json` del propietario autenticado.

**Eventos y duración.**

- `ONBOARDING_STARTED` y `STEP_COMPLETED` (con el `step`) se registran al completar el primer paso. Al completar `activacion` se registra además `ONBOARDING_CLOSED`.
- Los eventos van en `state.json` y no tienen endpoint público (S-6).
- `duration_seconds = closed_at − started_at`, en segundos con 3 decimales (P-7). El reloj se inyecta en el servicio para poder probarlo.

**Analítica 2.8.** `OnboardingService.monthly_analytics()` recorre los estados y agrupa por mes UTC de `closed_at`. Devuelve filas `{month, new_active_users, attributed_spend_cents}`. No hay endpoint HTTP, porque P-8 (formato y destino) está abierta. Ningún endpoint escribe `spend`, así que **el gasto atribuido será 0 hasta que exista un origen de pagos** (P-6).

## 8. Recorrido de casos

**Caso válido: `POST /kyc/verifications` con `{"document_number":"TEST-0001","scenario":"APPROVED"}` y `X-Owner-Id: demo-user-1`.**

1. `BodyLimitMiddleware` comprueba `Content-Length` y cuenta los bytes recibidos.
2. FastAPI resuelve `get_current_owner` y valida la cabecera. Después valida el cuerpo con `KycVerificationRequest`.
3. El router delega en `OnboardingService.create_verification`.
4. El servicio valida el prefijo `TEST-` y el resto del documento antes de tocar disco.
5. Con el lock del propietario, lee `state.json` (o el estado por defecto), comprueba el tope de verificaciones y crea el registro. El escenario `APPROVED` produce estado `APPROVED` y `decided_at` con la hora actual.
6. Escribe de forma atómica en `DATA_DIR/<sha256>/state.json` y responde 201 con `VerificationResponse`.

**Caso de error: `{"document_number":"12345678","scenario":"APPROVED"}`.**

1. Los pasos 1 a 3 son iguales.
2. El servicio detecta que no empieza por `TEST-` y lanza `ApiError(422, "DOCUMENT_NOT_TEST", ...)`.
3. **No se abre ningún archivo** ni se toma el lock.
4. El handler de `ApiError` responde `{"code":"DOCUMENT_NOT_TEST","message":"..."}`.

## 9. Supuestos y pendientes

**Dependencias de información faltante (conservadoras, deben confirmarse):**

- **B-1 (P-3).** Campos `document_number` y `scenario`, y los cuatro escenarios `APPROVED`/`REJECTED`/`PENDING`/`EXPIRED`, son provisionales. La estructura de `/scenarios` y `/support/cases` también. `/support/cases` lista las verificaciones del propietario no aprobadas.
- **B-2 (P-4).** Pasos, estados de wallet y rutas de onboarding y decisión KYC son provisionales (S-4).
- **B-3 (P-9).** La identidad llega en la cabecera `X-Owner-Id`, como credencial de mock. Debe sustituirse por el mecanismo real sin cambiar `get_current_owner`. `/health` y `/scenarios` son anónimos.
- **B-4 (P-6).** `low_amount_payments_enabled` es un campo añadido: `true` solo con wallet `ACTIVE`. No hay endpoint de pagos ni umbral de «bajo monto».
- **B-5 (P-7).** `duration_seconds` se expone en `GET /onboarding` como campo añadido y está en segundos.
- **B-6 (P-8).** Mes en UTC, sin endpoint de analítica. «Nuevo usuario activo» es quien cierra el onboarding ese mes. El gasto atribuido es la suma de `spend` de esos usuarios.
- **B-7 (P-5).** Persistencia en archivos JSON, un solo proceso. Conviene añadir `api/data/` a `.gitignore`.
- **B-8.** Códigos añadidos al contrato conservador del Arquitecto, que son decisiones mías:
  - 409 `LIMIT_REACHED`: máximo 50 verificaciones por propietario (`MAX_VERIFICATIONS_PER_OWNER`), para acotar el disco.
  - 400 `BAD_REQUEST`: `Content-Length` no numérico.
  - 405 `METHOD_NOT_ALLOWED`: método no permitido en una ruta existente.
- **B-9.** El paso `registro` valida `document_number` pero no lo almacena. Los demás pasos rechazan un `document_number` en el cuerpo (422).
- **B-10.** La «ventana de pasos» que mencionó el Arquitecto para `config.py` no se implementó: no hay requisito que la defina.

**Dependencias (versiones sin verificar).**

- El Issue no pide actualizar paquetes. No conozco el `requirements.txt` existente: si ya tiene líneas, conserva las suyas y fusiona solo lo que falte.
- Los pines entregados (`fastapi==0.115.6`, `starlette==0.41.3`, `uvicorn==0.34.0`, `pydantic==2.10.4`) son los que considero coherentes entre sí. **No están verificados contra PyPI ni OSV** en este contexto. Hay que validarlos con `pip check` y `pip-audit` (comandos en la sección 10) antes de aceptarlos.
- `pytest` y `httpx` son del rol de Pruebas y van en `requirements-dev.txt`.

**Otros.**

- No se entregan pruebas (rol de Pruebas). Para que el handler `Exception` devuelva 500 en `TestClient`, usar `raise_server_exceptions=False`.
- No se pudo revisar la spec (P-1): los criterios dependen de lo derivado por el Arquitecto.

---

# Código

```python
# api/app/__init__.py
```

```python
# api/app/config.py
"""Constantes y configuración del API, leídas del entorno con valores por defecto."""
import os
from pathlib import Path


def _positive_int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"La variable de entorno {name} debe ser un entero positivo.") from exc
    if value <= 0:
        raise RuntimeError(f"La variable de entorno {name} debe ser un entero positivo.")
    return value


# Directorio raíz donde se guarda el estado por propietario (subdirectorios con hash SHA-256).
DATA_DIR: Path = Path(os.environ.get("DATA_DIR", "data"))

# Tamaño máximo del cuerpo de cualquier solicitud, en bytes (contrato: 413 si se supera).
MAX_BODY_BYTES: int = _positive_int_env("MAX_BODY_BYTES", 16384)

# Tope de verificaciones KYC por propietario (acota el uso de disco del mock).
MAX_VERIFICATIONS_PER_OWNER: int = _positive_int_env("MAX_VERIFICATIONS_PER_OWNER", 50)

# Cabecera de identidad del mock (S-2 / P-9: sustituir por el mecanismo real de autenticación).
OWNER_HEADER: str = "X-Owner-Id"
OWNER_ID_PATTERN: str = r"[A-Za-z0-9._-]{1,128}"
```

```python
# api/app/errors.py
"""Excepción de dominio y handlers que unifican el formato {"code","message"}."""
import logging
import re
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")

_HTTP_ERRORS: dict[int, tuple[str, str]] = {
    400: ("BAD_REQUEST", "La solicitud no es válida."),
    401: ("UNAUTHENTICATED", "No se pudo identificar al usuario."),
    403: ("FORBIDDEN", "No tienes permisos para realizar esta acción."),
    404: ("NOT_FOUND", "El recurso solicitado no existe."),
    405: ("METHOD_NOT_ALLOWED", "El método no está permitido para esta ruta."),
    409: ("CONFLICT", "La solicitud entra en conflicto con el estado actual."),
    413: ("PAYLOAD_TOO_LARGE", "El cuerpo de la solicitud supera el tamaño permitido."),
    422: ("VALIDATION_ERROR", "La solicitud no es válida."),
}

_UNSAFE_NAME_CHARS = re.compile(r"[^A-Za-z0-9_.\-]")


class ApiError(HTTPException):
    """Error de negocio con código estable. Hereda de HTTPException para que FastAPI lo propague tal cual."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message


def error_body(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _field_names(exc: RequestValidationError) -> list[str]:
    names: list[str] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        parts = [str(p) for p in loc[1:] if not isinstance(p, int)]
        if not parts:
            continue
        name = _UNSAFE_NAME_CHARS.sub("?", ".".join(parts))[:64]
        if name not in names:
            names.append(name)
    return names[:5]


async def _api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message),
        headers=exc.headers,
    )


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code, message = _HTTP_ERRORS.get(exc.status_code, ("HTTP_ERROR", "No se pudo procesar la solicitud."))
    headers: Optional[dict[str, str]] = getattr(exc, "headers", None)
    return JSONResponse(status_code=exc.status_code, content=error_body(code, message), headers=headers)


async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    names = _field_names(exc)
    if names:
        message = f"La solicitud no es válida. Corrige los campos: {', '.join(names)}."
    else:
        message = "El cuerpo de la solicitud no es válido o está vacío. Envía un JSON conforme al contrato."
    return JSONResponse(status_code=422, content=error_body("VALIDATION_ERROR", message))


async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    # La traza queda solo en el log del servidor; el cliente recibe un mensaje genérico.
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=error_body("INTERNAL_ERROR", "Ocurrió un error interno. Inténtalo de nuevo más tarde."),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(Exception, _unhandled_handler)
```

```python
# api/app/middleware.py
"""Middleware ASGI que limita el tamaño del cuerpo antes de que se parsee."""
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.errors import ApiError, error_body

_TOO_LARGE_MESSAGE = "El cuerpo de la solicitud supera el tamaño permitido. Envía menos datos."


class BodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 1) Comprobación temprana con Content-Length.
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                if not value.isdigit():
                    await self._respond(scope, receive, send, 400, "BAD_REQUEST", "La cabecera Content-Length no es válida.")
                    return
                if int(value) > self.max_bytes:
                    await self._respond(scope, receive, send, 413, "PAYLOAD_TOO_LARGE", _TOO_LARGE_MESSAGE)
                    return
                break

        # 2) Conteo real de bytes (cubre chunked o Content-Length falso).
        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise ApiError(413, "PAYLOAD_TOO_LARGE", _TOO_LARGE_MESSAGE)
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except ApiError as exc:
            if response_started:
                raise
            await self._respond(scope, receive, send, exc.status_code, exc.code, exc.message)

    @staticmethod
    async def _respond(scope: Scope, receive: Receive, send: Send, status: int, code: str, message: str) -> None:
        response = JSONResponse(status_code=status, content=error_body(code, message))
        await response(scope, receive, send)
```

```python
# api/app/schemas.py
"""Modelos Pydantic de entrada y salida. Fuente del contrato que el frontend debe espejar."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KycScenario(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"


class VerificationStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"


class KycDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class WalletStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    KYC_PENDING = "KYC_PENDING"
    KYC_FAILED = "KYC_FAILED"
    ACTIVE = "ACTIVE"


class StepStatus(str, Enum):
    COMPLETED = "COMPLETED"
    CURRENT = "CURRENT"
    LOCKED = "LOCKED"


# ---------- Requests (rechazan campos desconocidos, p. ej. un "owner" enviado por el cliente) ----------
class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class KycVerificationRequest(_StrictModel):
    document_number: str = Field(min_length=1, max_length=64)
    scenario: KycScenario


class KycDecisionRequest(_StrictModel):
    decision: KycDecision


class StepRequest(_StrictModel):
    document_number: Optional[str] = Field(default=None, min_length=1, max_length=64)


# ---------- Responses ----------
class ErrorResponse(BaseModel):
    code: str
    message: str


class HealthResponse(BaseModel):
    status: str


class ScenarioItem(BaseModel):
    name: KycScenario
    description: str


class ScenariosResponse(BaseModel):
    scenarios: list[ScenarioItem]


class SupportCase(BaseModel):
    verification_id: str
    status: VerificationStatus
    message: str


class SupportCasesResponse(BaseModel):
    cases: list[SupportCase]


class VerificationResponse(BaseModel):
    verification_id: str
    document_number: str
    scenario: KycScenario
    status: VerificationStatus
    created_at: datetime
    decided_at: Optional[datetime] = None


class StepInfo(BaseModel):
    id: str
    order: int
    status: StepStatus


class OnboardingStateResponse(BaseModel):
    wallet_status: WalletStatus
    current_step: Optional[str] = None
    steps: list[StepInfo]
    low_amount_payments_enabled: bool
    duration_seconds: Optional[float] = None


class ResetResponse(BaseModel):
    status: str


class MonthlyAnalyticsRow(BaseModel):
    month: str  # "YYYY-MM" en UTC
    new_active_users: int
    attributed_spend_cents: int


# Documentación OpenAPI de los errores comunes (todos con el formato único).
ERROR_RESPONSES: dict[int, dict] = {
    401: {"model": ErrorResponse, "description": "Sin identidad válida"},
    404: {"model": ErrorResponse, "description": "Recurso inexistente"},
    409: {"model": ErrorResponse, "description": "Conflicto de estado"},
    413: {"model": ErrorResponse, "description": "Cuerpo demasiado grande"},
    422: {"model": ErrorResponse, "description": "Entrada inválida"},
    500: {"model": ErrorResponse, "description": "Error interno"},
}
```

```python
# api/app/storage.py
"""Capa de acceso a archivos: directorio por hash SHA-256, locks por propietario y escritura atómica."""
import hashlib
import json
import logging
import os
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger("app.storage")

STATE_FILENAME = "state.json"
SCHEMA_VERSION = 1
_LOCK_STRIPES = 64
_REQUIRED_KEYS = ("started_at", "closed_at", "steps_completed", "verifications", "events", "spend")


class StorageError(Exception):
    """Fallo de lectura/escritura o estado corrupto. Se traduce a 500 INTERNAL_ERROR."""


def owner_key(owner_id: str) -> str:
    return hashlib.sha256(owner_id.encode("utf-8")).hexdigest()


def default_state() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "started_at": None,
        "closed_at": None,
        "steps_completed": [],
        "verifications": [],
        "events": [],
        "spend": [],
    }


def _parse_state(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except ValueError:
        raise StorageError("El estado almacenado no es JSON válido.") from None
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise StorageError("El estado almacenado tiene una versión o estructura desconocida.")
    if any(key not in data for key in _REQUIRED_KEYS):
        raise StorageError("El estado almacenado está incompleto.")
    return data


class OwnerStore:
    def __init__(self, data_dir: Path) -> None:
        self._root = Path(data_dir)
        # Locks por franjas: memoria acotada sin importar cuántos propietarios existan.
        self._locks = [threading.Lock() for _ in range(_LOCK_STRIPES)]

    @contextmanager
    def locked(self, owner_id: str) -> Iterator[None]:
        index = int(owner_key(owner_id)[:8], 16) % _LOCK_STRIPES
        with self._locks[index]:
            yield

    def _owner_dir(self, owner_id: str) -> Path:
        return self._root / owner_key(owner_id)

    def read(self, owner_id: str) -> dict[str, Any]:
        path = self._owner_dir(owner_id) / STATE_FILENAME
        try:
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return default_state()
        except OSError as exc:
            logger.error("Fallo de lectura de estado: %s", type(exc).__name__)
            raise StorageError("No se pudo leer el estado.") from None
        return _parse_state(raw)

    def write(self, owner_id: str, state: dict[str, Any]) -> None:
        directory = self._owner_dir(owner_id)
        tmp_name = None
        try:
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(dir=directory, prefix=".state-", suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(state, handle, ensure_ascii=False, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, directory / STATE_FILENAME)
            tmp_name = None
        except OSError as exc:
            logger.error("Fallo de escritura de estado: %s", type(exc).__name__)
            raise StorageError("No se pudo guardar el estado.") from None
        finally:
            if tmp_name is not None:
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass

    def delete(self, owner_id: str) -> None:
        path = self._owner_dir(owner_id) / STATE_FILENAME
        try:
            path.unlink()
        except FileNotFoundError:
            return
        except OSError as exc:
            logger.error("Fallo al borrar estado: %s", type(exc).__name__)
            raise StorageError("No se pudo reiniciar el estado.") from None

    def iter_states(self) -> Iterator[dict[str, Any]]:
        """Recorre los estados de todos los propietarios (solo para analítica). No expone el hash."""
        if not self._root.is_dir():
            return
        for entry in sorted(self._root.iterdir()):
            path = entry / STATE_FILENAME
            if not path.is_file():
                continue
            try:
                yield _parse_state(path.read_text(encoding="utf-8"))
            except (OSError, StorageError):
                logger.warning("Se omitió un estado ilegible durante la analítica.")
```

```python
# api/app/services.py
"""Lógica de negocio del onboarding y KYC, y dependencia de identidad get_current_owner."""
import re
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import Header

from app import config
from app.errors import ApiError
from app.schemas import (
    KycDecision,
    KycScenario,
    MonthlyAnalyticsRow,
    OnboardingStateResponse,
    ScenarioItem,
    ScenariosResponse,
    StepInfo,
    StepStatus,
    SupportCase,
    SupportCasesResponse,
    VerificationResponse,
    VerificationStatus,
    WalletStatus,
)
from app.storage import OwnerStore

STEP_ORDER: tuple[str, ...] = ("registro", "kyc", "activacion")
TEST_PREFIX = "TEST-"

EVENT_STARTED = "ONBOARDING_STARTED"
EVENT_STEP = "STEP_COMPLETED"
EVENT_CLOSED = "ONBOARDING_CLOSED"

_OWNER_RE = re.compile(config.OWNER_ID_PATTERN)
_DOCUMENT_SUFFIX_RE = re.compile(r"[A-Za-z0-9-]{1,59}")

_SCENARIO_STATUS: dict[KycScenario, VerificationStatus] = {
    KycScenario.APPROVED: VerificationStatus.APPROVED,
    KycScenario.REJECTED: VerificationStatus.REJECTED,
    KycScenario.PENDING: VerificationStatus.PENDING,
    KycScenario.EXPIRED: VerificationStatus.EXPIRED,
}

_SCENARIO_DESCRIPTIONS: dict[KycScenario, str] = {
    KycScenario.APPROVED: "La verificación se aprueba de inmediato.",
    KycScenario.REJECTED: "La verificación se rechaza de inmediato.",
    KycScenario.PENDING: "La verificación queda pendiente hasta que se registre una decisión.",
    KycScenario.EXPIRED: "La verificación expira sin resolverse.",
}

_SUPPORT_MESSAGES: dict[str, str] = {
    VerificationStatus.PENDING.value: "Verificación pendiente: registra una decisión en /kyc/verifications/{id}/decision.",
    VerificationStatus.REJECTED.value: "Verificación rechazada: crea una nueva con un documento TEST- válido.",
    VerificationStatus.EXPIRED.value: "Verificación expirada: crea una nueva verificación.",
}


def get_current_owner(
    x_owner_id: Optional[str] = Header(default=None, alias=config.OWNER_HEADER),
) -> str:
    """Identidad del usuario autenticado. Nunca se toma del cuerpo ni de la URL."""
    if x_owner_id is None or _OWNER_RE.fullmatch(x_owner_id) is None:
        raise ApiError(401, "UNAUTHENTICATED", "No se pudo identificar al usuario.")
    return x_owner_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def compute_duration_seconds(started_at: Optional[str], closed_at: Optional[str]) -> Optional[float]:
    if not started_at or not closed_at:
        return None
    delta = datetime.fromisoformat(closed_at) - datetime.fromisoformat(started_at)
    return round(delta.total_seconds(), 3)


def _validate_document(document_number: str) -> None:
    if not document_number.startswith(TEST_PREFIX):
        raise ApiError(
            422,
            "DOCUMENT_NOT_TEST",
            "El documento debe comenzar con 'TEST-' en este entorno de pruebas.",
        )
    if _DOCUMENT_SUFFIX_RE.fullmatch(document_number[len(TEST_PREFIX):]) is None:
        raise ApiError(
            422,
            "VALIDATION_ERROR",
            "Tras 'TEST-' usa de 1 a 59 caracteres: letras, números o guiones.",
        )


def _wallet_status(state: dict[str, Any]) -> WalletStatus:
    completed = state["steps_completed"]
    if STEP_ORDER[-1] in completed:
        return WalletStatus.ACTIVE
    latest = state["verifications"][-1] if state["verifications"] else None
    if "kyc" not in completed and latest is not None:
        if latest["status"] == VerificationStatus.PENDING.value:
            return WalletStatus.KYC_PENDING
        if latest["status"] in (VerificationStatus.REJECTED.value, VerificationStatus.EXPIRED.value):
            return WalletStatus.KYC_FAILED
    if not completed and latest is None:
        return WalletStatus.NOT_STARTED
    return WalletStatus.IN_PROGRESS


def _state_response(state: dict[str, Any]) -> OnboardingStateResponse:
    completed = state["steps_completed"]
    current = next((step for step in STEP_ORDER if step not in completed), None)
    steps: list[StepInfo] = []
    for order, step in enumerate(STEP_ORDER, start=1):
        if step in completed:
            status = StepStatus.COMPLETED
        elif step == current:
            status = StepStatus.CURRENT
        else:
            status = StepStatus.LOCKED
        steps.append(StepInfo(id=step, order=order, status=status))
    wallet_status = _wallet_status(state)
    return OnboardingStateResponse(
        wallet_status=wallet_status,
        current_step=current,
        steps=steps,
        low_amount_payments_enabled=wallet_status == WalletStatus.ACTIVE,
        duration_seconds=compute_duration_seconds(state["started_at"], state["closed_at"]),
    )


def _verification_response(record: dict[str, Any]) -> VerificationResponse:
    return VerificationResponse(**record)


def _find_verification(state: dict[str, Any], verification_id: str) -> dict[str, Any]:
    for record in state["verifications"]:
        if record["verification_id"] == verification_id:
            return record
    raise ApiError(404, "NOT_FOUND", "La verificación no existe.")


class OnboardingService:
    def __init__(self, store: OwnerStore, clock: Callable[[], datetime] = _utcnow) -> None:
        self._store = store
        self._clock = clock

    # ---------- Consola ----------
    @staticmethod
    def list_scenarios() -> ScenariosResponse:
        return ScenariosResponse(
            scenarios=[ScenarioItem(name=s, description=_SCENARIO_DESCRIPTIONS[s]) for s in KycScenario]
        )

    def list_support_cases(self, owner_id: str) -> SupportCasesResponse:
        with self._store.locked(owner_id):
            state = self._store.read(owner_id)
        cases = [
            SupportCase(
                verification_id=record["verification_id"],
                status=VerificationStatus(record["status"]),
                message=_SUPPORT_MESSAGES[record["status"]],
            )
            for record in state["verifications"]
            if record["status"] in _SUPPORT_MESSAGES
        ]
        return SupportCasesResponse(cases=cases)

    def reset(self, owner_id: str) -> None:
        with self._store.locked(owner_id):
            self._store.delete(owner_id)

    # ---------- KYC ----------
    def create_verification(
        self, owner_id: str, document_number: str, scenario: KycScenario
    ) -> VerificationResponse:
        _validate_document(document_number)  # antes de tocar disco
        with self._store.locked(owner_id):
            state = self._store.read(owner_id)
            if len(state["verifications"]) >= config.MAX_VERIFICATIONS_PER_OWNER:
                raise ApiError(
                    409,
                    "LIMIT_REACHED",
                    "Alcanzaste el máximo de verificaciones de prueba. Usa POST /control/reset para reiniciar.",
                )
            now = self._clock().isoformat()
            status = _SCENARIO_STATUS[scenario]
            record = {
                "verification_id": uuid.uuid4().hex,
                "document_number": document_number,
                "scenario": scenario.value,
                "status": status.value,
                "created_at": now,
                "decided_at": None if status == VerificationStatus.PENDING else now,
            }
            state["verifications"].append(record)
            self._store.write(owner_id, state)
            return _verification_response(record)

    def get_verification(self, owner_id: str, verification_id: str) -> VerificationResponse:
        with self._store.locked(owner_id):
            state = self._store.read(owner_id)
        return _verification_response(_find_verification(state, verification_id))

    def decide_verification(
        self, owner_id: str, verification_id: str, decision: KycDecision
    ) -> VerificationResponse:
        with self._store.locked(owner_id):
            state = self._store.read(owner_id)
            record = _find_verification(state, verification_id)
            if record["status"] != VerificationStatus.PENDING.value:
                raise ApiError(
                    409,
                    "VERIFICATION_NOT_PENDING",
                    "La verificación ya fue resuelta; solo se puede decidir sobre verificaciones en estado PENDING.",
                )
            record["status"] = decision.value
            record["decided_at"] = self._clock().isoformat()
            self._store.write(owner_id, state)
            return _verification_response(record)

    # ---------- Onboarding ----------
    def get_state(self, owner_id: str) -> OnboardingStateResponse:
        with self._store.locked(owner_id):
            state = self._store.read(owner_id)
        return _state_response(state)

    def submit_step(
        self, owner_id: str, step_id: str, document_number: Optional[str]
    ) -> OnboardingStateResponse:
        if step_id not in STEP_ORDER:
            raise ApiError(404, "NOT_FOUND", "El paso no existe. Pasos válidos: registro, kyc, activacion.")
        if step_id == "registro":
            if document_number is None:
                raise ApiError(
                    422,
                    "VALIDATION_ERROR",
                    "El paso 'registro' requiere 'document_number' con prefijo 'TEST-'.",
                )
            _validate_document(document_number)
        elif document_number is not None:
            raise ApiError(422, "VALIDATION_ERROR", "Este paso no admite datos en el cuerpo de la solicitud.")

        with self._store.locked(owner_id):
            state = self._store.read(owner_id)
            completed = state["steps_completed"]
            if step_id in completed:  # idempotente: sin eventos duplicados
                return _state_response(state)
            self._assert_not_blocked(step_id, state)

            now = self._clock().isoformat()
            if state["started_at"] is None:
                state["started_at"] = now
                state["events"].append({"type": EVENT_STARTED, "step": None, "at": now})
            completed.append(step_id)
            state["events"].append({"type": EVENT_STEP, "step": step_id, "at": now})
            if step_id == STEP_ORDER[-1]:
                state["closed_at"] = now
                state["events"].append({"type": EVENT_CLOSED, "step": None, "at": now})
            self._store.write(owner_id, state)
            return _state_response(state)

    @staticmethod
    def _assert_not_blocked(step_id: str, state: dict[str, Any]) -> None:
        index = STEP_ORDER.index(step_id)
        if index > 0 and STEP_ORDER[index - 1] not in state["steps_completed"]:
            raise ApiError(
                409,
                "STEP_BLOCKED",
                f"Completa el paso '{STEP_ORDER[index - 1]}' antes de continuar con '{step_id}'.",
            )
        if step_id != "kyc":
            return
        latest = state["verifications"][-1] if state["verifications"] else None
        if latest is None:
            raise ApiError(
                409,
                "STEP_BLOCKED",
                "Crea una verificación KYC (POST /kyc/verifications) antes de completar este paso.",
            )
        if latest["status"] == VerificationStatus.PENDING.value:
            raise ApiError(
                409,
                "STEP_BLOCKED",
                "Tu verificación KYC está pendiente. Espera la decisión y vuelve a intentarlo.",
            )
        if latest["status"] != VerificationStatus.APPROVED.value:
            raise ApiError(
                409,
                "STEP_BLOCKED",
                "Tu verificación KYC no fue aprobada. Crea una nueva verificación con un documento TEST- válido.",
            )

    # ---------- Analítica mensual (2.8) ----------
    def monthly_analytics(self) -> list[MonthlyAnalyticsRow]:
        buckets: dict[str, list[int]] = {}
        for state in self._store.iter_states():
            closed_at = state.get("closed_at")
            if not closed_at:
                continue
            month = datetime.fromisoformat(closed_at).astimezone(timezone.utc).strftime("%Y-%m")
            spend = sum(int(item["amount_cents"]) for item in state.get("spend", []))
            bucket = buckets.setdefault(month, [0, 0])
            bucket[0] += 1
            bucket[1] += spend
        return [
            MonthlyAnalyticsRow(month=month, new_active_users=values[0], attributed_spend_cents=values[1])
            for month, values in sorted(buckets.items())
        ]


@lru_cache(maxsize=1)
def get_onboarding_service() -> OnboardingService:
    return OnboardingService(OwnerStore(Path(config.DATA_DIR)))
```

```python
# api/app/routers/__init__.py
```

```python
# api/app/routers/console.py
from fastapi import APIRouter, Depends

from app.schemas import (
    ERROR_RESPONSES,
    HealthResponse,
    ResetResponse,
    ScenariosResponse,
    SupportCasesResponse,
)
from app.services import OnboardingService, get_current_owner, get_onboarding_service

router = APIRouter(tags=["console"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/scenarios", response_model=ScenariosResponse)
def scenarios(service: OnboardingService = Depends(get_onboarding_service)) -> ScenariosResponse:
    return service.list_scenarios()


@router.get("/support/cases", response_model=SupportCasesResponse, responses=ERROR_RESPONSES)
def support_cases(
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> SupportCasesResponse:
    return service.list_support_cases(owner_id)


@router.post("/control/reset", response_model=ResetResponse, responses=ERROR_RESPONSES)
def reset(
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> ResetResponse:
    service.reset(owner_id)
    return ResetResponse(status="reset")
```

```python
# api/app/routers/kyc.py
from fastapi import APIRouter, Depends, Path

from app.schemas import (
    ERROR_RESPONSES,
    KycDecisionRequest,
    KycVerificationRequest,
    VerificationResponse,
)
from app.services import OnboardingService, get_current_owner, get_onboarding_service

router = APIRouter(prefix="/kyc", tags=["kyc"])


@router.post(
    "/verifications",
    response_model=VerificationResponse,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def create_verification(
    body: KycVerificationRequest,
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> VerificationResponse:
    return service.create_verification(owner_id, body.document_number, body.scenario)


@router.get(
    "/verifications/{verification_id}",
    response_model=VerificationResponse,
    responses=ERROR_RESPONSES,
)
def get_verification(
    verification_id: str = Path(min_length=1, max_length=64),
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> VerificationResponse:
    return service.get_verification(owner_id, verification_id)


@router.post(
    "/verifications/{verification_id}/decision",
    response_model=VerificationResponse,
    responses=ERROR_RESPONSES,
)
def decide_verification(
    body: KycDecisionRequest,
    verification_id: str = Path(min_length=1, max_length=64),
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> VerificationResponse:
    return service.decide_verification(owner_id, verification_id, body.decision)
```

```python
# api/app/routers/onboarding.py
from typing import Optional

from fastapi import APIRouter, Depends, Path

from app.schemas import ERROR_RESPONSES, OnboardingStateResponse, StepRequest
from app.services import OnboardingService, get_current_owner, get_onboarding_service

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("", response_model=OnboardingStateResponse, responses=ERROR_RESPONSES)
def get_onboarding(
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStateResponse:
    return service.get_state(owner_id)


@router.post("/steps/{step_id}", response_model=OnboardingStateResponse, responses=ERROR_RESPONSES)
def submit_step(
    body: Optional[StepRequest] = None,
    step_id: str = Path(min_length=1, max_length=32),
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStateResponse:
    document_number = body.document_number if body is not None else None
    return service.submit_step(owner_id, step_id, document_number)
```

```python
# api/app/main.py
from fastapi import FastAPI

from app import config
from app.errors import register_exception_handlers
from app.middleware import BodyLimitMiddleware
from app.routers import console, kyc, onboarding


def create_app() -> FastAPI:
    application = FastAPI(title="Wallet Onboarding Mock API", version="0.1.0")
    application.add_middleware(BodyLimitMiddleware, max_bytes=config.MAX_BODY_BYTES)
    register_exception_handlers(application)
    application.include_router(console.router)
    application.include_router(kyc.router)
    application.include_router(onboarding.router)
    return application


app = create_app()
```

```text
# api/requirements.txt
fastapi==0.115.6
starlette==0.41.3
uvicorn==0.34.0
pydantic==2.10.4
```

---

# C. Verificación (TODO marcado NO EJECUTADO)

Ningún comando se ha ejecutado. La persona que verifica debe conservar la salida real.

**1. Instalación y comprobación de dependencias — NO EJECUTADO**

```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip check
pip freeze | grep -iE '^(fastapi|starlette|uvicorn|pydantic)=='
pip-audit -r requirements.txt   # requiere pip-audit instalado; confirma avisos de seguridad
```

**2. Levantar el servicio — NO EJECUTADO**

```bash
cd api
uvicorn app.main:app --reload
```

**3. Caso válido — NO EJECUTADO**

```bash
curl -i -X POST http://127.0.0.1:8000/kyc/verifications \
  -H "Content-Type: application/json" \
  -H "X-Owner-Id: demo-user-1" \
  -d '{"document_number":"TEST-0001","scenario":"APPROVED"}'
```

Resultado esperado (NO EJECUTADO): `HTTP/1.1 201 Created`. Cuerpo, con `verification_id` y las fechas variables:

```json
{"verification_id":"<uuid hex de 32 caracteres>","document_number":"TEST-0001","scenario":"APPROVED","status":"APPROVED","created_at":"<ISO-8601 UTC>","decided_at":"<ISO-8601 UTC>"}
```

**4. Caso de error: documento sin prefijo `TEST-` — NO EJECUTADO**

```bash
curl -i -X POST http://127.0.0.1:8000/kyc/verifications \
  -H "Content-Type: application/json" \
  -H "X-Owner-Id: demo-user-1" \
  -d '{"document_number":"12345678","scenario":"APPROVED"}'
```

Resultado esperado (NO EJECUTADO): `HTTP/1.1 422 Unprocessable Entity`

```json
{"code":"DOCUMENT_NOT_TEST","message":"El documento debe comenzar con 'TEST-' en este entorno de pruebas."}
```

**5. Errores adicionales de contrato — NO EJECUTADO**

Sin identidad. Esperado: 401 `{"code":"UNAUTHENTICATED","message":"No se pudo identificar al usuario."}`.

```bash
curl -i http://127.0.0.1:8000/onboarding
```

Paso bloqueado, con un propietario nuevo. Esperado: 409 `{"code":"STEP_BLOCKED","message":"Completa el paso 'registro' antes de continuar con 'kyc'."}`.

```bash
curl -i -X POST http://127.0.0.1:8000/onboarding/steps/kyc -H "X-Owner-Id: demo-user-2"
```

**6. Pruebas automatizadas — NO EJECUTADO**

```bash
python tools/lab.py test api
```

Este entregable no incluye pruebas (las escribe el rol de Pruebas). No se afirma que el código funcione hasta que estos comandos se ejecuten y se conserve su salida.