"""Regresiones del extractor de código y del manejo de errores por paso."""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import main as app

FENCE = "```"


def block(lang, body):
    return f"{FENCE}{lang}\n{body}\n{FENCE}\n"


class ExtractTests(unittest.TestCase):
    def extract(self, text):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            out = Path(tmp)
            with patch.object(app, "OUTPUT_DIR", out):
                saved = app.extract_and_save_code(text)
            files = {p: (out / p).read_text() for p in saved}
        return saved, files

    def test_tree_and_shell_blocks_are_not_files(self):
        text = (
            "## Estructura\n" + block("", "api/\n  app/\n    main.py\n  tests/\n    test_upload.py")
            + "Comandos:\n" + block("bash", "pytest api/tests/test_upload.py\npython tools/lab.py test api")
            + block("python", "# api/app/main.py\nfrom fastapi import FastAPI\napp = FastAPI()")
            + block("python", "# api/tests/test_upload.py\ndef test_ok():\n    assert True")
        )
        saved, files = self.extract(text)
        self.assertEqual(sorted(saved), ["api/app/main.py", "api/tests/test_upload.py"])
        self.assertIn("FastAPI()", files["api/app/main.py"])
        self.assertIn("def test_ok", files["api/tests/test_upload.py"])

    def test_path_comment_beats_prose_before_block(self):
        text = ("Se registra el router en api/app/main.py:\n"
                + block("python", "# api/app/routers/upload.py\nrouter = 1"))
        saved, _ = self.extract(text)
        self.assertEqual(saved, ["api/app/routers/upload.py"])

    def test_heading_line_names_block_without_comment(self):
        saved, _ = self.extract("**`api/app/schemas.py`**\n" + block("python", "class A: ..."))
        self.assertEqual(saved, ["api/app/schemas.py"])

    def test_unusual_fences_and_crlf_do_not_shift_blocks(self):
        text = (f"{FENCE}py title=api/app/a.py\nA = 1\n{FENCE}\r\n"
                f"Texto con api/app/z.py\r\n"
                f"{FENCE} python\r\n# api/app/b.py\r\nB = 2\r\n{FENCE}\r\n")
        saved, files = self.extract(text)
        self.assertEqual(sorted(saved), ["api/app/a.py", "api/app/b.py"])
        self.assertIn("B = 2", files["api/app/b.py"])

    def test_markdown_wrapper_is_unwrapped(self):
        inner = block("python", "# api/app/x.py\nX = 1")
        saved, _ = self.extract(f"{FENCE}markdown\n# Spec\n{inner}{FENCE}")
        self.assertEqual(saved, ["api/app/x.py"])

    def test_python_project_files_are_kept(self):
        text = (block("text", "# api/requirements-dev.txt\npytest==8.3.3")
                + block("ini", "# api/pytest.ini\n[pytest]")
                + block("text", "# requirements.txt\nfastapi==0.115.0"))
        saved, _ = self.extract(text)
        self.assertEqual(sorted(saved), ["api/pytest.ini", "api/requirements-dev.txt", "api/requirements.txt"])

    def test_angular_keeps_its_folders(self):
        text = (block("typescript", "// src/app/tareas/tarea-form.component.ts\nexport class TareaFormComponent {}")
                + block("html", "<!-- src/app/tareas/tarea-form.component.html -->\n<form></form>")
                + block("typescript", "// app.routes.ts\nexport const routes = [];")
                + block("typescript", "export class TareaService {}"))
        saved, _ = self.extract(text)
        self.assertEqual(sorted(saved), [
            "frontend-angular/src/app/app.routes.ts",
            "frontend-angular/src/app/tarea.service.ts",
            "frontend-angular/src/app/tareas/tarea-form.component.html",
            "frontend-angular/src/app/tareas/tarea-form.component.ts",
        ])

    def test_java_and_path_traversal_are_ignored(self):
        text = (block("java", "public class User {}")
                + block("python", "# ../../etc/evil.py\nX = 1"))
        saved, _ = self.extract(text)
        self.assertEqual(saved, [])

    def test_sql_goes_to_db(self):
        saved, _ = self.extract(block("sql", "-- migration.sql\nCREATE TABLE t (id INT);"))
        self.assertEqual(saved, ["db/migration.sql"])


class StepErrorTests(unittest.TestCase):
    def test_step_error_offers_retry_instead_of_crashing(self):
        answers = iter(["r", ""])
        with patch("builtins.input", side_effect=lambda *_: next(answers)), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(app.handle_step_error("Backend", RuntimeError("timeout")), ("r", ""))

    def test_closed_stdin_never_approves(self):
        with patch("builtins.input", side_effect=EOFError), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(app.hitl_approve("Backend", "texto")[0], "n")


if __name__ == "__main__":
    unittest.main()
