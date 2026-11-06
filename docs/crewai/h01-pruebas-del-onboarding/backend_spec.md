# backend_spec.md

## 1. Resumen de la solución

El Issue H01 pide pruebas del onboarding de la wallet (grupo 3 de `tasks.md`), no funcionalidad nueva. El plan de Arquitectura dice que no se modifica `api/app/`, y la suite de pruebas la escribe el rol de Pruebas. Aun así, este rol debe entregar el backend implementado. Para que los 8 endpoints sean verificables, entrego una implementación mínima en memoria del contrato conocido.

**Conflicto a resolver por una persona.** Si el repositorio ya tiene `api/app/` con estos endpoints, prevalece el código existente. En ese caso, este entregable solo sirve para contrastar nombres de campos y mensajes (ver sección 9). No dispongo de `spec.md`, `design.md` ni de los `schemas.py` reales. Todo campo no fijado por el Issue está marcado como supuesto.

El stack es Python y FastAPI (Starlette). No se usa Java, Quarkus ni Maven. No encontré en el contexto ningún documento que indique otro stack.

No entrego pruebas, porque son del rol de Pruebas. Tampoco ejecuté nada, así que no afirmo que el código funcione.

## 2. Stack y estructura de archivos

- Python con FastAPI 0.115.6, Starlette 0.41.3, Pydantic v2 y Uvicorn. Los pines están sin verificar contra PyPI/OSV (ver sección 9).
- Estado en memoria, sin base de datos y sin archivos.

```text
api/
├── requirements.txt
├── requirements-dev.txt
└── app/
    ├── __init__.py
    ├── main.py          # crea la app, middleware, handlers y routers
    ├── config.py        # configuración por variables de entorno
    ├── errors.py        # ApiError y handlers con formato {"code","message"}
    ├── middleware.py    # límite de tamaño de cuerpo (ASGI)
    ├── schemas.py       # modelos Pydantic de entrada y salida
    ├── repository.py    # acceso a datos (almacén en memoria)
    ├── services.py      # lógica de negocio
    └── routers/
        ├── __init__.py
        ├── health.py
        ├── scenarios.py
        ├── kyc.py
        ├── wallets.py
        ├── support.py
        └── control.py
```

## 3. Endpoints

Los códigos HTTP y los estados vienen del Issue. Los nombres de campos y de `code` no fijados por el Issue son supuestos (ver sección 9).

| Método | Ruta | Entrada | Respuesta | Errores |
|---|---|---|---|---|
| GET | `/health` | — | `200 {"status":"ok"}` | — |
| GET | `/scenarios` | — | `200` lista `[{"id","label"}]` | — |
| POST | `/kyc/verifications` | JSON `{"documentNumber": str, "scenario": APPROVED\|REJECTED\|MANUAL_REVIEW\|KYC_UNAVAILABLE}` | `201 {"id","status","decisionStatus","walletId","createdAt"}` | `400 BAD_REQUEST`, `413 PAYLOAD_TOO_LARGE`, `503 KYC_UNAVAILABLE` |
| GET | `/kyc/verifications/{id}` | `id` en la ruta | `200` mismo cuerpo que la creación | `400 BAD_REQUEST` (id con formato inválido), `404 NOT_FOUND` |
| POST | `/kyc/verifications/{id}/decision` | JSON `{"decision": APPROVED\|REJECTED}` | `200` verificación actualizada | `400`, `404`, `409 DECISION_CONFLICT`, `413` |
| GET | `/wallets/{id}` | `id` en la ruta | `200 {"id","balances":{"available":0,"pending":0}}` | `400`, `404 NOT_FOUND` |
| GET | `/support/cases` | — | `200` lista `[{"id","type":"KYC_REVIEW","status":"OPEN"\|"CLOSED","verificationId","createdAt"}]`, vacía si no hay casos | — |
| POST | `/control/reset` | — | `200 {"status":"reset"}` | `404 NOT_FOUND` si `ENABLE_CONTROL_RESET=false` |

**Modelo de estados (supuesto S-B1).** El Issue habla a la vez de `MANUAL_REVIEW` como resultado del POST y de `PENDING` como estado decidible. Para conciliarlo uso dos campos en la verificación:
- `status` es el resultado: `APPROVED`, `REJECTED` o `MANUAL_REVIEW`.
- `decisionStatus` es `PENDING` (solo con `MANUAL_REVIEW`), `DECIDED` o `NOT_REQUIRED`.

Solo se puede decidir cuando `decisionStatus == PENDING`. Cualquier otro caso devuelve `409 DECISION_CONFLICT`.

## 4. Reglas de validación (en el servidor)

- **`documentNumber`:** obligatorio, no nulo, se recortan espacios, longitud de 1 a 32 y solo `A-Za-z0-9-`.
  - El prefijo `TEST-` se bloquea en el cliente (P-4).
  - En el servidor solo se exige si `ENFORCE_TEST_DOC_PREFIX=true` (por defecto `false`), con `400 BAD_REQUEST`.
- **`scenario`:** obligatorio y debe ser uno de los 4 valores.
- **`decision`:** solo `APPROVED` o `REJECTED`. `MANUAL_REVIEW` o `PENDING` devuelven 400.
- **`{id}` en rutas:** patrón `^[A-Za-z0-9_-]{1,64}$`. Si no cumple, 400 antes de consultar el almacén. Si cumple pero no existe, 404.
- **Campos desconocidos en el cuerpo:** se ignoran (supuesto, para no romper al cliente real).
- **Tamaño del cuerpo:** máximo `MAX_BODY_BYTES` (por defecto 16384).
  - Se comprueba `Content-Length` antes de leer.
  - Si falta o es falso (chunked), se cuentan los bytes recibidos. Al superar el límite, 413.
  - Un `Content-Length` no numérico devuelve 400.
- No hay subida de archivos en este feature, así que no aplican nombres de archivo ni archivos temporales.

## 5. Manejo de errores

Todo error se devuelve como `{"code": "...", "message": "..."}`. No se incluyen trazas, rutas, SQL ni secretos.

| HTTP | `code` | Origen |
|---|---|---|
| 400 | `BAD_REQUEST` | `RequestValidationError` (convierte el 422 de FastAPI), reglas de negocio de entrada, `Content-Length` inválido |
| 404 | `NOT_FOUND` | recurso inexistente, ruta inexistente, reset deshabilitado |
| 405 | `METHOD_NOT_ALLOWED` | método no permitido |
| 409 | `DECISION_CONFLICT` | decisión sobre una verificación que no está `PENDING` (explícito en el Issue) |
| 413 | `PAYLOAD_TOO_LARGE` | cuerpo superior a `MAX_BODY_BYTES` |
| 429 | `RATE_LIMITED` | **ningún endpoint lo genera hoy**. El handler lo formatea si alguna capa lanza `HTTPException(429)` (P-5) |
| 503 | `KYC_UNAVAILABLE` | `scenario=KYC_UNAVAILABLE` en `POST /kyc/verifications` (explícito en el Issue) |
| 500 | `INTERNAL_ERROR` | cualquier excepción no controlada, con mensaje genérico. El detalle solo va al log del servidor |

Hay handlers registrados para `ApiError`, `HTTPException` (Starlette), `RequestValidationError` y `Exception`.

En el handler de `Exception`, Starlette responde 500 y luego vuelve a lanzar la excepción. Por eso, en pruebas, el `TestClient` debe crearse con `raise_server_exceptions=False` para ver el 500.

## 6. Límites, concurrencia y archivos

- **Límite de tamaño:** `MAX_BODY_BYTES` está definido en `api/app/config.py` y aplicado por `BodySizeLimitMiddleware` en `api/app/middleware.py`.
- **Archivos:** no hay escritura en disco, así que no hay archivos preexistentes que tratar.
- **Concurrencia:**
  - El almacén usa un `RLock`. La comprobación `PENDING` y el cambio de estado de una decisión son atómicos bajo ese lock. Dos decisiones simultáneas sobre la misma verificación dan un `200` y un `409`.
  - Los identificadores son únicos (uuid4), así que dos POST simultáneos no colisionan.
- **Reglas fuera del feature:**
  - No hay identidad ni propietario en el Issue, así que no se implementa autenticación ni aislamiento por hash (supuesto S-3 de Arquitectura). Si se añadiera, la identidad vendría de una dependencia `Depends`, nunca del cuerpo.
  - No se devuelven valores derivados de propietario.

## 7. Persistencia

- **Origen:** almacén en memoria (`api/app/repository.py`), consistente con que `POST /control/reset` limpia el estado. No hay contrato de Datos en el contexto.
- **SQL:** el Issue no usa base de datos, por eso no emito SQL ni migración.
- **Reinicio:** el estado se pierde al reiniciar el proceso, y esto es intencional.

## 8. Recorrido de casos

**Caso válido: `POST /kyc/verifications` con `scenario=MANUAL_REVIEW`**
1. Entra a `BodySizeLimitMiddleware`: `Content-Length` es menor que el límite, así que continúa.
2. Pydantic valida `documentNumber` y `scenario`.
3. El router delega en `services.create_verification`.
4. El servicio, con el lock tomado, crea el registro con `status=MANUAL_REVIEW` y `decisionStatus=PENDING`. También crea el caso `KYC_REVIEW` en `OPEN` en el almacén.
5. Responde `201` con el `VerificationOut`.
6. Luego `POST .../decision` con `{"decision":"APPROVED"}` devuelve `200`, crea la wallet con saldos 0 y cierra el caso.

**Caso de error: `POST /kyc/verifications` con `scenario=KYC_UNAVAILABLE`**
1. Pasa el middleware y la validación.
2. `services.create_verification` lanza `ApiError(503, "KYC_UNAVAILABLE", ...)` antes de escribir nada en el almacén.
3. `api_error_handler` responde `503 {"code":"KYC_UNAVAILABLE","message":"..."}`.

## 9. Supuestos y pendientes

| # | Tema | Detalle |
|---|---|---|
| A-1 | Código ya existente | Conflicto entre "no cambiar `api/app/`" (Arquitectura) y entregar código (este rol). Si ya existe, prevalece lo existente. |
| A-2 | Campos (P-3) | `documentNumber`, `scenario`, `decision` y los nombres de salida (`status`, `decisionStatus`, `walletId`, `balances`, `verificationId`) son supuestos. Se resuelven contra `design.md` / `schemas.py` reales. |
| A-3 | Cómo provocar resultados | Se elige con `scenario`. `KYC_UNAVAILABLE` se ofrece en `/scenarios` para provocar el 503. Pendiente de confirmar. |
| A-4 | `PENDING` frente a `MANUAL_REVIEW` | Ver S-B1 en la sección 3. |
| A-5 | `code` propuestos | `BAD_REQUEST`, `NOT_FOUND`, `PAYLOAD_TOO_LARGE`, `RATE_LIMITED` y los demás no dados por el Issue deben confirmarse con `design.md`. |
| A-6 | 429 (P-5) | Sin endpoint que lo produzca. No implementé limitador de tasa porque el Issue no lo define. |
| A-7 | Latencia en `/health` | La "latencia inválida" se bloquea en el cliente, así que `/health` no recibe parámetros. |
| A-8 | Frontend | Las tareas 3.1 (latencia), 3.2 (error de red), 3.3 (`TEST-`), 3.8 (confirmación), 3.10 y 3.11 son del cliente Angular y quedan fuera de este entregable. |
| A-9 | `/control/reset` | Se pueden desactivar con `ENABLE_CONTROL_RESET=false`. Por defecto activo, por ser entorno de laboratorio. Su política en producción es pendiente. |
| A-10 | Saldos | Enteros en unidad mínima, supuesto. |
| A-11 | Dependencias (bloqueo parcial) | El Issue no es una actualización de dependencias, y P-9 indica que no hay versiones decididas por Arquitectura. Los pines de `requirements.txt` son exactos pero **no verificados** contra PyPI/OSV. Con la fecha actual pueden existir versiones más nuevas y avisos de seguridad para `starlette`/`fastapi`. Si el repo ya tiene manifiesto, prevalece. Arquitectura/Seguridad deben confirmarlos antes de fusionar. `pytest` y `httpx` van en `requirements-dev.txt` (P-9). |
| A-12 | 3.12 | La salida real de las pruebas la adjunta una persona al PR. No fabrico salidas. |

# Código

```python
# api/app/__init__.py
"""Paquete de la API de onboarding de wallet."""
```

```python
# api/app/config.py
"""Configuración leída de variables de entorno, con valores por defecto."""
import os


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= minimum else default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# Tamaño máximo del cuerpo de una petición (bytes). Contrato: rechazar con 413.
MAX_BODY_BYTES: int = _int_env("MAX_BODY_BYTES", 16384)

# Longitud máxima del número de documento.
DOCUMENT_MAX_LENGTH: int = _int_env("DOCUMENT_MAX_LENGTH", 32)

# Patrón de los identificadores de recurso en rutas.
RESOURCE_ID_PATTERN: str = r"^[A-Za-z0-9_-]{1,64}$"

# Si es true, el servidor exige el prefijo TEST- en el documento (P-4: por defecto solo cliente).
ENFORCE_TEST_DOC_PREFIX: bool = _bool_env("ENFORCE_TEST_DOC_PREFIX", False)

# Permite desactivar POST /control/reset fuera del laboratorio.
ENABLE_CONTROL_RESET: bool = _bool_env("ENABLE_CONTROL_RESET", True)
```

```python
# api/app/errors.py
"""Formato único de error {"code","message"} y handlers de excepciones."""
import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")

STATUS_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    429: "RATE_LIMITED",
    503: "SERVICE_UNAVAILABLE",
}

STATUS_MESSAGES: dict[int, str] = {
    400: "La solicitud no es válida. Revise los datos enviados e intente de nuevo.",
    401: "Se requiere autenticación para esta operación.",
    403: "No tiene permisos para esta operación.",
    404: "El recurso solicitado no existe.",
    405: "El método no está permitido para esta ruta.",
    409: "La operación entra en conflicto con el estado actual del recurso.",
    413: "El cuerpo de la solicitud es demasiado grande. Reduzca su tamaño e intente de nuevo.",
    429: "Demasiadas solicitudes. Espere unos segundos e intente de nuevo.",
    503: "El servicio no está disponible. Intente de nuevo más tarde.",
}


class ApiError(Exception):
    """Error de negocio con código HTTP y código de error del contrato."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def error_response(
    status_code: int,
    code: str,
    message: str,
    headers: Optional[dict[str, str]] = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message},
        headers=headers,
    )


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    # Se ignora exc.detail para no filtrar texto interno; el mensaje es fijo por código HTTP.
    code = STATUS_CODES.get(exc.status_code, "HTTP_ERROR")
    message = STATUS_MESSAGES.get(
        exc.status_code, "No se pudo completar la solicitud."
    )
    headers = dict(exc.headers) if exc.headers else None
    return error_response(exc.status_code, code, message, headers)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    fields: set[str] = set()
    for error in exc.errors():
        parts = [str(p) for p in error.get("loc", ()) if p not in ("body", "query", "path")]
        if parts:
            fields.add(".".join(parts))
    detail = f" Campos: {', '.join(sorted(fields))}." if fields else ""
    return error_response(
        400,
        "BAD_REQUEST",
        "La solicitud no es válida. Revise los datos enviados e intente de nuevo." + detail,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # La traza solo va al log del servidor, nunca al cliente.
    logger.error(
        "Error no controlado en %s %s", request.method, request.url.path, exc_info=exc
    )
    return error_response(
        500,
        "INTERNAL_ERROR",
        "Ocurrió un error interno. Intente de nuevo más tarde.",
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, api_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
```

```python
# api/app/middleware.py
"""Middleware ASGI que limita el tamaño del cuerpo antes de que se parsee."""
from fastapi import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .errors import STATUS_MESSAGES, error_response


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = None
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    declared = -1
                break

        if declared is not None and declared < 0:
            response = error_response(400, "BAD_REQUEST", STATUS_MESSAGES[400])
            await response(scope, receive, send)
            return
        if declared is not None and declared > self.max_bytes:
            response = error_response(413, "PAYLOAD_TOO_LARGE", STATUS_MESSAGES[413])
            await response(scope, receive, send)
            return

        received = 0
        max_bytes = self.max_bytes

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > max_bytes:
                    # HTTPException atraviesa el parseo de FastAPI y sale como 413 con el formato común.
                    raise HTTPException(status_code=413)
            return message

        await self.app(scope, limited_receive, send)
```

```python
# api/app/schemas.py
"""Modelos Pydantic de entrada y salida. No exponen estructuras internas."""
from datetime import datetime
from typing import Annotated, Literal, Optional

from fastapi import Path
from pydantic import BaseModel, ConfigDict, StringConstraints

from . import config

Scenario = Literal["APPROVED", "REJECTED", "MANUAL_REVIEW", "KYC_UNAVAILABLE"]
VerificationStatus = Literal["APPROVED", "REJECTED", "MANUAL_REVIEW"]
DecisionStatus = Literal["PENDING", "DECIDED", "NOT_REQUIRED"]

DocumentNumber = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=config.DOCUMENT_MAX_LENGTH,
        pattern=r"^[A-Za-z0-9-]+$",
    ),
]

ResourceId = Annotated[str, Path(pattern=config.RESOURCE_ID_PATTERN)]


class VerificationCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    documentNumber: DocumentNumber
    scenario: Scenario


class DecisionIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    decision: Literal["APPROVED", "REJECTED"]


class VerificationOut(BaseModel):
    id: str
    status: VerificationStatus
    decisionStatus: DecisionStatus
    walletId: Optional[str] = None
    createdAt: datetime


class Balances(BaseModel):
    available: int
    pending: int


class WalletOut(BaseModel):
    id: str
    balances: Balances


class SupportCaseOut(BaseModel):
    id: str
    type: Literal["KYC_REVIEW"]
    status: Literal["OPEN", "CLOSED"]
    verificationId: str
    createdAt: datetime


class ScenarioOut(BaseModel):
    id: Scenario
    label: str


class HealthOut(BaseModel):
    status: Literal["ok"]


class ResetOut(BaseModel):
    status: Literal["reset"]


class ErrorOut(BaseModel):
    code: str
    message: str
```

```python
# api/app/repository.py
"""Acceso a datos: almacén en memoria con bloqueo para operaciones atómicas."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class VerificationRecord:
    id: str
    status: str
    decision_status: str
    wallet_id: str | None
    created_at: datetime


@dataclass
class WalletRecord:
    id: str
    available: int
    pending: int


@dataclass
class CaseRecord:
    id: str
    type: str
    status: str
    verification_id: str
    created_at: datetime


class InMemoryStore:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.verifications: dict[str, VerificationRecord] = {}
        self.wallets: dict[str, WalletRecord] = {}
        self.cases: dict[str, CaseRecord] = {}

    def reset(self) -> None:
        with self.lock:
            self.verifications.clear()
            self.wallets.clear()
            self.cases.clear()


_store = InMemoryStore()


def get_store() -> InMemoryStore:
    return _store
```

```python
# api/app/services.py
"""Lógica de negocio del onboarding de wallet."""
import dataclasses
from datetime import datetime, timezone
from uuid import uuid4

from . import config
from .errors import ApiError
from .repository import (
    CaseRecord,
    InMemoryStore,
    VerificationRecord,
    WalletRecord,
)
from .schemas import (
    Balances,
    ScenarioOut,
    SupportCaseOut,
    VerificationCreate,
    VerificationOut,
    WalletOut,
)

SCENARIOS: list[ScenarioOut] = [
    ScenarioOut(id="APPROVED", label="Verificación aprobada"),
    ScenarioOut(id="REJECTED", label="Verificación rechazada"),
    ScenarioOut(id="MANUAL_REVIEW", label="Revisión manual"),
    ScenarioOut(id="KYC_UNAVAILABLE", label="Servicio KYC no disponible"),
]


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_verification_out(record: VerificationRecord) -> VerificationOut:
    return VerificationOut(
        id=record.id,
        status=record.status,  # type: ignore[arg-type]
        decisionStatus=record.decision_status,  # type: ignore[arg-type]
        walletId=record.wallet_id,
        createdAt=record.created_at,
    )


def _open_wallet(store: InMemoryStore) -> str:
    wallet = WalletRecord(id=_new_id("wlt"), available=0, pending=0)
    store.wallets[wallet.id] = wallet
    return wallet.id


def list_scenarios() -> list[ScenarioOut]:
    return list(SCENARIOS)


def create_verification(
    store: InMemoryStore, payload: VerificationCreate
) -> VerificationOut:
    if config.ENFORCE_TEST_DOC_PREFIX and not payload.documentNumber.startswith("TEST-"):
        raise ApiError(
            400, "BAD_REQUEST", "El documento de prueba debe comenzar con TEST-."
        )
    if payload.scenario == "KYC_UNAVAILABLE":
        raise ApiError(
            503,
            "KYC_UNAVAILABLE",
            "El servicio de verificación no está disponible. Intente de nuevo más tarde.",
        )

    with store.lock:
        record = VerificationRecord(
            id=_new_id("ver"),
            status=payload.scenario,
            decision_status="PENDING" if payload.scenario == "MANUAL_REVIEW" else "NOT_REQUIRED",
            wallet_id=None,
            created_at=_now(),
        )
        if payload.scenario == "APPROVED":
            record.wallet_id = _open_wallet(store)
        if payload.scenario == "MANUAL_REVIEW":
            case = CaseRecord(
                id=_new_id("case"),
                type="KYC_REVIEW",
                status="OPEN",
                verification_id=record.id,
                created_at=record.created_at,
            )
            store.cases[case.id] = case
        store.verifications[record.id] = record
        return _to_verification_out(dataclasses.replace(record))


def get_verification(store: InMemoryStore, verification_id: str) -> VerificationOut:
    with store.lock:
        record = store.verifications.get(verification_id)
        if record is None:
            raise ApiError(404, "NOT_FOUND", "La verificación solicitada no existe.")
        return _to_verification_out(dataclasses.replace(record))


def decide_verification(
    store: InMemoryStore, verification_id: str, decision: str
) -> VerificationOut:
    # Comprobación de PENDING y cambio de estado dentro del mismo lock (atómico).
    with store.lock:
        record = store.verifications.get(verification_id)
        if record is None:
            raise ApiError(404, "NOT_FOUND", "La verificación solicitada no existe.")
        if record.decision_status != "PENDING":
            raise ApiError(
                409,
                "DECISION_CONFLICT",
                "La verificación ya fue decidida y no puede modificarse.",
            )
        record.status = decision
        record.decision_status = "DECIDED"
        if decision == "APPROVED":
            record.wallet_id = _open_wallet(store)
        for case in store.cases.values():
            if case.verification_id == record.id:
                case.status = "CLOSED"
        return _to_verification_out(dataclasses.replace(record))


def get_wallet(store: InMemoryStore, wallet_id: str) -> WalletOut:
    with store.lock:
        wallet = store.wallets.get(wallet_id)
        if wallet is None:
            raise ApiError(404, "NOT_FOUND", "La wallet solicitada no existe.")
        return WalletOut(
            id=wallet.id,
            balances=Balances(available=wallet.available, pending=wallet.pending),
        )


def list_support_cases(store: InMemoryStore) -> list[SupportCaseOut]:
    with store.lock:
        cases = sorted(store.cases.values(), key=lambda c: c.created_at)
        return [
            SupportCaseOut(
                id=c.id,
                type=c.type,  # type: ignore[arg-type]
                status=c.status,  # type: ignore[arg-type]
                verificationId=c.verification_id,
                createdAt=c.created_at,
            )
            for c in cases
        ]


def reset_state(store: InMemoryStore) -> None:
    if not config.ENABLE_CONTROL_RESET:
        raise ApiError(404, "NOT_FOUND", "El recurso solicitado no existe.")
    store.reset()
```

```python
# api/app/routers/__init__.py
"""Routers de la API."""
```

```python
# api/app/routers/health.py
from fastapi import APIRouter

from ..schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(status="ok")
```

```python
# api/app/routers/scenarios.py
from fastapi import APIRouter

from .. import services
from ..schemas import ScenarioOut

router = APIRouter(tags=["scenarios"])


@router.get("/scenarios", response_model=list[ScenarioOut])
def list_scenarios() -> list[ScenarioOut]:
    return services.list_scenarios()
```

```python
# api/app/routers/kyc.py
from fastapi import APIRouter, Depends

from .. import services
from ..repository import InMemoryStore, get_store
from ..schemas import (
    DecisionIn,
    ErrorOut,
    ResourceId,
    VerificationCreate,
    VerificationOut,
)

router = APIRouter(prefix="/kyc/verifications", tags=["kyc"])


@router.post(
    "",
    response_model=VerificationOut,
    status_code=201,
    responses={400: {"model": ErrorOut}, 413: {"model": ErrorOut}, 503: {"model": ErrorOut}},
)
def create_verification(
    payload: VerificationCreate, store: InMemoryStore = Depends(get_store)
) -> VerificationOut:
    return services.create_verification(store, payload)


@router.get(
    "/{verification_id}",
    response_model=VerificationOut,
    responses={400: {"model": ErrorOut}, 404: {"model": ErrorOut}},
)
def get_verification(
    verification_id: ResourceId, store: InMemoryStore = Depends(get_store)
) -> VerificationOut:
    return services.get_verification(store, verification_id)


@router.post(
    "/{verification_id}/decision",
    response_model=VerificationOut,
    responses={
        400: {"model": ErrorOut},
        404: {"model": ErrorOut},
        409: {"model": ErrorOut},
        413: {"model": ErrorOut},
    },
)
def decide_verification(
    verification_id: ResourceId,
    payload: DecisionIn,
    store: InMemoryStore = Depends(get_store),
) -> VerificationOut:
    return services.decide_verification(store, verification_id, payload.decision)
```

```python
# api/app/routers/wallets.py
from fastapi import APIRouter, Depends

from .. import services
from ..repository import InMemoryStore, get_store
from ..schemas import ErrorOut, ResourceId, WalletOut

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.get(
    "/{wallet_id}",
    response_model=WalletOut,
    responses={400: {"model": ErrorOut}, 404: {"model": ErrorOut}},
)
def get_wallet(
    wallet_id: ResourceId, store: InMemoryStore = Depends(get_store)
) -> WalletOut:
    return services.get_wallet(store, wallet_id)
```

```python
# api/app/routers/support.py
from fastapi import APIRouter, Depends

from .. import services
from ..repository import InMemoryStore, get_store
from ..schemas import SupportCaseOut

router = APIRouter(prefix="/support", tags=["support"])


@router.get("/cases", response_model=list[SupportCaseOut])
def list_cases(store: InMemoryStore = Depends(get_store)) -> list[SupportCaseOut]:
    return services.list_support_cases(store)
```

```python
# api/app/routers/control.py
from fastapi import APIRouter, Depends

from .. import services
from ..repository import InMemoryStore, get_store
from ..schemas import ErrorOut, ResetOut

router = APIRouter(prefix="/control", tags=["control"])


@router.post("/reset", response_model=ResetOut, responses={404: {"model": ErrorOut}})
def reset(store: InMemoryStore = Depends(get_store)) -> ResetOut:
    services.reset_state(store)
    return ResetOut(status="reset")
```

```python
# api/app/main.py
"""Crea la app FastAPI, registra middleware, handlers de error y routers."""
from fastapi import FastAPI

from . import config
from .errors import register_error_handlers
from .middleware import BodySizeLimitMiddleware
from .routers import control, health, kyc, scenarios, support, wallets

app = FastAPI(title="Wallet onboarding API", version="0.1.0")

app.add_middleware(BodySizeLimitMiddleware, max_bytes=config.MAX_BODY_BYTES)
register_error_handlers(app)

app.include_router(health.router)
app.include_router(scenarios.router)
app.include_router(kyc.router)
app.include_router(wallets.router)
app.include_router(support.router)
app.include_router(control.router)
```

```text
# api/requirements.txt
fastapi==0.115.6
starlette==0.41.3
pydantic==2.10.3
uvicorn==0.34.0
```

```text
# api/requirements-dev.txt
-r requirements.txt
pytest==8.3.4
httpx==0.28.1
```

# C. Verificación

**Todo lo siguiente está NO EJECUTADO. La persona responsable debe ejecutarlo y conservar la salida real.**

Instalación y comprobación de dependencias (NO EJECUTADO):

```bash
cd api
pip install -r requirements-dev.txt
pip check
pip freeze | grep -iE "^(fastapi|starlette|pydantic|uvicorn|httpx|pytest)=="
```

Levantar el servicio (NO EJECUTADO):

```bash
cd api
uvicorn app.main:app --reload
```

**Caso válido (NO EJECUTADO).** Crear una verificación aprobada:

```bash
curl -i -X POST http://127.0.0.1:8000/kyc/verifications \
  -H "Content-Type: application/json" \
  -d '{"documentNumber":"TEST-0001","scenario":"APPROVED"}'
```

Resultado esperado, sin ejecutar:
- Estado `HTTP/1.1 201 Created`.
- Cuerpo con esta forma: `{"id":"ver_<16 hex>","status":"APPROVED","decisionStatus":"NOT_REQUIRED","walletId":"wlt_<16 hex>","createdAt":"<fecha ISO UTC>"}`.
- Los valores de `id`, `walletId` y `createdAt` varían en cada ejecución.

**Caso de error (NO EJECUTADO).** Servicio KYC no disponible:

```bash
curl -i -X POST http://127.0.0.1:8000/kyc/verifications \
  -H "Content-Type: application/json" \
  -d '{"documentNumber":"TEST-0002","scenario":"KYC_UNAVAILABLE"}'
```

Resultado esperado, sin ejecutar:
- Estado `HTTP/1.1 503 Service Unavailable`.
- Cuerpo `{"code":"KYC_UNAVAILABLE","message":"El servicio de verificación no está disponible. Intente de nuevo más tarde."}`.

Pruebas de la suite, escritas por el rol de Pruebas (NO EJECUTADO):

```bash
python tools/lab.py test api
```

Resultado esperado, sin ejecutar: la salida real de esta ejecución debe adjuntarse al PR por una persona (tarea 3.12). No se declara ninguna cobertura ni resultado.