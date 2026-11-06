# api/tests/test_h01_requirements.py
"""Dependencias: pins con ==, starlette fijado, entorno coherente (Seguridad/Arquitecto S7).

La consulta a PyPI/OSV es un procedimiento manual obligatorio (ver testing_report.md §6,
paso 12); no se modela como prueba opcional.
"""
import re
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement

REQ = Path(__file__).resolve().parents[1] / "requirements.txt"
PIN = re.compile(r"^([A-Za-z0-9_.\-]+)==([A-Za-z0-9_.+!\-]+)$")


def _lines():
    assert REQ.is_file(), f"No existe {REQ}"
    out = []
    for raw in REQ.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            out.append(line)
    assert out, "requirements.txt no contiene requisitos"
    return out


def _pins():
    pins = {}
    for line in _lines():
        m = PIN.match(line)
        assert m, f"Requisito no fijado con '==': {line!r}"
        pins[m.group(1).lower().replace("_", "-")] = m.group(2)
    return pins


def test_todas_fijadas_con_igualdad():
    assert _pins()


def test_starlette_fijado():
    assert "starlette" in _pins(), "starlette debe fijarse con == de forma explícita"


def test_versiones_instaladas_coinciden():
    mismatches = []
    for name, version in _pins().items():
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            mismatches.append(f"{name}: no instalado (pin {version})")
            continue
        if installed != version:
            mismatches.append(f"{name}: instalado {installed}, pin {version}")
    assert not mismatches, "; ".join(mismatches)


def test_starlette_cumple_requisito_de_fastapi():
    starlette_version = metadata.version("starlette")
    requisitos = metadata.requires("fastapi") or []
    checked = False
    for raw in requisitos:
        req = Requirement(raw)
        if req.name.lower() == "starlette" and req.marker is None:
            checked = True
            assert req.specifier.contains(starlette_version, prereleases=True), (
                f"starlette {starlette_version} no cumple {req.specifier} de fastapi"
            )
    assert checked, "fastapi no declara Requires-Dist de starlette sin marcador"
