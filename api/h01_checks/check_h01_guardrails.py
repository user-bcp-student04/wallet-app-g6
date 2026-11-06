# api/h01_checks/check_h01_guardrails.py
"""Línea base. Comprueba que H01 no altera el API ni la persistencia (alcance del Arquitecto).

Fuera de api/tests/: no se recogen con `pytest tests/` ni con `python tools/lab.py test api`.
Requiere git en el PATH. H01_BASE_REF (por defecto HEAD) es el commit base y se valida (SEC-06).
Supuesto S8: si api/app existe en la base, app.main:app es importable con el directorio actual api/.
H01 es de preparación: si api/app aún no existe en la base, T-26 exige que siga sin existir.
"""
import pytest

from h01_support import base_ref, repo_root, run_git

PROTECTED = ["api/app", "api/requirements.txt", "tools/verify.py"]


def _git_lines(*args: str) -> list[str]:
    proc = run_git(repo_root(), *args)
    assert proc.returncode == 0, f"git {' '.join(args)} falló: {proc.stderr}"
    return [line for line in proc.stdout.splitlines() if line.strip()]


@pytest.mark.parametrize("path", PROTECTED)
def test_archivos_protegidos_sin_diff(path):  # T-22
    assert _git_lines("diff", "--name-only", base_ref(), "--", path) == []


def test_pruebas_existentes_no_modificadas():  # T-23
    # M=modificado, D=borrado, R=renombrado, A=añadido: api/tests/ no cambia en H01
    changed = _git_lines("diff", "--name-only", "--diff-filter=MDRA", base_ref(), "--", "api/tests")
    assert changed == []
    assert _git_lines("ls-files", "--others", "--exclude-standard", "--", "api/tests") == []


def test_sin_pruebas_h01_en_api_tests():  # T-34 (B-1)
    names = [p.name for p in (repo_root() / "api" / "tests").glob("*h01*")]
    assert names == []


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
    in_base = _git_lines("ls-tree", "-r", "--name-only", base_ref(), "--", "api/app")
    if not in_base:
        assert not (repo_root() / "api" / "app").exists(), "H01 no crea api/app"
        return

    from fastapi.testclient import TestClient
    from app.main import app  # importar antes de cambiar el directorio actual

    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/__ruta_inexistente_h01__").status_code == 404
    assert list(tmp_path.iterdir()) == []
