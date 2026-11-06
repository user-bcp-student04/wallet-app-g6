"""Fuente de features desde openspec/changes/ (SDD) en lugar del backlog MCP."""
import re
from pathlib import Path

CHANGES_DIR = Path(__file__).resolve().parents[1] / "openspec" / "changes"
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_PLACEHOLDER = re.compile(r"<[^<>\n]{2,}>")


class OpenSpecError(Exception):
    pass


def list_changes(changes_dir: Path = CHANGES_DIR) -> list[str]:
    if not changes_dir.is_dir():
        return []
    return sorted(p.name for p in changes_dir.iterdir()
                  if p.is_dir() and p.name != "archive" and (p / "proposal.md").is_file())


def _read(path: Path) -> str:
    return _COMMENT.sub("", path.read_text(encoding="utf-8")).strip() if path.is_file() else ""


def _criteria(spec_text: str) -> list[str]:
    criteria: list[str] = []
    requirement = ""
    scenario = ""
    section = ""
    for raw in spec_text.splitlines():
        line = raw.strip()
        if line.startswith("### Requirement:"):
            requirement, scenario, section = line.split(":", 1)[1].strip(), "", "req"
        elif line.startswith("#### Scenario:"):
            scenario, section = line.split(":", 1)[1].strip(), "scenario"
            criteria.append(f"{requirement} / Escenario {scenario}:")
        elif line.startswith("## "):
            section = line[3:].strip().lower()
            requirement = scenario = ""
        elif not line:
            continue
        elif section == "req" and requirement:
            criteria.append(f"{requirement}: {line}")
        elif section == "scenario" and criteria:
            criteria[-1] += " " + line.lstrip("- ").replace("**", "")
        elif section in ("constraints", "acceptance evidence") and line.startswith("- "):
            label = "Restricción" if section == "constraints" else "Evidencia"
            criteria.append(f"{label}: {line[2:].strip()}")
    return criteria


def _issue_number(proposal: str):
    match = re.search(r"Issue:\s*#(\d+)", proposal)
    return int(match.group(1)) if match else None


def load_feature(name: str, changes_dir: Path = CHANGES_DIR) -> dict:
    """Devuelve {title, description, acceptance_criteria, issue_number} del change."""
    base = changes_dir / name
    proposal = _read(base / "proposal.md")
    design = _read(base / "design.md")
    tasks = _read(base / "tasks.md")
    specs = [(p, _read(p)) for p in sorted((base / "specs").glob("**/spec.md"))]
    criteria = [c for _, text in specs for c in _criteria(text)]

    for label, text in (("proposal.md", proposal), ("design.md", design), ("tasks.md", tasks),
                        *((str(p.relative_to(base)), t) for p, t in specs)):
        if _PLACEHOLDER.search(text):
            raise OpenSpecError(f"{name}/{label} aún tiene plantillas sin completar ({_PLACEHOLDER.search(text).group(0)}).")
    if not criteria:
        raise OpenSpecError(f"{name} no tiene requisitos en specs/*/spec.md.")

    description = "\n\n".join(f"## {title}\n{text}" for title, text in
                              (("Propuesta (proposal.md)", proposal),
                               ("Diseño (design.md)", design),
                               ("Tareas (tasks.md)", tasks)) if text)
    return {"title": name, "description": description,
            "acceptance_criteria": criteria, "issue_number": _issue_number(proposal)}
