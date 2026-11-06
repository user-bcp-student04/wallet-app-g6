# api/h01_checks/check_h01_change_state.py
"""Comprobaciones del cambio H01 sobre el repositorio real (fase 2).

Fuera de api/tests/: no se recogen con `pytest tests/` ni con `python tools/lab.py test api`.
Se ejecutan a propósito (ver testing_report.md §5).
En la línea base pueden fallar legítimamente por artefactos aún no creados
(.env, baseline.md rellenado, spec cerrada, URL fijada). Eso no es regresión.
Ninguna prueba usa skip: si falta MOCK_W1_URL, falla.
"""
from h01_support import (
    BASELINE_PATH,
    ENVIRONMENT_TS_PATH,
    SPEC_PATH,
    TASKS_PATH,
    base_ref,
    check_baseline_text,
    check_health,
    check_spec_text,
    get_mock_url,
    parse_tasks,
    read_env_problems,
    repo_root,
    run_git,
    url_in_environment_ts,
)


def _read(rel: str) -> str:
    path = repo_root() / rel
    assert path.is_file(), f"no existe {rel}"
    return path.read_text(encoding="utf-8")


# ----------------------------------------------------------------- 1.1
def test_env_real_tiene_las_tres_variables_exactas():  # T-17
    assert read_env_problems(repo_root()) == []


def test_env_real_no_versionado():  # T-18
    root = repo_root()
    # la comprobación de secretos por clave y por valor ya vive en read_env_problems (T-17)
    proc = run_git(root, "check-ignore", "-q", ".env")
    assert proc.returncode == 0, ".env no está ignorado por git (supuesto S2)"
    tracked = run_git(root, "ls-files", "--error-unmatch", ".env")
    assert tracked.returncode != 0, ".env está versionado"


# ----------------------------------------------------------------- 1.2
def test_baseline_md_real_rellenado():  # T-27
    assert check_baseline_text(_read(BASELINE_PATH)) == []


# ----------------------------------------------------------------- 1.3
def test_spec_real_cierra_las_seis_preguntas():  # T-28 (depende de S5)
    assert check_spec_text(_read(SPEC_PATH)) == []


def test_tasks_1_1_a_1_4_marcadas():  # T-29
    tasks = parse_tasks(_read(TASKS_PATH))
    for task_id in ("1.1", "1.2", "1.3", "1.4"):
        assert tasks.get(task_id) is True, f"tarea {task_id} no está marcada [x]"


# ----------------------------------------------------------------- 1.4
def test_mock_w1_responde_200_en_health():  # T-21
    assert check_health(get_mock_url()) == 200


def test_url_del_mock_fijada_en_environment_ts():  # T-30
    url = get_mock_url()
    assert url_in_environment_ts(_read(ENVIRONMENT_TS_PATH), url), (
        f"{url} no aparece como literal en {ENVIRONMENT_TS_PATH}"
    )


def test_diff_frontend_limitado_a_environment_ts():  # T-33
    root = repo_root()
    tracked = run_git(root, "diff", "--name-only", base_ref(), "--", "src")
    untracked = run_git(root, "ls-files", "--others", "--exclude-standard", "--", "src")
    assert tracked.returncode == 0, tracked.stderr
    assert untracked.returncode == 0, untracked.stderr
    changed = [p for p in (tracked.stdout + untracked.stdout).splitlines() if p.strip()]
    assert set(changed) <= {ENVIRONMENT_TS_PATH}, f"cambios fuera de environment.ts: {changed}"
