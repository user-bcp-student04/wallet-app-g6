"""S1 CrewAI — Generador BCP con HITL y checkpoint por paso.

Flujo:
  1. Conecta al MCP Projects → lista proyectos → elige proyecto → lista backlog → elige feature
  2. Por cada agente (Arquitecto, Backend, Frontend, Pruebas, Seguridad, Chapter), corre un mini-Crew de un solo paso.
  3. Tras cada paso muestra un preview y pide aprobación humana [s / n / r]:
       s = aprobar y continuar
       n = rechazar y abortar
       r = reintentar el mismo paso
  4. Al aprobar: guarda el artefacto inmediatamente (spec .md / código .py .ts .sql)
     y registra el checkpoint en output/.checkpoint.json.
  5. Al volver a ejecutar: carga el checkpoint y omite los pasos ya aprobados,
     inyectando sus outputs como contexto para los pasos restantes.

Estructura generada en output/:
  .checkpoint.json        ← estado de cada paso
  specs/
    user_story.md
    backend_spec.md
    frontend_spec.md
    chapter_review.md
  api/app/*.py  api/tests/*.py  api/requirements.txt
  frontend-angular/src/app/<feature>/...
  db/schema.sql  seed.sql
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
import logging

# ---------------------------------------------------------------------------
# Telemetría configurable por entorno
# ---------------------------------------------------------------------------
os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ["OTEL_LOG_LEVEL"] = "error"                # No ensucia la terminal con logs informativos
os.environ["OTEL_BSP_EXPORT_TIMEOUT"] = "2000"        # Reduce timeout de exportación a 2s (evita cuelgues al salir)

# Silenciar loggers que puedan imprimir advertencias de red/telemetría en stderr
for _log in ("opentelemetry", "crewai.telemetry", "urllib3", "requests"):
    logging.getLogger(_log).setLevel(logging.ERROR)


import re
import json
import time
import signal
import threading
import textwrap
from pathlib import Path
from crewai import Crew, Process

from lab_copilot import runtime as copilot_runtime

from crew.workflow import build_tasks, include_data, workflow_steps
from crew import publish_pr

# ── MCP clients ────────────────────────────────────────────────────
from mcp_projects import (
    list_tools as proj_tools,
    list_projects,
    list_project_items,
    get_feature_from_item,
)

# ── Flag de verbosidad MCP ─────────────────────────────────────────
# True  → muestra el detalle de cada herramienta al arrancar
# False → solo confirma "Herramientas cargadas correctamente."
VERBOSE_MCP_TOOLS = False

# ── Scaffolding determinista para Backend y Frontend ────────────────
FASTAPI_REQUIREMENTS_TEMPLATE = """fastapi>=0.110
uvicorn[standard]>=0.29
python-multipart>=0.0.9
pytest>=8.0
httpx>=0.27
"""

ANGULAR_PACKAGE_JSON = """{
  "name": "frontend-angular",
  "version": "1.0.0",
  "scripts": {
    "ng": "ng",
    "start": "ng serve",
    "build": "ng build",
    "watch": "ng build --watch --configuration development"
  },
  "private": true,
  "dependencies": {
    "@angular/animations": "^17.3.0",
    "@angular/common": "^17.3.0",
    "@angular/compiler": "^17.3.0",
    "@angular/core": "^17.3.0",
    "@angular/forms": "^17.3.0",
    "@angular/platform-browser": "^17.3.0",
    "@angular/platform-browser-dynamic": "^17.3.0",
    "@angular/router": "^17.3.0",
    "rxjs": "~7.8.0",
    "tslib": "^2.3.0",
    "zone.js": "~0.14.3"
  },
  "devDependencies": {
    "@angular-devkit/build-angular": "^17.3.0",
    "@angular/cli": "^17.3.0",
    "@angular/compiler-cli": "^17.3.0",
    "typescript": "~5.4.2"
  }
}
"""

ANGULAR_JSON = """{
  "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
  "version": 1,
  "newProjectRoot": "projects",
  "projects": {
    "frontend-angular": {
      "projectType": "application",
      "root": "",
      "sourceRoot": "src",
      "prefix": "app",
      "architect": {
        "build": {
          "builder": "@angular-devkit/build-angular:application",
          "options": {
            "outputPath": "dist/frontend-angular",
            "index": "src/index.html",
            "browser": "src/main.ts",
            "polyfills": ["zone.js"],
            "tsConfig": "tsconfig.app.json",
            "styles": ["src/styles.css"]
          },
          "configurations": {
            "production": {
              "outputHashing": "all"
            },
            "development": {
              "optimization": false,
              "sourceMap": true
            }
          },
          "defaultConfiguration": "production"
        },
        "serve": {
          "builder": "@angular-devkit/build-angular:dev-server",
          "configurations": {
            "production": {
              "buildTarget": "frontend-angular:build:production"
            },
            "development": {
              "buildTarget": "frontend-angular:build:development"
            }
          },
          "defaultConfiguration": "development"
        }
      }
    }
  }
}
"""

ANGULAR_TSCONFIG_JSON = """{
  "compileOnSave": false,
  "compilerOptions": {
    "outDir": "./dist/out-tsc",
    "strict": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "experimentalDecorators": true,
    "moduleResolution": "node",
    "target": "ES2022",
    "module": "ES2022",
    "lib": ["ES2022", "dom"]
  }
}
"""

ANGULAR_TSCONFIG_APP_JSON = """{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "outDir": "./out-tsc/app",
    "types": []
  },
  "files": ["src/main.ts"],
  "include": ["src/**/*.d.ts"]
}
"""

ANGULAR_INDEX_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>BCP - Portal de Autenticación</title>
  <base href="/">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
  <app-root></app-root>
</body>
</html>
"""

ANGULAR_STYLES_CSS = """* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Inter', sans-serif;
  background: linear-gradient(135deg, #0b1f3a 0%, #002a66 50%, #0a438c 100%);
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}
"""

ANGULAR_MAIN_TS = """import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { AppComponent } from './app/app.component';
import { routes } from './app/app.routes';

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptorsFromDi())
  ]
}).catch(err => console.error(err));
"""

# El codigo de aplicacion (app.component.ts, app.routes.ts, el .css del
# componente y los módulos de api/app/*.py) lo genera el modelo: depende del feature.
# Aca solo queda el andamiaje de build, que ningun agente tiene que escribir.


def ensure_scaffolding(output_dir: Path) -> None:
    """
    Escribe sólo el andamiaje de build: api/requirements.txt de FastAPI, y
    package.json / angular.json / tsconfig / index.html / main.ts de
    Angular. Nada de esto describe el feature, así que no se le pide al modelo.

    El código de aplicación —entidad, repositorio, servicio, componentes, rutas
    y estilos— lo genera el agente y lo escribe extract_and_save_code(). Si el
    agente no lo emite, el proyecto queda incompleto a propósito: es la señal
    de que el paso falló, no algo que el andamiaje deba tapar.
    """
    # 1. Backend FastAPI
    req_path = output_dir / "api" / "requirements.txt"
    if not req_path.exists():
        req_path.parent.mkdir(parents=True, exist_ok=True)
        req_path.write_text(FASTAPI_REQUIREMENTS_TEMPLATE, encoding="utf-8")
        print("  🏗️ Scaffolding Backend: generado api/requirements.txt (FastAPI)")

    # 2. Frontend Angular 17
    front_dir = output_dir / "frontend-angular"
    front_scaffold = {
        "package.json": ANGULAR_PACKAGE_JSON,
        "angular.json": ANGULAR_JSON,
        "tsconfig.json": ANGULAR_TSCONFIG_JSON,
        "tsconfig.app.json": ANGULAR_TSCONFIG_APP_JSON,
        "src/index.html": ANGULAR_INDEX_HTML,
        "src/styles.css": ANGULAR_STYLES_CSS,
        "src/main.ts": ANGULAR_MAIN_TS,
    }
    created_front = 0
    for rel_path, content in front_scaffold.items():
        file_path = front_dir / rel_path
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            created_front += 1

    if created_front > 0:
        print(f"  🏗️ Scaffolding Frontend: generados {created_front} archivos base de Angular 17")


# ── Rutas base ─────────────────────────────────────────────────────
OUTPUT_DIR      = Path(__file__).parent / "output"
CHECKPOINT_FILE = OUTPUT_DIR / ".checkpoint.json"
OUTPUT_DIR.mkdir(exist_ok=True)   # lo necesita save_checkpoint()
# ensure_scaffolding() NO se llama aquí: escribiría en output/ con sólo importar
# el módulo, antes del MCP, del feature elegido y del primer agente.

# ── Checkpoint ─────────────────────────────────────────────────────

def load_checkpoint() -> dict:
    """Carga el checkpoint si existe, o retorna estado vacío."""
    if CHECKPOINT_FILE.exists():
        try:
            return json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"steps": {}}


def save_checkpoint(data: dict) -> None:
    """Persiste el checkpoint en disco de forma segura."""
    try:
        clean_data = {}
        for k, v in data.items():
            if k == "steps" and isinstance(v, dict):
                clean_steps = {}
                for sk, sv in v.items():
                    if isinstance(sv, dict):
                        clean_steps[sk] = {
                            "status": sv.get("status"),
                            "output": str(getattr(sv.get("output"), "raw", sv.get("output")) or "")
                        }
                    else:
                        clean_steps[sk] = str(sv)
                clean_data[k] = clean_steps
            else:
                clean_data[k] = v
        CHECKPOINT_FILE.write_text(json.dumps(clean_data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"  ⚠ Advertencia al guardar checkpoint: {e}")


# ── Output helpers ─────────────────────────────────────────────────

# ── Extracción de código ───────────────────────────────────────────
# Cada bloque ``` del output se guarda como archivo solo si su ruta es
# explícita (comentario de ruta en la primera línea, atributo del fence o
# línea-título justo antes del bloque) o, como último recurso, deducible del
# contenido. Los bloques de comandos y árboles de carpetas nunca se guardan.

CODE_EXTENSIONS = (
    "py", "ts", "html", "css", "scss", "sql", "txt", "json",
    "toml", "ini", "cfg", "yaml", "yml",
)
_EXT = "|".join(CODE_EXTENSIONS)
_PATH = rf"[A-Za-z0-9_.\-/\\]+\.(?:{_EXT})"
KNOWN_ROOTS = ("api/", "frontend-angular/", "db/")
SHELL_LANGS = {
    "bash", "sh", "shell", "zsh", "console", "terminal", "powershell", "ps1",
    "pwsh", "cmd", "bat", "batch", "http", "curl",
}
ANGULAR_ROOT_FILES = {"app.component.ts", "app.component.html", "app.component.css",
                      "app.routes.ts", "app.config.ts"}
PYTHON_PROJECT_FILES = {"pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini", ".coveragerc"}

_FENCE_OPEN = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})[ \t]*([^`\n]*)$")
# Primera línea del bloque formada SOLO por un comentario con la ruta.
_PATH_COMMENT = re.compile(
    rf"^\s*(?:#|//|--|/\*|<!--|;)\s*(?:(?:archivo|file|fichero|ruta|path)\s*:\s*)?"
    rf"[`\"']?({_PATH})[`\"']?\s*(?:\*/|-->)?\s*$",
    re.IGNORECASE,
)
# Línea-título previa al bloque: `ruta`, **ruta**, ### ruta, Archivo: ruta, 1. ruta:
_PATH_HEADING = re.compile(
    rf"^\s*(?:#{{1,6}}\s*)?(?:[-*+]\s+)?(?:\d+[.)]\s*)?(?:\*\*|__)?\s*"
    rf"(?:(?:archivo|file|fichero|ruta|path)\s*:?\s*)?(?:\*\*|__)?\s*`?({_PATH})`?\s*(?:\*\*|__)?"
    rf"\s*(?:\([^)]*\))?\s*:?\s*(?:\*\*|__)?\s*$",
    re.IGNORECASE,
)
_FENCE_ATTR = re.compile(rf"(?:title|file|filename|name|path)\s*=\s*[\"']?({_PATH})", re.IGNORECASE)
_FENCE_BARE_PATH = re.compile(rf"(?:^|\s)({_PATH})(?:\s|$)")


def _parse_code_blocks(text: str) -> list[dict]:
    """Separa bloques ``` / ~~~ respetando longitud y tipo de fence (CommonMark)."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks, i, prev = [], 0, ""
    while i < len(lines):
        m = _FENCE_OPEN.match(lines[i])
        if not m:
            if lines[i].strip():
                prev = lines[i]
            i += 1
            continue
        fence, info = m.group(1), m.group(2).strip()
        closer = re.compile(rf"^[ \t]{{0,3}}{re.escape(fence[0])}{{{len(fence)},}}[ \t]*$")
        body, j = [], i + 1
        while j < len(lines) and not closer.match(lines[j]):
            body.append(lines[j])
            j += 1
        blocks.append({"info": info, "lang": (info.split() or [""])[0].lower(),
                       "body": "\n".join(body), "prev": prev})
        prev, i = "", j + 1
    return blocks


def _unwrap_markdown(text: str) -> str:
    """Quita un ```markdown que envuelva toda la respuesta (con fences anidados dentro)."""
    stripped = text.strip()
    m = re.match(r"^(`{3,}|~{3,})[ \t]*(?:markdown|md)[ \t]*\n", stripped, re.IGNORECASE)
    if m and stripped.endswith(m.group(1)):
        return stripped[m.end():len(stripped) - len(m.group(1))]
    return text


def _kebab(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def _guess_name(lang: str, code: str) -> str | None:
    """Último recurso cuando el bloque no trae ruta: solo nombres inequívocos."""
    upper = code.upper()
    if lang in ("sql", "postgresql", "mysql", "sqlite") or "CREATE TABLE" in upper:
        if "CREATE TABLE" in upper or "ALTER TABLE" in upper:
            return "schema.sql"
        if "INSERT INTO" in upper:
            return "seed.sql"
    if lang in ("ts", "typescript"):
        m = re.search(r"export\s+class\s+(\w+?)(Component|Service|Guard|Interceptor|Pipe|Directive)\b", code)
        if m:
            return f"{_kebab(m.group(1))}.{m.group(2).lower()}.ts"
    return None


def python_destination(raw_name: str) -> str:
    """Ruta destino de un archivo Python/requirements del API FastAPI, siempre bajo api/."""
    parts = [p for p in raw_name.replace("\\", "/").split("/") if p not in ("", ".")]
    name = parts[-1]
    if ".." in parts:
        parts = [name]
    if len(parts) > 1 and parts[0] == "api":
        return "/".join(parts)
    if len(parts) > 1 and parts[0] in ("app", "tests"):
        return "api/" + "/".join(parts)
    if re.fullmatch(r"requirements[\w.\-]*\.txt", name) or name in PYTHON_PROJECT_FILES:
        return f"api/{name}"
    if name == "conftest.py" or name.startswith("test_") or name.endswith("_test.py"):
        return f"api/tests/{name}"
    return f"api/app/{name}"


def code_destination(raw_name: str) -> str | None:
    """Ruta bajo output/ para un archivo; None si no corresponde a ningún proyecto."""
    clean = raw_name.strip().strip("`\"'").replace("\\", "/")
    parts = [p for p in clean.split("/") if p not in ("", ".")]
    if not parts or ".." in parts:
        return None
    if parts[0] == "output" and len(parts) > 1:
        parts = parts[1:]
    path, name = "/".join(parts), parts[-1]
    ext = name.rsplit(".", 1)[-1].lower()
    if "frontend-angular" in parts:
        return "/".join(parts[parts.index("frontend-angular"):])
    if path.startswith(KNOWN_ROOTS):
        return path
    if ext == "py" or re.fullmatch(r"requirements[\w.\-]*\.txt", name) or name in PYTHON_PROJECT_FILES:
        return python_destination(path)
    if ext == "sql":
        return f"db/{name}"
    if ext in ("ts", "html", "css", "scss"):
        if parts[0] == "src":
            return "frontend-angular/" + path
        if parts[0] == "app":
            return "frontend-angular/src/" + path
        # Nombre sin carpeta: todo en src/app/ para que los imports relativos
        # entre archivos sin carpeta ('./x.service') sigan resolviendo.
        return f"frontend-angular/src/app/{name}"
    return None  # json/yaml/txt sueltos: ambiguos, no se adivinan


def extract_and_save_code(text) -> list[str]:
    """Extrae bloques de código del output del LLM y los guarda en sus carpetas correspondientes."""
    text_str = _unwrap_markdown(str(getattr(text, "raw", text) or ""))
    files: dict[str, str] = {}
    skipped: list[str] = []

    for block in _parse_code_blocks(text_str):
        code, lang, info = block["body"], block["lang"], block["info"]
        if not code.strip():
            continue

        # 1. Comentario de ruta en la primera línea no vacía del bloque.
        first = next((l for l in code.split("\n") if l.strip()), "")
        m = _PATH_COMMENT.match(first)
        name = m.group(1) if m else None
        from_comment = name is not None
        # 2. Ruta en el info string del fence (```python title="api/app/x.py").
        if not name and info:
            m = _FENCE_ATTR.search(info) or _FENCE_BARE_PATH.search(info.split(None, 1)[-1] if " " in info else "")
            name = m.group(1) if m else None
        # Los comandos y árboles de carpetas nunca son archivos.
        if not name and (lang in SHELL_LANGS or re.search(r"[├└│]", code)):
            continue
        # 3. Línea-título justo antes del bloque (no cualquier frase con una ruta).
        if not name and block["prev"]:
            m = _PATH_HEADING.match(block["prev"])
            name = m.group(1) if m else None
        # 4. Contenido inequívoco (SQL, clases Angular).
        if not name:
            name = _guess_name(lang, code)
        if not name:
            if lang in ("python", "py", "typescript", "ts", "html", "css", "scss", "sql"):
                skipped.append(f"bloque {lang} sin ruta (primera línea: {first.strip()[:60]!r})")
            elif lang in ("java", "kotlin", "csharp", "cs", "xml"):
                skipped.append(f"bloque {lang} ignorado: el stack es FastAPI + Angular")
            continue

        dest_rel = code_destination(name)
        if not dest_rel:
            skipped.append(f"{name}: no corresponde a api/, frontend-angular/ ni db/")
            continue
        if from_comment and dest_rel.endswith(".json"):
            code = code.replace(first, "", 1)  # JSON no admite el comentario de ruta
        if dest_rel in files:
            print(f"  ↺ {dest_rel} aparece más de una vez: se conserva la última versión")
        files[dest_rel] = code.strip("\n") + "\n"

    saved = []
    for dest_rel, code in files.items():
        dest = OUTPUT_DIR / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(code, encoding="utf-8")
        saved.append(dest_rel)
        print(f"  💾 Guardado: {dest_rel}")
    for note in skipped:
        print(f"  ⚠ No se guardó {note}")

    if not saved:
        print("  ⚠ Advertencia: no se detectaron archivos de código fuente para extraer en este paso.")
    else:
        print(f"  📦 Total archivos de código generados en este paso: {len(saved)}")

    # Asegurar que el andamiaje base exista siempre
    ensure_scaffolding(OUTPUT_DIR)

    return saved


def save_spec(filename: str, content) -> None:
    specs_dir = OUTPUT_DIR / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    text = str(getattr(content, "raw", content) or "")
    (specs_dir / filename).write_text(text, encoding="utf-8")
    print(f"  ✅ specs/{filename}")


# ── Mini-Crew: corre un único agente/tarea ─────────────────────────

class StepLoadingSpinner:
    """Indicador de carga interactivo con spinner y tiempo transcurrido en tiempo real."""
    def __init__(self, message: str = "Agente procesando con el LLM..."):
        self.message = message
        self.stop_event = threading.Event()
        self.thread = None

    def _spin(self):
        chars = ["|", "/", "-", "\\"]
        idx = 0
        t0 = time.time()
        # Pequeña pausa inicial para que CrewAI imprima sus recuadros iniciales
        time.sleep(1.0)
        while not self.stop_event.is_set():
            elapsed = int(time.time() - t0)
            mins, secs = divmod(elapsed, 60)
            time_str = f"{mins:02d}:{secs:02d}"
            char = chars[idx % len(chars)]
            msg = f"\r  ⏳ [{char}] {self.message} ({time_str} transcurrido)   "
            try:
                sys.stdout.write(msg)
                sys.stdout.flush()
            except Exception:
                pass
            idx += 1
            time.sleep(0.2)
        try:
            sys.stdout.write("\r" + " " * 75 + "\r")
            sys.stdout.flush()
        except Exception:
            pass

    def __enter__(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=1.0)


def run_step(agent, task) -> str:
    """Ejecuta un mini-Crew de un solo agente y retorna el output en texto.

    Ctrl-C cancela la llamada en curso (CrewAI la ejecuta en otro hilo, así que
    se avisa al runtime de Copilot); un segundo Ctrl-C sale de inmediato.
    """
    # Sin reintentos automáticos: ante un error decide la persona (r/n).
    agent.max_retry_limit = 0
    mini_crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
        tracing=False,
    )
    copilot_runtime.CANCEL.clear()

    def on_sigint(_signum, _frame):
        if copilot_runtime.CANCEL.is_set():
            print("\n⏹  Saliendo sin esperar a Copilot.", flush=True)
            copilot_runtime.kill_active_runtimes()
            os._exit(130)
        copilot_runtime.CANCEL.set()
        print("\n⏹  Cancelando el paso... (Ctrl-C otra vez para salir de inmediato)", flush=True)

    in_main = threading.current_thread() is threading.main_thread()
    previous = signal.signal(signal.SIGINT, on_sigint) if in_main else None
    try:
        with StepLoadingSpinner(f"Generando con {agent.llm.model}..."):
            result = mini_crew.kickoff()
    except BaseException:
        if copilot_runtime.CANCEL.is_set():
            raise copilot_runtime.CopilotCancelled("Paso cancelado por la persona (Ctrl-C).") from None
        raise
    finally:
        if in_main:
            signal.signal(signal.SIGINT, previous)
    if copilot_runtime.CANCEL.is_set():
        raise copilot_runtime.CopilotCancelled("Paso cancelado por la persona (Ctrl-C).")

    # Pausa para permitir que los callbacks y paneles asíncronos de CrewAI terminen de pintar en consola
    time.sleep(1.2)

    if hasattr(result, "raw") and result.raw:
        return str(result.raw)
    if hasattr(task, "output") and task.output:
        return str(getattr(task.output, "raw", task.output))
    return str(result)


# ── HITL: aprobación humana ────────────────────────────────────────

def _flush_input_buffer():
    """Limpia caracteres tecleados accidentalmente mientras el LLM generaba."""
    try:
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    except Exception:
        pass


def print_formatted_preview(step_name: str, output: str, max_lines: int = 45) -> None:
    """Muestra el preview con formato enriquecido (tablas redondeadas alineadas, colores, preservando saltos de línea)."""
    output_str = str(getattr(output, "raw", output) or "").strip()
    if not output_str:
        print("  (Sin contenido generado)")
        return

    try:
        from rich.console import Console
        from rich.table import Table
        from rich.box import ROUNDED

        console = Console()
        console.print(f"\n[bold cyan]{'─'*65}[/bold cyan]")
        console.print(f"[bold cyan]▶ OUTPUT GENERADO — {step_name}[/bold cyan]")
        console.print(f"[bold cyan]{'─'*65}[/bold cyan]\n")

        all_lines = output_str.splitlines()
        lines = all_lines[:max_lines]
        hidden_count = max(0, len(all_lines) - max_lines)

        table_lines = []
        in_table = False
        non_table_buffer = []

        def flush_buf():
            if non_table_buffer:
                console.print("\n".join(non_table_buffer))
                non_table_buffer.clear()

        def render_table(tbl_lines):
            if len(tbl_lines) < 2:
                for tl in tbl_lines:
                    console.print(tl)
                return
            headers = [c.strip() for c in tbl_lines[0].split("|")[1:-1]]
            if not headers:
                for tl in tbl_lines:
                    console.print(tl)
                return
            table = Table(show_header=True, header_style="bold magenta", box=ROUNDED, expand=True)
            for i, h in enumerate(headers):
                if i == 0:
                    table.add_column(h, style="cyan", ratio=3)
                elif i == 1 and any(k in h.lower() for k in ("estado", "status", "resultado")):
                    table.add_column(h, justify="center", ratio=1)
                else:
                    table.add_column(h, style="white", ratio=4)

            # Las filas de datos comienzan tras el separador | --- |
            for r in tbl_lines[2:]:
                cols = [c.strip() for c in r.split("|")[1:-1]]
                if len(cols) == len(headers):
                    table.add_row(*cols)
                elif cols:
                    while len(cols) < len(headers):
                        cols.append("")
                    table.add_row(*cols[:len(headers)])
            console.print(table)

        for line in lines:
            st = line.strip()
            if st.startswith("|") and st.endswith("|") and st.count("|") >= 2:
                if not in_table:
                    flush_buf()
                    in_table = True
                table_lines.append(st)
            else:
                if in_table:
                    render_table(table_lines)
                    table_lines.clear()
                    in_table = False
                non_table_buffer.append(line)

        if in_table:
            render_table(table_lines)
        flush_buf()

        if hidden_count > 0:
            console.print(f"\n[dim italic]... [{hidden_count} líneas adicionales guardadas en specs/ y código][/dim italic]")

        console.print(f"\n[bold cyan]{'─'*65}[/bold cyan]")

    except Exception:
        # Fallback sin formato especial si falla Rich
        sep = "─" * 65
        print(f"\n{sep}\n▶ OUTPUT GENERADO — {step_name}\n{sep}")
        print("\n".join(output_str.splitlines()[:max_lines]))
        print(sep)


def hitl_approve(step_name: str, output: str) -> tuple[str, str]:
    """
    Muestra un preview del output y pide aprobación de forma clara e interactiva.

    Retorna:
        ("s", "")         → aprobado
        ("n", "")         → rechazado (abortar)
        ("r", feedback)   → reintentar el paso (con feedback opcional del usuario)
    """
    import time
    time.sleep(0.3)

    print_formatted_preview(step_name, output)

    box_line = "=" * 65
    banner = f"""
{box_line}
 🔔 ACCIÓN REQUERIDA — Aprobación humana para: {step_name}
{box_line}
 [s] = Aprobar y continuar al siguiente paso
 [r] = Reintentar este mismo paso (permite ingresar feedback opcional)
 [n] = Rechazar y detener ejecución
{box_line}"""
    print(banner)

    while True:
        _flush_input_buffer()
        try:
            raw = input("\n👉 Ingresa tu opción [s/r/n] y presiona Enter: ").strip().lower()
        except EOFError:
            print("\n❌ Entrada cerrada: no se puede aprobar sin una persona. Deteniendo.")
            return "n", ""
        except KeyboardInterrupt:
            print("\n❌ Interrupción por teclado.")
            return "n", ""

        tokens = raw.split()
        choice = tokens[-1] if tokens else ""

        if not choice:
            continue

        if choice in ("s", "si", "sí", "y", "yes", "1") or choice.endswith("s"):
            return "s", ""
        if choice in ("n", "no", "0") or choice.endswith("n"):
            return "n", ""
        if choice in ("r", "retry", "reintentar") or choice.endswith("r"):
            print("\n💬 [Feedback Opcional] Escribe instrucciones adicionales para el agente")
            try:
                feedback = input("   (o presiona Enter para reintentar sin cambios): ").strip()
            except (EOFError, KeyboardInterrupt):
                feedback = ""
            return "r", feedback

        print("\n  ✗ Opción inválida. Por favor ingresa 's' para sí, 'r' para reintentar o 'n' para rechazar.")



def ask(prompt: str) -> str:
    """input() que termina el flujo con un mensaje claro si la entrada se cierra."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\n❌ Entrada cancelada. Deteniendo el flujo; los pasos aprobados quedan en el checkpoint.")
        raise SystemExit(1)


def handle_step_error(step_label: str, error: BaseException) -> tuple[str, str]:
    """Muestra el error del paso y deja decidir: reintentar o detener."""
    box_line = "=" * 65
    if isinstance(error, KeyboardInterrupt):
        reason = "cancelado con Ctrl-C"
    else:
        reason = f"{type(error).__name__}: {error}"
    print(f"""
{box_line}
 ⚠  El paso {step_label} no terminó: {reason}
{box_line}
 [r] = Reintentar este paso (permite ingresar feedback opcional)
 [n] = Detener (los pasos aprobados quedan guardados en el checkpoint)
{box_line}""")
    while True:
        choice = ask("\n👉 Ingresa tu opción [r/n] y presiona Enter: ").lower()
        if choice in ("r", "retry", "reintentar", "s", "si", "sí"):
            try:
                feedback = input("   Feedback opcional (Enter para reintentar sin cambios): ").strip()
            except (EOFError, KeyboardInterrupt):
                feedback = ""
            return "r", feedback
        if choice in ("n", "no"):
            return "n", ""
        print("  ✗ Opción inválida. Ingresa 'r' o 'n'.")


# ── Contexto acumulado ─────────────────────────────────────────────

def _ctx_snippet(text: str, max_chars: int = 80000) -> str:
    """Recorta el output a max_chars para inyectarlo como contexto."""
    text_clean = str(text or "").strip()
    if len(text_clean) <= max_chars:
        return text_clean
    return text_clean[:max_chars] + "\n...(truncado para contexto)"


def build_context_note(approved_outputs: dict) -> str:
    """Construye una nota de contexto con los outputs aprobados anteriores."""
    parts = []
    labels = {key: label for key, label, *_ in workflow_steps(True)}
    for key, label in labels.items():
        if key in approved_outputs:
            val = str(getattr(approved_outputs[key], "raw", approved_outputs[key]) or "")
            parts.append(f"### {label}\n{_ctx_snippet(val)}")
    if not parts:
        return ""
    return "\n\n---\n## Contexto de pasos anteriores\n\n" + "\n\n".join(parts)



# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    with_data = include_data()
    steps = workflow_steps(with_data)
    # ── MCP Proyectos: descubrir tools ────────────────────────────────
    print("\n[MCP Proyectos] Autenticando...")
    _proj_tools = proj_tools()
    if VERBOSE_MCP_TOOLS:
        print("[MCP Proyectos] Herramientas disponibles:")
        for t in _proj_tools:
            print(f"  · {t['name']}: {t['description']}")
    else:
        print("[MCP Proyectos] Herramientas cargadas correctamente.")

    # ── Selección de proyecto ─────────────────────────────────────────
    projects = list_projects()
    if not projects:
        print("[MCP Proyectos] ✗ No se encontraron proyectos.")
        raise SystemExit(1)

    if len(projects) == 1:
        selected_project = projects[0]
        print(f"\n[MCP Proyectos] Proyecto asignado: {selected_project['title']}")
    else:
        print("\n[MCP Proyectos] Proyectos disponibles:")
        for i, proj in enumerate(projects, 1):
            icon = "⚫" if proj.get("closed") else "🟢"
            print(f"  {i}. {icon} {proj.get('title', '(sin título)')}")
        while True:
            sel = ask(f"\nSelecciona el número de proyecto [1-{len(projects)}]: ")
            if sel.isdigit() and 1 <= int(sel) <= len(projects):
                selected_project = projects[int(sel) - 1]
                break
            print(f"  ✗ Entrada inválida.")

    # ── Selección de feature del backlog ─────────────────────────────
    backlog = list_project_items(selected_project["id"])
    if not backlog:
        print("[MCP Proyectos] ✗ El proyecto no tiene items en el backlog.")
        raise SystemExit(1)

    print(f"\n[MCP Proyectos] Backlog de '{selected_project['title']}':")
    for i, item in enumerate(backlog, 1):
        icon = "⚫" if item.get("state", "").lower() == "closed" else "🟢"
        num  = f"#{item['number']} — " if item.get("number") else ""
        print(f"  {i}. {icon} {num}{item.get('title', '(sin título)')}")

    while True:
        sel = ask(f"\nSelecciona el número de feature [1-{len(backlog)}]: ")
        if sel.isdigit() and 1 <= int(sel) <= len(backlog):
            selected_item = backlog[int(sel) - 1]
            break
        print(f"  ✗ Entrada inválida.")

    feature = get_feature_from_item(selected_item)
    print(f"\n[MCP Proyectos] Feature cargado: {feature['title']}")
    print(f"[MCP Proyectos] Criterios de aceptación: {feature['acceptance_criteria']}")

    # ── Cargar checkpoint ─────────────────────────────────────────────
    checkpoint  = load_checkpoint()
    steps_state = checkpoint.get("steps", {})

    # Verificar si el checkpoint corresponde a este feature (por título)
    ckpt_feature = checkpoint.get("feature_title")
    if ckpt_feature and ckpt_feature != feature["title"]:
        print(f"\n⚠  El checkpoint existente es para '{ckpt_feature}'.")
        ans = ask("¿Ignorar checkpoint y empezar desde cero? [s/n]: ").lower()
        if ans == "s":
            steps_state = {}
            checkpoint  = {"steps": {}}
        else:
            print("Abortando. Cambia de feature o elimina output/.checkpoint.json para reiniciar.")
            raise SystemExit(0)

    mode = "with-data" if with_data else "standard"
    previous_mode = checkpoint.get("workflow_mode", "standard")
    if steps_state and previous_mode != mode:
        print("El checkpoint pertenece a otro flujo. Conserva output/ moviéndolo a otra carpeta antes de cambiar CREWAI_INCLUDE_DATA.")
        raise SystemExit(1)
    checkpoint["workflow_mode"] = mode
    checkpoint["feature_title"] = feature["title"]

    # ── Recuperar outputs aprobados del checkpoint ────────────────────
    approved_outputs: dict = {}
    for step_key, step_data in steps_state.items():
        if step_data.get("status") == "approved":
            approved_outputs[step_key] = step_data.get("output", "")

    # ── Definición de pasos ───────────────────────────────────────────
    # (key, label, agent, spec_filename, extraer_código)


    # Andamiaje de build: en este punto, con proyecto y feature ya elegidos.
    ensure_scaffolding(OUTPUT_DIR)

    print("\n" + "=" * 60)
    print(f"S1 CrewAI — HITL — Feature: {feature['title']}")
    print("Pasos: " + " → ".join(step[1] for step in steps))
    print("=" * 60)

    generated_files: list[str] = []

    # ── Loop HITL ─────────────────────────────────────────────────────
    for step_key, step_label, agent, spec_file, do_code in steps:

        # ── Ya aprobado en ejecución anterior → omitir ───────────────
        if steps_state.get(step_key, {}).get("status") == "approved":
            print(f"\n✅ [{step_label}] — ya aprobado (checkpoint). Omitiendo.")
            if do_code:
                saved_out = steps_state[step_key].get("output", "")
                if saved_out:
                    generated_files.extend(extract_and_save_code(saved_out))
            continue

        print(f"\n{'─'*60}")
        print(f"▶ PASO: {step_label}")
        print(f"{'─'*60}")

        # ── Bucle de reintentos ───────────────────────────────────────
        user_feedback = ""
        while True:
            # Rebuild tasks fresh en cada intento
            task_map = build_tasks(feature, with_data)
            task = task_map[step_key]

            # Inyectar contexto de pasos anteriores en la descripción
            ctx_note = build_context_note(approved_outputs)
            if ctx_note:
                task.description = task.description + ctx_note

            if with_data and step_key == "backend":
                task.description += "\nUsa el diseño de persistencia aprobado de Datos y persistencia. No regeneres sus archivos SQL; implementa el acceso a datos según ese contrato."
            if with_data and step_key == "chapter":
                task.description += "\nRevisa también el modelo, migración y compatibilidad del contrato aprobado de Datos y persistencia con backend."

            # Si el usuario ingresó feedback opcional en un reintento, inyectarlo como directiva prioritaria
            if user_feedback:
                task.description += (
                    f"\n\n---\n## ⚠️ INSTRUCCIONES ESPECÍFICAS DE CORRECCIÓN (FEEDBACK HUMANO):\n"
                    f"{user_feedback}\n"
                    f"Por favor atiende y corrige con máxima prioridad las observaciones del usuario indicadas arriba.\n"
                )

            # Ejecutar mini-Crew; un error o Ctrl-C no tumba el flujo
            try:
                output = run_step(agent, task)
            except (Exception, KeyboardInterrupt) as error:
                decision, user_feedback = handle_step_error(step_label, error)
                if decision == "n":
                    print(f"\n❌ {step_label} detenido tras un error. Vuelve a ejecutar para retomarlo.")
                    raise SystemExit(1)
                print(f"\n🔄 Reintentando {step_label}...")
                continue

            # HITL
            decision, user_feedback = hitl_approve(step_label, output)

            if decision == "s":
                # APROBADO
                print(f"\n✅ {step_label} aprobado. Guardando artefactos...")
                save_spec(spec_file, output)
                if do_code:
                    generated_files.extend(extract_and_save_code(output))
                approved_outputs[step_key] = output
                steps_state[step_key] = {"status": "approved", "output": output}
                checkpoint["steps"] = steps_state
                save_checkpoint(checkpoint)
                break

            elif decision == "n":
                # RECHAZADO
                print(f"\n❌ {step_label} rechazado. Abortando ejecución.")
                steps_state[step_key] = {"status": "rejected", "output": output}
                checkpoint["steps"] = steps_state
                save_checkpoint(checkpoint)
                raise SystemExit(0)

            else:
                # REINTENTAR
                if user_feedback:
                    print(f"\n🔄 Reintentando {step_label} incorporando tu feedback: \"{user_feedback}\"...")
                else:
                    print(f"\n🔄 Reintentando {step_label}...")
                # el while True vuelve a ejecutar el paso

    # ── Todos los pasos aprobados ─────────────────────────────────────
    chapter_text = str(getattr(approved_outputs.get("chapter", ""), "raw", approved_outputs.get("chapter", "")) or "")

    print("\n" + "=" * 60)
    print("✅ TODOS LOS PASOS APROBADOS")
    print("=" * 60)
    print("  output/specs/            → " + " · ".join(step[3] for step in steps))
    print("  output/api/              → archivos .py extraídos (FastAPI)")
    print("  output/frontend-angular/ → archivos .ts/.html extraídos")
    print("  output/db/               → .sql extraídos")
    print("=" * 60)
    print("\nVEREDICTO del Chapter (extracto):")
    print(chapter_text[-500:] if len(chapter_text) > 500 else chapter_text)

    publish_step(checkpoint, feature, selected_item.get("number"), steps, generated_files, chapter_text)


def publish_step(checkpoint: dict, feature: dict, issue_number, steps, generated_files, chapter_text) -> None:
    """Último paso: PR en borrador a <GITHUB_OWNER>/ai-labs, solo con aprobación humana."""
    repo = publish_pr.target_repo()
    print("\n" + "─" * 60)
    print("▶ PASO: Pull request")
    print("─" * 60)
    if checkpoint.get("pr", {}).get("url"):
        print(f"✅ PR ya abierto en una ejecución anterior: {checkpoint['pr']['url']}")
        return
    if not repo:
        print("  ⚠ Define GITHUB_OWNER en .env para abrir el PR en <owner>/ai-labs. Paso omitido.")
        return

    slug = publish_pr.slugify(feature["title"])
    files = publish_pr.plan_files(OUTPUT_DIR, generated_files, [step[3] for step in steps], slug)
    verdict = publish_pr.verdict(chapter_text)
    box_line = "=" * 65
    print(f"  Repo destino : {repo} (PR en borrador)")
    print(f"  Veredicto    : {verdict}")
    print(f"  Archivos ({len(files)}):")
    for path in files:
        print(f"    · {path}")
    if verdict != "APROBADO":
        print(f"\n  ⚠ El Chapter no aprobó ({verdict}). Puedes abrir el PR igualmente para revisión humana.")
    print(f"""
{box_line}
 🔔 ACCIÓN REQUERIDA — Aprobación humana para abrir el PR
{box_line}
 [s] = Abrir el PR en {repo}
 [n] = No abrir el PR (puedes volver a ejecutar más tarde)
{box_line}""")
    while True:
        try:
            choice = input("\n👉 ¿Abrir el PR? [s/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = "n"
        if choice in ("s", "si", "sí", "y", "yes"):
            break
        if choice in ("n", "no"):
            print("  PR no abierto.")
            return
        print("  ✗ Ingresa 's' o 'n'.")

    try:
        url = publish_pr.open_pr(repo, feature, issue_number, files, chapter_text)
    except publish_pr.PublishError as error:
        print(f"\n❌ No se pudo abrir el PR: {error}")
        return
    print(f"\n✅ PR abierto: {url}")
    checkpoint["pr"] = {"url": url, "repo": repo}
    save_checkpoint(checkpoint)


if __name__ == "__main__":
    main()
