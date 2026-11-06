## Context

- `wallet-app-g6` es un generador CrewAI. `main.py` carga un feature del backlog (MCP Projects), cada agente genera artefactos en `output/` y `crew/publish_pr.py` los publica mediante PR en el repo destino (`GITHUB_OWNER`/`PR_REPO`, por defecto `ai-labs`).
- No existe lógica de onboarding, estado de wallet ni eventos analíticos en este repositorio.
- El código de producto se genera hacia `api/` (FastAPI), `web/` (Angular) y `db/`; las specs van a `docs/crewai/<slug>/`.
- Spec de entrada: `specs/wallet-onboarding/spec.md`.
- Fuente de contrato para KYC y wallet: mock W1 en `docs/bcp-wallet-mock-openapi.yaml` y `docs/H1_registro` (en memoria, sin autenticación, importes en céntimos PEN, límite de 2000 recursos por grupo).
- El mock no registra eventos de onboarding ni calcula duración, MAU o CAC; eso lo implementa la aplicación.

## Goals / Non-Goals

**Goals**

- Cumplir la spec con el cambio mínimo, sin reescribir el generador.
- Mantener intactos los contratos del pipeline.
- Entregar una consola Angular básica que pruebe cada servicio W1 del mock.
- Cobertura básica de pruebas por endpoint.
- Entregar en pasos pequeños y reversibles, cada uno con aprobación humana.

**Non-Goals**

- Reescribir o rediseñar el motor (`main.py`, `crew/`).
- Pago por contacto o QR, recarga, validación de acceso en transporte y conciliación.
- Reglas de KYC reales.
- Resolver deuda técnica fuera del Issue.

## Protected Contracts

- `crew/workflow.py`: orden de etapas y semántica de `CREWAI_INCLUDE_DATA` (`true`/`false`; otro valor lanza `ValueError`).
- Contrato de cada agente: `KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, `agent`, `build_task(feature)`.
- Entregables: `user_story.md`, `data_spec.md`, `backend_spec.md`, `frontend_spec.md`, `testing_report.md`, `security_report.md`, `chapter_review.md`.
- Línea `VEREDICTO: APROBADO` / `VEREDICTO: RECHAZADO` y su lectura en `publish_pr.verdict()`.
- `crew/publish_pr.py`: `PATH_MAP`, `SPECS_DIR` y resolución del repo destino.
- Formato de extracción de código (ruta completa del archivo en el bloque).
- Cuerpo de error `{"code","message"}` del API generado; la consola lee aparte el cuerpo de error del mock (`error`) y no lo mezcla con el anterior.
- `tools/verify.py` y los tests existentes.
- Contrato del mock W1 (`docs/bcp-wallet-mock-openapi.yaml`, `docs/H1_registro`): solo lectura.
- Estructura de cambio OpenSpec y regla de una historia a la vez.
- Contratos nuevos (API de onboarding, esquema de eventos, salida analítica): se definen aquí sin alterar los anteriores.
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

### Decision: Consola Angular que consume el mock directamente

- Opción elegida (propuesta, pendiente de aprobación humana): una app Angular en `web/` con un `MockApiService` tipado (un método por endpoint W1), un `SessionService` único (URL base, latencia, últimos `id` y `wallet_id`), un `OnboardingEventsService` (inicio, paso y cierre con `userId` y marca de tiempo) y componentes de presentación: configuración, flujo guiado y consola de servicios. Los componentes no llaman HTTP directo.
- Motivo: la historia pide probar los servicios del mock sin autenticación; el mock es el contrato fuente y no hay API propia que lo intermedie. Respeta `docs/GOOD_PRACTICES.md` (tipado estricto, servicios, `environment.ts`, sin `[innerHTML]`).
- Alternativas consideradas: pasar por `api/` (FastAPI) como proxy (descartada por ahora: agrega una capa y no la pide la historia; se reevaluará si el mock no admite CORS).
- Consecuencias: la URL base vive en `environment.ts` y es editable en la consola; los eventos se guardan provisionalmente en almacenamiento local del navegador hasta cerrar la pregunta de persistencia; el cálculo de duración y mediana parte de esos eventos.

### Contratos nuevos (borrador)

- Evento de onboarding: `{ type: "STARTED" | "STEP_COMPLETED" | "CLOSED", userId, step?, timestamp }`. `userId` es el `id` de verificación cuando existe, o un identificador de sesión antes de la verificación.
- Duración: diferencia entre `STARTED` y `CLOSED` del mismo `userId`; la frontera oficial se fija al cerrar la pregunta abierta.
- Salida analítica mensual: `{ month, newActiveUsers, attributedSpendPen }` y `CAC = attributedSpendPen / newActiveUsers`; la fuente del gasto está pendiente.

## Cobertura básica por endpoint

Una prueba de camino feliz y una de error por endpoint, con `HttpTestingController` sobre `MockApiService`; las pruebas de componente cubren el mensaje accionable y la habilitación de pagos.

| Endpoint | Camino feliz | Camino de error |
| --- | --- | --- |
| `GET /health` | `200`, muestra `status: ok` | `400` por latencia inválida, bloqueada en cliente |
| `GET /scenarios` | `200`, llena el selector de escenarios KYC | error de red, mensaje legible |
| `POST /kyc/verifications` | `201` `APPROVED` con `ACTIVE`; `201` `REJECTED` y `MANUAL_REVIEW` | `503 KYC_UNAVAILABLE`; `400` por documento sin `TEST-` |
| `GET /kyc/verifications/{id}` | `200` con `id`, `wallet_id`, `scenario`, `status` | `404 NOT_FOUND` |
| `POST /kyc/verifications/{id}/decision` | `200` con `ACTIVE` sobre `PENDING` | `409 DECISION_CONFLICT` al cambiar una decisión final |
| `GET /wallets/{id}` | `200`, saldos 0 y `currency` `PEN` | `404 NOT_FOUND` |
| `GET /support/cases` | `200` con caso `KYC_REVIEW` `OPEN`; lista vacía `[]` | error de red, mensaje legible |
| `POST /control/reset` | `200`, limpia identificadores y eventos locales | cancelación de la confirmación: no llama a la API |

Transversal: `413` y `429 GROUP_LIMIT_RESET_REQUIRED` se prueban una vez sobre el manejador de errores común.

## Incremental Strategy

1. Ejecutar `python tools/verify.py` y guardar la línea base.
2. Configurar `.env` con `GITHUB_OWNER=user-bcp-student04` y `PR_REPO=wallet-app-g6`, y cerrar las preguntas bloqueantes de la spec.
3. Ejecutar el pipeline con H01 y revisar cada etapa con aprobación humana.
4. Solo si la salida no cubre la spec, ajustar las instrucciones del agente afectado sin cambiar su contrato, en un PR pequeño por agente coordinado con el arquitecto.
5. Entregar el producto en este orden: servicio tipado del mock y estado de wallet, validación de pasos, KYC y decisión, eventos, consola de servicios, salida analítica.

## Required Tests

- Antes de modificar: los tests existentes de `tests/test_workflow.py`, `tests/test_publish.py` y `tests/test_extract.py` pasan; si se editan instrucciones, una prueba fija el contrato de agente.
- Producto generado: pasos visibles; bloqueo con dato faltante, inválido y documento sin `TEST-`; escenarios KYC `APPROVED`, `REJECTED`, `MANUAL_REVIEW` con decisión, y `UNAVAILABLE`; estado `ACTIVE` solo tras onboarding exitoso; eventos de inicio, paso y cierre (incluido abandono); cálculo de mediana; salida mensual de nuevos usuarios activos y gasto atribuido.
- Cobertura básica por endpoint según la tabla anterior (camino feliz y un camino de error por servicio).
- Una persona ejecuta las pruebas y adjunta la salida real al PR.

## Risks / Trade-offs

- Repo destino igual al repo del generador: el PR añade `api/`, `web/`, `db/` y `docs/crewai/` junto al código del pipeline -> el PR no debe modificar `agents/`, `crew/`, `main.py` ni `tools/` salvo ajustes aprobados; `PR_REPO` por defecto es `ai-labs`, por lo que debe definirse explícitamente.
- Instrucciones del Arquitecto orientadas a otro caso (subida de archivos, dependencias) -> evaluar la salida y ajustar solo si es necesario.
- Datos personales en eventos sin tratamiento definido -> definirlo con seguridad y cumplimiento.
- KYC real sin definir impide concretar pasos y datos obligatorios adicionales -> se usa solo el KYC simulado y se bloquea el resto hasta su definición.
- Mock sin CORS o caído por inactividad (datos en memoria) -> proxy de desarrollo si hace falta, y repetir el escenario tras un reinicio.
- Límite de 2000 recursos por grupo -> usar `POST /control/reset` con confirmación; el reset borra datos de todo el grupo.
- Eventos en almacenamiento local no sirven para MAU y CAC reales -> definir persistencia antes de producción.
- Métricas de duración y CAC no verificables sin frontera de eventos ni fuente de gasto -> cerrar las preguntas de la spec.
- Salida del modelo no determinista -> revisión humana por etapa y pruebas ejecutadas.
- Cambiar entre flujo de seis y siete etapas invalida el checkpoint -> conservar `output/` con otro nombre antes de cambiar de modo.

## Rollback

Cada cambio va en un PR separado y se revierte por PR. El generador no ejecuta migraciones, por lo que no hay reversión de datos desde este repositorio.

## Open Questions

1. ¿Se editan las instrucciones del Arquitecto o solo se alimenta el feature?
2. Preguntas de la spec: frontera de eventos de duración; pasos adicionales al KYC simulado; espera de una wallet `PENDING`; persistencia de eventos y URL base cloud/local; CORS del mock; definición de "usuario activo" y fuente del gasto de adquisición; muestra de la mediana.
3. ¿Se confirma el listado de contratos protegidos?
