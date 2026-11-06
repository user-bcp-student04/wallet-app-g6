"""Paso final: abre un PR (borrador) con el código y las specs en <GITHUB_OWNER>/ai-labs.

Solo corre tras la aprobación humana explícita. Usa el CLI `gh` con la sesión
de quien ejecuta el flujo; si esa cuenta no puede hacer push al repo destino,
publica la rama en un fork y abre el PR desde ahí.

Variables de entorno:
  GITHUB_OWNER    owner del repo destino (obligatoria).
  PR_REPO         nombre del repo destino (por defecto ai-labs).
  PR_BASE_BRANCH  rama base (por defecto, la rama por defecto del repo).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import unicodedata
from pathlib import Path

# output/<origen>  →  ruta dentro del repo del producto
PATH_MAP = (
    ("api/", "api/"),
    ("frontend-angular/", "web/"),
    ("db/", "db/"),
)
SPECS_DIR = "docs/crewai"


class PublishError(RuntimeError):
    pass


def target_repo() -> str | None:
    owner = os.getenv("GITHUB_OWNER", "").strip()
    if not owner or owner.startswith("<"):
        return None
    return f"{owner}/{os.getenv('PR_REPO', 'ai-labs').strip() or 'ai-labs'}"


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:40] or "feature"


def repo_path(generated: str) -> str | None:
    """Ruta en el repo destino para un archivo generado en output/."""
    for source, dest in PATH_MAP:
        if generated.startswith(source):
            return dest + generated[len(source):]
    return None


def plan_files(output_dir: Path, generated: list[str], spec_files: list[str], slug: str) -> dict[str, Path]:
    """{ruta en el repo: archivo local}. Solo lo generado por los agentes, nunca el andamiaje."""
    files: dict[str, Path] = {}
    for rel in sorted(set(generated)):
        dest = repo_path(rel)
        if dest and (output_dir / rel).is_file():
            files[dest] = output_dir / rel
    for spec in spec_files:
        if (output_dir / "specs" / spec).is_file():
            files[f"{SPECS_DIR}/{slug}/{spec}"] = output_dir / "specs" / spec
    return files


def verdict(chapter_text: str) -> str:
    found = re.findall(r"VEREDICTO\W*\s*(APROBADO|RECHAZADO)", chapter_text.upper())
    return found[-1] if found else "SIN VEREDICTO"


def build_body(feature: dict, issue_number, chapter_text: str, files: dict[str, Path]) -> str:
    criteria = "\n".join(f"- [ ] {c}" for c in feature.get("acceptance_criteria", []))
    file_list = "\n".join(f"- `{p}`" for p in files)
    refs = f"Refs #{issue_number}\n\n" if issue_number else ""
    excerpt = chapter_text.strip()[-1500:]
    return (
        f"{refs}## {feature.get('title', '')}\n\n"
        "Generado por el flujo CrewAI (Arquitecto → Backend → Frontend → Pruebas → Seguridad → Chapter) "
        "con aprobación humana en cada etapa.\n\n"
        f"**Veredicto del Chapter:** {verdict(chapter_text)}\n\n"
        f"### Criterios de aceptación\n{criteria}\n\n"
        "### Pruebas\nNO EJECUTADAS por el flujo. Antes de integrar, ejecutar y adjuntar la salida real:\n\n"
        "```sh\npython tools/lab.py test api\n```\n\n"
        f"### Archivos\n{file_list}\n\n"
        f"Las specs completas están en `{SPECS_DIR}/`.\n\n"
        f"<details><summary>Extracto de la revisión del Chapter</summary>\n\n{excerpt}\n\n</details>\n"
    )


def _run(cmd: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()[-3:]
        raise PublishError(f"Falló `{' '.join(cmd[:3])}`: {' '.join(detail)}")
    return result.stdout.strip()


def _push_target(repo: str) -> tuple[str, str]:
    """(remoto al que hacer push, prefijo de --head). Usa un fork si no hay permiso de push."""
    info = json.loads(_run(["gh", "api", f"repos/{repo}"]))
    if info.get("permissions", {}).get("push"):
        return f"https://github.com/{repo}.git", ""
    me = _run(["gh", "api", "user", "--jq", ".login"])
    _run(["gh", "repo", "fork", repo, "--clone=false", "--default-branch-only"])
    forks = _run(["gh", "api", "--paginate", f"repos/{repo}/forks",
                  "--jq", f'.[] | select(.owner.login=="{me}") | .full_name'])
    fork = forks.splitlines()[0] if forks else f"{me}/{repo.split('/')[1]}"
    for _ in range(10):  # GitHub tarda unos segundos en crear el fork
        if subprocess.run(["gh", "api", f"repos/{fork}"], capture_output=True).returncode == 0:
            break
        time.sleep(3)
    return f"https://github.com/{fork}.git", f"{me}:"


def open_pr(repo: str, feature: dict, issue_number, files: dict[str, Path], chapter_text: str) -> str:
    """Clona el repo destino, copia los archivos, publica una rama y abre el PR en borrador."""
    if shutil.which("gh") is None:
        raise PublishError("No se encontró el CLI `gh`. Instálalo y ejecuta `gh auth login`.")
    if not files:
        raise PublishError("No hay archivos generados que publicar.")
    _run(["gh", "auth", "status"])
    info = json.loads(_run(["gh", "api", f"repos/{repo}"]))
    base = os.getenv("PR_BASE_BRANCH", "").strip() or info["default_branch"]
    slug = slugify(feature.get("title", ""))
    branch = f"crewai/{slug}-{time.strftime('%Y%m%d-%H%M%S')}"

    with tempfile.TemporaryDirectory(prefix="crewai-pr-") as tmp:
        clone = Path(tmp) / "repo"
        _run(["gh", "repo", "clone", repo, str(clone), "--", "--depth", "1", "--branch", base])
        _run(["git", "switch", "-c", branch], cwd=clone)
        for dest, source in files.items():
            target = clone / dest
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        _run(["git", "add", "--", *files.keys()], cwd=clone)
        if not _run(["git", "status", "--porcelain"], cwd=clone):
            raise PublishError(f"Los archivos generados son idénticos a {repo}@{base}: no hay cambios.")
        title = f"feat: {feature.get('title', 'feature')} (CrewAI)"
        _run(["git", "commit", "-m", title, "-m",
              "Generado por el flujo CrewAI con aprobación humana en cada etapa."], cwd=clone)
        remote, head_prefix = _push_target(repo)
        _run(["git", "push", remote, f"HEAD:refs/heads/{branch}"], cwd=clone)
        body = Path(tmp) / "body.md"
        body.write_text(build_body(feature, issue_number, chapter_text, files), encoding="utf-8")
        out = _run(["gh", "pr", "create", "--repo", repo, "--base", base,
                    "--head", f"{head_prefix}{branch}", "--draft",
                    "--title", title, "--body-file", str(body)])
    return out.splitlines()[-1]
