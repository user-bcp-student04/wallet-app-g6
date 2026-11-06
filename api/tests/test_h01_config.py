# api/tests/test_h01_config.py
"""Configuración MAX_BODY_BYTES: valores por defecto, inválidos y válidos."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from app import config

API_DIR = Path(__file__).resolve().parents[1]
DEFAULT = 1_048_576
VAR = "MAX_BODY_BYTES"


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, DEFAULT),
        ("", DEFAULT),
        ("   ", DEFAULT),
        ("abc", DEFAULT),
        ("0", DEFAULT),
        ("-5", DEFAULT),
        ("2048", 2048),
        (" 4096 ", 4096),
    ],
)
def test_int_env(monkeypatch, raw, expected):
    if raw is None:
        monkeypatch.delenv(VAR, raising=False)
    else:
        monkeypatch.setenv(VAR, raw)
    assert config._int_env(VAR, DEFAULT) == expected


def test_max_body_bytes_positivo():
    assert isinstance(config.MAX_BODY_BYTES, int)
    assert config.MAX_BODY_BYTES > 0


def _run_config(env_value):
    env = dict(os.environ)
    env.pop(VAR, None)
    if env_value is not None:
        env[VAR] = env_value
    env["PYTHONPATH"] = str(API_DIR)
    out = subprocess.run(
        [sys.executable, "-c", "from app import config; print(config.MAX_BODY_BYTES)"],
        cwd=str(API_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert out.returncode == 0, out.stderr
    return int(out.stdout.strip())


def test_config_en_proceso_aislado_default():
    assert _run_config(None) == DEFAULT


def test_config_en_proceso_aislado_valor_valido():
    assert _run_config("2048") == 2048


def test_config_en_proceso_aislado_valor_invalido():
    assert _run_config("no-es-numero") == DEFAULT
