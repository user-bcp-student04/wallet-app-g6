## Context

- `wallet-app-g6` es un generador CrewAI. `main.py` carga un feature del backlog (MCP Projects), cada agente genera artefactos en `output/` y `crew/publish_pr.py` los publica mediante PR en el repo destino (`GITHUB_OWNER`/`PR_REPO`, por defecto `ai-labs`).
- No existe lógica de onboarding, estado de wallet ni eventos analíticos en este repositorio.
- El código de producto se genera hacia `api/` (FastAPI), `web/` (Angular) y `db/`; las specs van a `docs/crewai/<slug>/`.
- Spec de entrada: `specs/wallet-onboarding/spec.md`.

## Goals / Non-Goals

**Goals**

- Cumplir la spec con el cambio mínimo, sin reescribir el generador.
- Mantener intactos los contratos del pipeline.
- Entregar en pasos pequeños y reversibles, cada uno con aprobación humana.

**Non-Goals**

- Reescribir o rediseñar el motor (`main.py`, `crew/`).
- Pago por contacto o QR, recarga, validación de acceso en transporte y conciliación.
- Definir los requisitos de KYC.
- Resolver deuda técnica fuera del Issue.

## Protected Contracts

- `crew/workflow.py`: orden de etapas y semántica de `CREWAI_INCLUDE_DATA` (`true`/`false`; otro valor lanza `ValueError`).
- Contrato de cada agente: `KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, `agent`, `build_task(feature)`.
- Entregables: `user_story.md`, `data_spec.md`, `backend_spec.md`, `frontend_spec.md`, `testing_report.md`, `security_report.md`, `chapter_review.md`.
- Línea `VEREDICTO: APROBADO` / `VEREDICTO: RECHAZADO` y su lectura en `publish_pr.verdict()`.
- `crew/publish_pr.py`: `PATH_MAP`, `SPECS_DIR` y resolución del repo destino.
- Formato de extracción de código (ruta completa del archivo en el bloque).
- Cuerpo de error `{"code","message"}` del API generado.
- `tools/verify.py` y los tests existentes.
- Estructura de cambio OpenSpec y regla de una historia a la vez.
- Contratos nuevos (API de onboarding, esquema de eventos, salida analítica): se definen aquí sin alterar los anteriores.

## Decisions

### Decision: Implementar el onboarding en el repo destino

- Opción elegida: el código de onboarding se genera y publica en el repo destino mediante el pipeline existente, con H01 como feature. El repo destino es `user-bcp-student04/wallet-app-g6` (`GITHUB_OWNER=user-bcp-student04`, `PR_REPO=wallet-app-g6`), el mismo que aloja el generador. El motor no cambia.
- Motivo: este repo es un generador sin código de producto; el mapeo de `publish_pr.py` ya envía `api/`, `web/`, `db/` y specs al repo destino. Respeta los contratos protegidos y es el cambio mínimo.
- Alternativas consideradas: implementar dentro de `wallet-app-g6` (descartada por decisión humana: mezclaría producto y generador y exigiría cambiar contratos protegidos).
- Consecuencias: el producto se publica por PR en `api/`, `web/`, `db/` y `docs/crewai/<slug>/` de la raíz del repo, separado del generador (`agents/`, `crew/`, `main.py`, `tools/`). Se editan instrucciones de agentes solo si la salida no cubre la spec.

### Decision: Activar el rol de Datos y persistencia

- Opción elegida: `CREWAI_INCLUDE_DATA=true`; flujo de siete etapas (Arquitectura, Datos, Backend, Frontend, Pruebas, Seguridad, Chapter).
- Motivo: el estado de wallet y los eventos de onboarding requieren persistencia; Datos produce `data_spec.md` y propuestas SQL en `output/db/` que Backend consume y Chapter revisa.
- Alternativas consideradas: flujo de seis etapas, con Backend cubriendo la persistencia (descartada por decisión humana).
- Consecuencias: Datos no ejecuta migraciones; no se reutiliza un checkpoint de seis etapas, y no existe `output/` previo.

No se registra ADR adicional: no hay otra decisión significativa tomada.

## Incremental Strategy

1. Ejecutar `python tools/verify.py` y guardar la línea base.
2. Configurar `.env` con `GITHUB_OWNER=user-bcp-student04` y `PR_REPO=wallet-app-g6`, y cerrar las preguntas bloqueantes de la spec.
3. Ejecutar el pipeline con H01 y revisar cada etapa con aprobación humana.
4. Solo si la salida no cubre la spec, ajustar las instrucciones del agente afectado sin cambiar su contrato, en un PR pequeño por agente coordinado con el arquitecto.
5. Entregar el producto en este orden: estado de wallet y validación de pasos, eventos, salida analítica, interfaz.

## Required Tests

- Antes de modificar: los tests existentes de `tests/test_workflow.py`, `tests/test_publish.py` y `tests/test_extract.py` pasan; si se editan instrucciones, una prueba fija el contrato de agente.
- Producto generado: pasos visibles; bloqueo con dato faltante e inválido; estado activo solo tras onboarding exitoso; eventos de inicio, paso y cierre (incluido abandono); cálculo de mediana; salida mensual de nuevos usuarios activos y gasto atribuido.
- Una persona ejecuta las pruebas y adjunta la salida real al PR.

## Risks / Trade-offs

- Repo destino igual al repo del generador: el PR añade `api/`, `web/`, `db/` y `docs/crewai/` junto al código del pipeline -> el PR no debe modificar `agents/`, `crew/`, `main.py` ni `tools/` salvo ajustes aprobados; `PR_REPO` por defecto es `ai-labs`, por lo que debe definirse explícitamente.
- Instrucciones del Arquitecto orientadas a otro caso (subida de archivos, dependencias) -> evaluar la salida y ajustar solo si es necesario.
- Datos personales en eventos sin tratamiento definido -> definirlo con seguridad y cumplimiento.
- KYC sin definir impide concretar pasos y datos obligatorios -> bloquear esa parte hasta su definición.
- Métricas de duración y CAC no verificables sin frontera de eventos ni fuente de gasto -> cerrar las preguntas de la spec.
- Salida del modelo no determinista -> revisión humana por etapa y pruebas ejecutadas.
- Cambiar entre flujo de seis y siete etapas invalida el checkpoint -> conservar `output/` con otro nombre antes de cambiar de modo.

## Rollback

Cada cambio va en un PR separado y se revierte por PR. El generador no ejecuta migraciones, por lo que no hay reversión de datos desde este repositorio.

## Open Questions

1. ¿Se editan las instrucciones del Arquitecto o solo se alimenta el feature?
2. Preguntas de la spec: frontera de eventos de duración; pasos y KYC; definición de "usuario activo" y fuente del gasto de adquisición; muestra de la mediana.
3. ¿Se confirma el listado de contratos protegidos?
