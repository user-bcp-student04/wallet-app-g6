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
