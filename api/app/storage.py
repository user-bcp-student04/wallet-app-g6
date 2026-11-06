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
