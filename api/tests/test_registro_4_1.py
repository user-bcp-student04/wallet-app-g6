# openspec/changes/registro-activacion-wallet/tests/test_registro_4_1.py
"""Fase 2 (cambio): valida el registro de la tarea 4.1 en tasks.md.

Se ejecuta explícitamente DESPUÉS de ejecutar tools/verify.py y registrar el
resultado. Está fuera de api/tests/ para no contaminar la línea base (ST7).
"""
import re
from datetime import datetime
from pathlib import Path

import pytest


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "tools" / "verify.py").is_file():
            return parent
    raise AssertionError("No se encontró la raíz del repo (tools/verify.py)")


TASKS = (
    _repo_root()
    / "openspec"
    / "changes"
    / "registro-activacion-wallet"
    / "tasks.md"
)

LINEA = re.compile(
    r"^- \[(?P<mark>[ xX])\] 4\.1 Ejecutar `python tools/verify\.py` "
    r"y registrar el resultado\s*$"
)
CAMPO = re.compile(
    r"^- (Fecha/hora|Comando|Versión de Python|Código de salida|Resultado|"
    r"Resumen de la salida):\s*(.*)$"
)
CAMPOS = [
    "Fecha/hora",
    "Comando",
    "Versión de Python",
    "Código de salida",
    "Resultado",
    "Resumen de la salida",
]


def _leer_registro():
    assert TASKS.is_file(), f"No existe {TASKS}"
    lines = TASKS.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        m = LINEA.match(line)
        if not m:
            continue
        note = []
        for nxt in lines[i + 1:]:
            if nxt.startswith("  ") and nxt.strip():
                note.append(nxt.strip())
            else:
                break
        fields = {}
        for n in note:
            c = CAMPO.match(n)
            if c:
                fields[c.group(1)] = c.group(2).strip()
        return m.group("mark"), fields
    raise AssertionError("No se encontró la línea de la tarea 4.1 en tasks.md")


@pytest.fixture(scope="module")
def registro():
    return _leer_registro()


def test_campos_obligatorios_presentes(registro):
    _, fields = registro
    faltan = [c for c in CAMPOS if c not in fields]
    assert not faltan, f"Faltan campos en el registro de 4.1: {faltan}"


def test_sin_placeholders(registro):
    _, fields = registro
    con_placeholder = {
        k: v for k, v in fields.items() if re.search(r"<[^>]+>", v)
    }
    assert not con_placeholder, f"Quedan placeholders sin rellenar: {con_placeholder}"


def test_fecha_hora_iso_con_offset(registro):
    _, fields = registro
    value = fields["Fecha/hora"].strip("`")
    assert re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)$", value
    ), f"Formato de fecha/hora inválido: {value!r}"
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_comando_es_verify(registro):
    _, fields = registro
    assert fields["Comando"].strip("`") == "python tools/verify.py"


def test_version_python(registro):
    _, fields = registro
    assert re.match(r"^`?Python \d+\.\d+\.\d+\S*`?$", fields["Versión de Python"]), (
        f"Versión de Python inválida: {fields['Versión de Python']!r}"
    )


def test_codigo_salida_entero(registro):
    _, fields = registro
    assert re.match(r"^`?-?\d+`?$", fields["Código de salida"]), (
        f"Código de salida no numérico: {fields['Código de salida']!r}"
    )


def test_resultado_valido(registro):
    _, fields = registro
    assert fields["Resultado"].strip("`") in {"APROBADO", "FALLIDO"}


def test_resumen_no_vacio(registro):
    _, fields = registro
    assert fields["Resumen de la salida"].strip("`").strip() != ""


def test_resultado_coherente_con_codigo_salida(registro):
    _, fields = registro
    codigo = int(fields["Código de salida"].strip("`"))
    resultado = fields["Resultado"].strip("`")
    # S2: 0 = éxito, cualquier otro valor = fallo.
    assert (codigo == 0) == (resultado == "APROBADO"), (
        f"Incoherencia: código de salida {codigo} con Resultado {resultado}"
    )


def test_estado_marca_coherente_con_resultado(registro):
    # ST9: [x] <=> APROBADO (S4: un fallo no se marca como completado con éxito).
    mark, fields = registro
    resultado = fields["Resultado"].strip("`")
    assert (mark in {"x", "X"}) == (resultado == "APROBADO"), (
        f"Marca [{mark}] incoherente con Resultado {resultado}"
    )
