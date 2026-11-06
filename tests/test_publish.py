"""Paso final de PR: mapeo de rutas y aprobación humana (sin llamar a GitHub)."""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import main as app
from crew import publish_pr

FEATURE = {"title": "Crear una tarea con título", "description": "d", "acceptance_criteria": ["A"]}
STEPS = [("chapter", "Chapter", None, "chapter_review.md", False)]


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)
        for rel in ("api/app/tasks.py", "frontend-angular/src/app/tareas/t.component.ts",
                    "frontend-angular/package.json", "specs/chapter_review.md"):
            (self.out / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.out / rel).write_text("x")

    def tearDown(self):
        self.tmp.cleanup()

    def test_only_generated_files_are_mapped_to_product_layout(self):
        files = publish_pr.plan_files(
            self.out, ["api/app/tasks.py", "frontend-angular/src/app/tareas/t.component.ts"],
            ["chapter_review.md"], "crear-una-tarea")
        self.assertEqual(sorted(files), [
            "api/app/tasks.py",
            "docs/crewai/crear-una-tarea/chapter_review.md",
            "web/src/app/tareas/t.component.ts",
        ])  # el andamiaje (package.json) no viaja al PR

    def test_target_repo_uses_owner_from_env(self):
        with patch.dict("os.environ", {"GITHUB_OWNER": "acme", "PR_REPO": ""}):
            self.assertEqual(publish_pr.target_repo(), "acme/ai-labs")
        with patch.dict("os.environ", {"GITHUB_OWNER": "<OWNER>"}):
            self.assertIsNone(publish_pr.target_repo())

    def test_verdict_is_parsed(self):
        self.assertEqual(publish_pr.verdict("...\n**VEREDICTO: APROBADO**"), "APROBADO")
        self.assertEqual(publish_pr.verdict("nada"), "SIN VEREDICTO")

    def run_step(self, answer):
        checkpoint = {"steps": {}}
        with patch.object(app, "OUTPUT_DIR", self.out), \
                patch.object(app, "CHECKPOINT_FILE", self.out / ".checkpoint.json"), \
                patch.object(publish_pr, "target_repo", return_value="acme/ai-labs"), \
                patch.object(publish_pr, "open_pr", return_value="https://github.com/acme/ai-labs/pull/7") as opened, \
                patch("builtins.input", return_value=answer), \
                contextlib.redirect_stdout(io.StringIO()):
            app.publish_step(checkpoint, FEATURE, 12, STEPS, ["api/app/tasks.py"], "VEREDICTO: APROBADO")
        return checkpoint, opened

    def test_pr_needs_human_approval(self):
        checkpoint, opened = self.run_step("n")
        opened.assert_not_called()
        self.assertNotIn("pr", checkpoint)

    def test_approved_pr_is_opened_once_and_recorded(self):
        checkpoint, opened = self.run_step("s")
        opened.assert_called_once()
        self.assertEqual(opened.call_args.args[2], 12)
        self.assertEqual(checkpoint["pr"]["url"], "https://github.com/acme/ai-labs/pull/7")


if __name__ == "__main__":
    unittest.main()
