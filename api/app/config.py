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
