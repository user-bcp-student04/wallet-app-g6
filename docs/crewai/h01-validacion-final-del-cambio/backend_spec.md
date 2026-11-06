# backend_spec.md

## 1. Resumen de la solución

El Issue **[H01] Validación final del cambio** (tarea 4.1 del grupo 4 de `tasks.md`) consiste en ejecutar `python tools/verify.py` y registrar el resultado. No pide endpoints, servicios ni persistencia nuevos.

- **No se modifica la lógica del API.** No se inventan rutas, campos ni esquemas, porque el contenido de `spec.md` y el contrato de API no se recibieron.
- **Nada se ha ejecutado.** Este documento no declara ningún resultado de `verify.py`. El resultado lo registra la persona que lo ejecute, con la plantilla de la sección 9.
- **El código de la sección B es una base transversal opcional.** Contiene solo el formato único de error `{"code","message"}`, el límite de tamaño de cuerpo y la configuración. No añade endpoints. Aplícala únicamente si `api/app/` no tiene ya algo equivalente. Si el repositorio ya tiene esos archivos, **prevalecen los existentes** y no hay que sobrescribirlos.

## 2. Stack y estructura de archivos

Stack: Python con FastAPI (Starlette). No se usa Java, Quarkus ni Maven.

```text
api/
├── requirements.txt        (referencia; prevalece el manifiesto existente)
└── app/
    ├── main.py             crea la app y registra los handlers y el middleware
    ├── config.py           configuración desde variables de entorno
    ├── errors.py           formato único de error y exception_handlers
    └── middleware.py       límite de bytes del cuerpo (ASGI)
```

- `routers/`, `services.py`, `schemas.py` y `api/tests/` no se tocan ni se crean. No hay recurso que los requiera.
- `tools/verify.py` solo se ejecuta, no se edita.
- Cambio de documentación: la línea 4.1 de `openspec/changes/registro-activacion-wallet/tasks.md` y su nota de resultado.

## 3. Tabla de endpoints

| Método | Ruta | Entrada | Respuesta | Errores |
|---|---|---|---|---|
| — | — | — | — | — |

**Este Issue no define endpoints** y el contrato de `wallet-onboarding` no se aportó. Los únicos errores comunes del catálogo base son los que se describen en la sección 5.

## 4. Reglas de validación

- No hay campos de contrato que validar, porque no hay endpoints.
- Validación transversal de la base opcional:
  - Un `Content-Length` no numérico o negativo responde 400.
  - Un `Content-Length` o un cuerpo recibido mayor que `MAX_BODY_BYTES` responde 413, **antes** de que la aplicación parsee el cuerpo.
  - La validación de Pydantic y de `Query`/`Path`/`Form` de futuros endpoints se normaliza al formato único de error (422).
- Si la spec define subida de archivos, se aplicarían el saneado de nombres, la lista de MIME y extensiones, la lectura por bloques, la escritura temporal con `os.replace` y el aislamiento por hash SHA-256. Eso requiere el contrato y no está en este Issue.

## 5. Manejo de errores

Formato único: `{"code": "...", "message": "..."}`. Es el catálogo base del Arquitecto, marcado como supuesto.

| Situación | HTTP | `code` |
|---|---|---|
| Content-Length inválido | 400 | `BAD_REQUEST` |
| Sin identidad | 401 | `UNAUTHENTICATED` |
| Sin permiso | 403 | `FORBIDDEN` |
| Ruta o recurso inexistente | 404 | `NOT_FOUND` |
| Conflicto | 409 | `CONFLICT` |
| Cuerpo excede el tamaño | 413 | `PAYLOAD_TOO_LARGE` |
| Entrada inválida (Pydantic) | 422 | `INVALID_REQUEST` |
| Error inesperado | 500 | `INTERNAL_ERROR` |

- `HTTPException`, `RequestValidationError` y `Exception` tienen handler.
- Los errores 500 no devuelven trazas, rutas ni SQL, solo un mensaje genérico.
- El 422 devuelve únicamente la ubicación de los campos inválidos, sin el valor recibido.

## 6. Límites y archivos

- `MAX_BODY_BYTES` (variable de entorno, por defecto 1 048 576) está en `api/app/config.py`.
- Este límite es un supuesto conservador. El Issue no lo exige. Si la spec fija otro valor, se cambia el valor por defecto.
- No hay subida de archivos en este Issue. Por tanto no hay directorios por propietario, hash ni gestión de archivos preexistentes.
- Si la spec los introduce:
  - Identidad mediante `Depends`.
  - Directorio derivado de SHA-256.
  - Lock por propietario y `os.replace`.
  - Respuesta 409 ante archivos preexistentes.
  - Nada de hash ni ruta en las respuestas.

## 7. Origen de la persistencia

- No se asume base de datos ni almacenamiento nuevo.
- No hay contrato de Datos en el contexto.
- No se emite SQL: el Issue no usa base de datos.
- Si `wallet-onboarding` exige tablas, habrá que definirlas con el rol correspondiente (Datos, o este rol en un equipo de seis). Esa tarea sería otro Issue.

## 8. Recorrido de un caso válido y de un caso de error

**Caso válido (tarea 4.1).**
1. La persona ejecuta `python tools/verify.py` desde la raíz del repositorio.
2. El script realiza sus comprobaciones. Cuáles son es desconocido (P2).
3. Con código de salida 0 (supuesto S2) se marca 4.1 como `[x]` en `tasks.md` y se rellena la nota con la plantilla de la sección 9.

**Caso de error (tarea 4.1).** Si el código de salida es distinto de 0, la tarea **no** se marca como completada con éxito. Se registra el fallo (código de salida y salida relevante) y se abre trabajo correctivo aparte (S4).

**Caso de error de la base opcional.**
1. Petición `GET /ruta-inexistente`.
2. Starlette lanza `HTTPException(404)`.
3. `http_exception_handler` lo convierte en `{"code":"NOT_FOUND",...}` con estado 404.
4. No se toca disco ni base de datos.

## 9. Plantilla de registro de 4.1 (rellenar solo tras ejecutar)

```markdown
- [x] 4.1 Ejecutar `python tools/verify.py` y registrar el resultado
  - Fecha/hora: <AAAA-MM-DDThh:mm:ss±hh:mm>
  - Comando: `python tools/verify.py`
  - Versión de Python: <salida de `python --version`>
  - Código de salida: <n>
  - Resultado: <APROBADO | FALLIDO>
  - Resumen de la salida: <líneas relevantes o referencia al log>
```

## 10. Supuestos y pendientes

**Supuestos**
- **S1.** El Issue no modifica código ni dependencias. La base de la sección B es opcional y no cambia ningún contrato.
- **S2.** El código de salida 0 de `verify.py` significa éxito.
- **S3.** El resultado se registra en `tasks.md` con la plantilla.
- **S4.** Si `verify.py` falla, no se marca 4.1 como éxito y se abre trabajo aparte.
- **S5.** El catálogo de errores y los `code` vienen del Arquitecto y deben alinearse con los de las interfaces existentes. Se usa 422 para entrada inválida, como dice el Arquitecto, aunque la guía general mencione 400.
- **S6.** `MAX_BODY_BYTES` es un valor por defecto conservador, no un requisito del Issue.
- **S7.** Las versiones de `api/requirements.txt` son una referencia coherente entre sí (FastAPI 0.115.0 acepta starlette `>=0.37.2,<0.39.0`). **No se verificaron contra PyPI ni OSV** (sin ejecución). Si el repositorio ya tiene manifiesto, se conserva el existente. Este Issue no es una actualización de dependencias.
- **S8.** Documentos previos que mencionaran Java, Quarkus o Maven se ignoran. Manda el Issue: Python con FastAPI.

**Pendientes**
- **P1.** Falta el contenido de `spec.md`. Sin él no hay endpoints que implementar.
- **P2.** Falta saber qué comprueba `tools/verify.py` y qué necesita (argumentos, variables de entorno, servicios previos).
- **P3.** Se desconoce qué pruebas de `api/tests/` cubren los POST válidos. Es una brecha pendiente de aceptación humana.
- **P4.** Falta saber dónde registrar el resultado además de `tasks.md` (PR, CI, archivo de evidencia).
- **P5.** Falta saber si hay datos preexistentes que exijan migración.
- **P6.** Falta el mecanismo de identidad real (cabecera, token, sesión).
- **P7.** Falta saber si hay un límite de tamaño de cuerpo exigido.
- **P8.** Falta saber si un fallo de `verify.py` bloquea el cierre del cambio o abre un Issue nuevo.

---

# B. Código

```python
# api/app/config.py
"""Configuración leída de variables de entorno con valores por defecto."""
import os


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


# Tamaño máximo del cuerpo de una petición, en bytes (por defecto 1 MiB).
MAX_BODY_BYTES: int = _int_env("MAX_BODY_BYTES", 1_048_576)
```

```python
# api/app/errors.py
"""Formato único de error {"code", "message"} y handlers de excepciones."""
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")

_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    422: "INVALID_REQUEST",
}


def error_body(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def error_response(
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_body(code, message),
        headers=headers,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code = _CODES.get(exc.status_code, "ERROR")
    # Se usa un texto genérico por estado: no se reenvía detail arbitrario.
    messages: dict[int, str] = {
        400: "Solicitud incorrecta.",
        401: "Identidad no proporcionada.",
        403: "Acceso denegado.",
        404: "Recurso no encontrado.",
        405: "Método no permitido.",
        409: "Conflicto con el estado actual del recurso.",
        413: "El cuerpo excede el tamaño permitido.",
    }
    message = messages.get(exc.status_code, "Error en la solicitud.")
    headers: dict[str, str] | None = dict(exc.headers) if exc.headers else None
    return error_response(exc.status_code, code, message, headers)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Solo ubicaciones de campos: no se devuelven los valores recibidos.
    fields: list[str] = []
    errors: list[Any] = exc.errors()
    for err in errors:
        loc = ".".join(str(p) for p in err.get("loc", ()))
        if loc and loc not in fields:
            fields.append(loc)
    detail = f" Campos: {', '.join(fields)}." if fields else ""
    return error_response(
        422, "INVALID_REQUEST", "Entrada inválida." + detail
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    # Se registra solo el tipo de la excepción, sin trazas en la respuesta.
    logger.error("Error no controlado: %s", type(exc).__name__)
    return error_response(500, "INTERNAL_ERROR", "Error interno del servidor.")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
```

```python
# api/app/middleware.py
"""Middleware ASGI que limita los bytes del cuerpo antes de parsearlo."""
import json
from typing import Any, Awaitable, Callable, MutableMapping

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


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

        # 1) Content-Length declarado: rechazo inmediato.
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    await self._reject(
                        send, 400, "BAD_REQUEST", "Content-Length inválido."
                    )
                    return
                if declared < 0:
                    await self._reject(
                        send, 400, "BAD_REQUEST", "Content-Length inválido."
                    )
                    return
                if declared > self.max_bytes:
                    await self._reject(
                        send,
                        413,
                        "PAYLOAD_TOO_LARGE",
                        "El cuerpo excede el tamaño permitido.",
                    )
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
                    raise BodyTooLarge()
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except BodyTooLarge:
            if not response_started:
                await self._reject(
                    send,
                    413,
                    "PAYLOAD_TOO_LARGE",
                    "El cuerpo excede el tamaño permitido.",
                )

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

```python
# api/app/main.py
"""Crea la app FastAPI, registra el middleware y los handlers de error."""
from fastapi import FastAPI

from app.config import MAX_BODY_BYTES
from app.errors import register_error_handlers
from app.middleware import BodySizeLimitMiddleware

app = FastAPI(title="API")

app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_BODY_BYTES)
register_error_handlers(app)

# Los routers del contrato aprobado de wallet-onboarding se registrarían aquí
# con app.include_router(...). Este Issue no define endpoints.
```

```text
# api/requirements.txt
fastapi==0.115.0
starlette==0.38.6
uvicorn==0.30.6
pydantic==2.9.2
```

---

# C. Verificación (todo NO EJECUTADO)

Ningún comando se ha ejecutado. La persona que los ejecute debe conservar la salida.

**Caso válido (tarea 4.1): ejecutar la verificación final**

```bash
# NO EJECUTADO
python --version
python tools/verify.py; echo "exit=$?"
```

Resultado esperado: `exit=0` (supuesto S2). La salida concreta es desconocida (P2). **NO EJECUTADO.**

**Caso de error de la tarea 4.1: fallo de verify.py**

Si `exit` es distinto de 0, registrar `Resultado: FALLIDO`, no marcar 4.1 como éxito y abrir trabajo correctivo. **NO EJECUTADO.**

**Caso de error de la base opcional (solo si se aplicó la sección B)**

```bash
# NO EJECUTADO — levantar el servicio desde api/
cd api
uvicorn app.main:app --reload
```

```bash
# NO EJECUTADO — en otra terminal
curl -i -X GET http://127.0.0.1:8000/ruta-inexistente
```

Resultado esperado: HTTP 404 con cuerpo `{"code":"NOT_FOUND","message":"Recurso no encontrado."}`. **NO EJECUTADO.**

**Pruebas del repositorio**

```bash
# NO EJECUTADO
python tools/lab.py test api
```

Resultado: **NO EJECUTADO**. No se afirma cobertura ni resultados.

**Dependencias (solo si se adopta `api/requirements.txt` de referencia)**

```bash
# NO EJECUTADO
cd api
pip install -r requirements.txt
pip check
pip freeze | grep -i -E "^(fastapi|starlette|uvicorn|pydantic)=="
```

Resultado: **NO EJECUTADO**.