# api/tests/h01/test_h01_requirements.py
"""Dependencias: pines exactos (paquete==versión), incluido starlette. Obligatorio, sin red."""
import re
from pathlib import Path

import pytest

REQUIREMENTS = Path(__file__).resolve().parents[2] / "requirements.txt"
PAQUETES_CLAVE = ("fastapi", "starlette", "uvicorn", "pydantic")


def _lineas() -> list:
    texto = REQUIREMENTS.read_text(encoding="utf-8")
    return [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith("#")]


def _nombre(linea: str) -> str:
    return re.split(r"[\[=<>!~;\s]", linea, maxsplit=1)[0].lower()


def test_requirements_existe_y_tiene_contenido():
    assert REQUIREMENTS.is_file(), f"No existe {REQUIREMENTS}"
    assert _lineas(), "requirements.txt está vacío"


@pytest.mark.parametrize("paquete", PAQUETES_CLAVE)
def test_paquetes_clave_con_pin_exacto(paquete):
    coincidencias = [l for l in _lineas() if _nombre(l) == paquete]
    assert len(coincidencias) == 1, f"{paquete}: se esperaba exactamente una línea, hay {coincidencias}"
    assert re.search(r"==\s*\d+(\.\d+)*", coincidencias[0]), f"{paquete} no está fijado con ==: {coincidencias[0]}"


def test_ninguna_linea_usa_rangos():
    opciones = [l for l in _lineas() if not l.startswith("-")]
    prohibidos = (">=", "<=", "~=", "!=", ">", "<", "^", "*")
    malas = [l for l in opciones if "==" not in l or any(p in l for p in prohibidos)]
    assert malas == [], f"Líneas sin pin exacto: {malas}"
