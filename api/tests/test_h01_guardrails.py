# api/tests/test_h01_guardrails.py
"""Línea base. Comprueba que H01 no altera el API ni la persistencia (alcance del Arquitecto).

Requiere git en el PATH. H01_BASE_REF (por defecto HEAD) es el commit base.
Supuesto S8: app.main:app es importable con el directorio actual api/.
"""
import pytest
from fastapi.testclient import TestClient

try:
    from h01_support import base_ref, repo_root, run_git
except ImportError:
    from tests.h01_support import base_ref, repo_root, run_git

PROTECTED = ["api/app", "api/requirements.txt", "tools/verify.py"]


def _git_lines(*args: str) -> list[str]:
    proc = run_git(repo_root(), *args)
    assert proc.returncode == 0, f"git {' '.join(args)} falló: {proc.stderr}"
    return [line for line in proc.stdout.splitlines() if line.strip()]


@pytest.mark.parametrize("path", PROTECTED)
def test_archivos_protegidos_sin_diff(path):  # T-22
    assert _git_lines("diff", "--name-only", base_ref(), "--", path) == []


def test_pruebas_existentes_no_modificadas():  # T-23
    # M=modificado, D=borrado, R=renombrado: las pruebas nuevas (A / sin rastrear) no cuentan
    changed = _git_lines("diff", "--name-only", "--diff-filter=MDR", base_ref(), "--", "api/tests")
    assert changed == []


def test_sin_archivos_nuevos_en_api_app():  # T-24
    assert _git_lines("ls-files", "--others", "--exclude-standard", "--", "api/app") == []
    assert _git_lines("diff", "--name-only", "--diff-filter=A", base_ref(), "--", "api/app") == []


def test_sin_sql_ni_migraciones_nuevas():  # T-25
    candidates = _git_lines("ls-files", "--others", "--exclude-standard", "--", "api")
    candidates += _git_lines("diff", "--name-only", "--diff-filter=A", base_ref(), "--", "api")
    offenders = [
        p for p in candidates
        if p.lower().endswith(".sql") or "migration" in p.lower() or "alembic" in p.lower()
    ]
    assert offenders == []


def test_api_responde_sin_escribir_en_cwd(tmp_path, monkeypatch):  # T-26
    from app.main import app  # importar antes de cambiar el directorio actual

    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/__ruta_inexistente_h01__").status_code == 404
    assert list(tmp_path.iterdir()) == []
