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
