"""Load features from openspec/changes without MCP or GitHub."""

from pathlib import Path
import tempfile
import unittest

from crew import openspec_source as source

SPEC = """## ADDED Requirements

### Requirement: Consultar saldo

El sistema DEBE devolver el saldo actual.

#### Scenario: Usuario con saldo

- **GIVEN** una wallet activa
- **WHEN** consulta GET /wallet/balance
- **THEN** recibe 200 con el saldo

## Constraints

- No cambiar GET /health
"""


def make_change(root: Path, spec: str = SPEC, name: str = "demo") -> None:
    change = root / name
    (change / "specs" / "wallet").mkdir(parents=True)
    (change / "proposal.md").write_text("## GitHub Issue\n\n- Issue: #7\n\n## Why\n\nSaldo.\n", encoding="utf-8")
    (change / "design.md").write_text("## Context\n\nFastAPI.\n", encoding="utf-8")
    (change / "tasks.md").write_text("- [ ] 1.1 Endpoint\n", encoding="utf-8")
    (change / "specs" / "wallet" / "spec.md").write_text(spec, encoding="utf-8")


class OpenSpecSourceTests(unittest.TestCase):
    def test_lists_changes_and_skips_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_change(root)
            (root / "archive").mkdir()
            self.assertEqual(source.list_changes(root), ["demo"])

    def test_builds_feature_from_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_change(Path(tmp))
            feature = source.load_feature("demo", Path(tmp))
        self.assertEqual(feature["title"], "demo")
        self.assertEqual(feature["issue_number"], 7)
        self.assertIn("FastAPI", feature["description"])
        self.assertIn("1.1 Endpoint", feature["description"])
        criteria = feature["acceptance_criteria"]
        self.assertIn("Consultar saldo: El sistema DEBE devolver el saldo actual.", criteria)
        self.assertTrue(any("GIVEN una wallet activa" in c and "THEN recibe 200" in c for c in criteria))
        self.assertIn("Restricción: No cambiar GET /health", criteria)

    def test_rejects_unfilled_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_change(Path(tmp), SPEC.replace("Consultar saldo", "<nombre verificable>"))
            with self.assertRaises(source.OpenSpecError):
                source.load_feature("demo", Path(tmp))


if __name__ == "__main__":
    unittest.main()
