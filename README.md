# wallet-app (plantilla Hackathon)

Esqueleto autocontenido derivado de `crewai-grupo-06`. Genera una billetera (FastAPI + Angular 17)
con agentes CrewAI a partir del backlog del proyecto `wallet-app`.

Orden del flujo: `architect → backend → frontend → testing → security → chapter`
(con `data` al inicio si `CREWAI_INCLUDE_DATA=true`). Cada etapa pide aprobación humana (`s`/`n`/`r`).

## Arranque rápido

Requiere Python 3.11–3.13, Git, Copilot CLI (`copilot` → `/login`) y el MCP Projects activo.

```bash
cd wallet-app
python -m venv .venv
source .venv/Scripts/activate   # Git Bash en Windows; en macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env            # completa GITHUB_OWNER, PROJECTS_MCP_URL y PROJECTS_MCP_API_KEY
python tools/verify.py          # comprobación sin credenciales
python main.py
```

## Estructura

- `agents/`: un archivo por rol (instrucciones y tarea). Edita aquí el prompt de cada agente.
- `crew/`: orden del flujo, configuración del LLM y publicación del PR.
- `lab_copilot/`: runtime de Copilot.
- `mcp_projects.py`: cliente del backlog MCP.
- `support/mcp-local/`: MCP local (requiere Podman/Docker y la imagen del instructor).
- `tests/` y `tools/verify.py`: verificación del flujo.
- `output/`: artefactos generados (specs, `api/`, `frontend-angular/`, `db/`). Está ignorado por git.

## Probar lo generado

```sh
cd output/api && pip install -r requirements.txt && pytest && uvicorn app.main:app --reload
cd output/frontend-angular && npm install && npm start
```

API en `http://localhost:8000`, Angular en `http://localhost:4200`.

## Referencias

Detalle completo en [MEJORA_TU_AGENTE.md](MEJORA_TU_AGENTE.md), [TEAM.md](TEAM.md) y [SOURCE.md](SOURCE.md).
`.env` nunca se commitea.
