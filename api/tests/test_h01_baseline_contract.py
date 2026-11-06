# api/tests/test_h01_baseline_contract.py
"""Línea base H01: los artefactos de entrada de la tarea 4.1 existen y son coherentes.

No ejecuta tools/verify.py (su contenido es desconocido y podría ser recursivo).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHANGE = ROOT / "openspec" / "changes" / "registro-activacion-wallet"
TASKS = CHANGE / "tasks.md"
SPEC = CHANGE / "specs" / "wallet-onboarding" / "spec.md"
VERIFY = ROOT / "tools" / "verify.py"
LAB = ROOT / "tools" / "lab.py"

LINEA_4_1 = re.compile(
    r"^- \[[ xX]\] 4\.1 Ejecutar `python tools/verify\.py` y registrar el resultado\s*$",
    re.MULTILINE,
)


def test_verify_py_existe_y_compila():
    assert VERIFY.is_file(), f"No existe {VERIFY}"
    source = VERIFY.read_text(encoding="utf-8")
    compile(source, str(VERIFY), "exec")  # solo sintaxis; no se ejecuta


def test_lab_py_existe():
    assert LAB.is_file(), f"No existe {LAB}"


def test_spec_existe():
    assert SPEC.is_file(), f"No existe {SPEC}"


def test_tarea_4_1_existe_una_vez():
    assert TASKS.is_file(), f"No existe {TASKS}"
    text = TASKS.read_text(encoding="utf-8")
    matches = LINEA_4_1.findall(text)
    assert len(matches) == 1, (
        "La tarea 4.1 debe aparecer exactamente una vez; "
        f"encontradas: {len(matches)}"
    )
