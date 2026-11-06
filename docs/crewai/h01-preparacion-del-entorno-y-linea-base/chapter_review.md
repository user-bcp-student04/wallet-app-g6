# chapter_review.md

**Feature:** [H01] Preparación del entorno y línea base
**Rol:** Chapter, revisor transversal del Issue
**Fecha de la revisión:** 2026-11-06
**Spec:** `openspec/changes/registro-activacion-wallet/specs/wallet-onboarding/spec.md`
**Tareas:** `openspec/changes/registro-activacion-wallet/tasks.md` (grupo 1)

> **Naturaleza de este informe.** Es una auditoría por lectura. No ejecuté nada y no afirmo que algo se haya ejecutado. Todo resultado de comando es **NO EJECUTADO** y lo que figura como "esperado" es una predicción. **Este informe no sustituye ninguna aprobación humana.**
>
> **Material recibido.** No llegó truncado. Recibí el Issue, el análisis del Arquitecto, la especificación del Backend, la del Frontend, el informe de Pruebas con su código completo y el informe de Seguridad.
>
> **Material no recibido (no invento su contenido).** No vi `spec.md`, `tasks.md` real, `tools/verify.py`, `environment.ts`, el mock W1, `api/app/*`, `.gitignore` ni `requirements*.txt`.

---

## 1. Supuesto confirmado de stack

- El API es Python con FastAPI en `api/`, decisión del equipo ya confirmada por una persona.
- Revisé los cinco entregables. Ninguno mezcla Java, Maven o Quarkus con Python, y ninguno implementa otro stack.
- Backend y Pruebas traducen de forma explícita las equivalencias legadas: no hay SQL ni `PreparedStatement`, y se usa `pytest` en lugar de `mvn test`.
- Esto se registra como **supuesto confirmado**. No es contradicción ni motivo de rechazo por stack.

---

## 2. Cobertura por criterio de aceptación

El Issue no enumera criterios por separado. Cada tarea 1.1 a 1.4 se toma como criterio, igual que hace el Arquitecto.

| Criterio | Arquitectura | Persistencia | Implementación | Pruebas | Seguridad | Cobertura de diseño |
|---|---|---|---|---|---|---|
| **1.1** `.env` con `GITHUB_OWNER=user-bcp-student04`, `PR_REPO=wallet-app-g6`, `CREWAI_INCLUDE_DATA=true` | Componente `.env` con límite de tres variables. `.gitignore` y `.env.example` fuera de alcance. | No aplica: archivo local, sin BD ni migración. | Backend entrega las tres líneas exactas. | T-02 a T-09 y T-37 (lógica), T-17 y T-18 (fase 2), V-12 (`grep -cE` → 3). | SEC-02 (no versionado), SEC-07 (sin valores en mensajes), SEC-01 (semántica de `CREWAI_INCLUDE_DATA`). | **Cubierto.** Pendiente ejecución. |
| **1.2** `python tools/verify.py` ejecutado y línea base registrada | `verify.py` no se modifica. Registro en `baseline.md` (ruta **[Supuesto]**). | No aplica. | Backend entrega la plantilla con `<RELLENAR>`, que es un marcador de ejecución y no de diseño. | T-01, T-10, T-11, T-12, T-27, M-1. Regla de fases y S12 (no invocar `verify.py` desde pytest). | SEC-03 (salida sensible en `baseline.md`). | **Cubierto.** Ver OBS-05 (orden `.env`/línea base). |
| **1.3** Seis preguntas bloqueantes cerradas | Tabla de seis decisiones conservadoras. Según el Arquitecto, cerradas en `spec.md` con responsable y fecha 2026-11-06. | Decisión "eventos en memoria, sin migración". Coherente con la ausencia de SQL del Backend y con T-25. | Entregable documental en `spec.md`, **que no recibí**. | T-13, T-14, T-15, T-28, T-29, T-39. | SEC-04 (CORS), SEC-05 (identidad y gasto en servidor), SEC-01. | **Cubierto en diseño.** El contenido de la spec no es verificable aquí. Ver OBS-03 y OBS-04. |
| **1.4** Mock W1 responde a `GET /health` y URL fijada en `environment.ts` | Contrato `GET /health`: **[Supuesto]** `200`, sin autenticación, cuerpo no especificado. `environment.ts` a cargo del rol Frontend (OBS-06). | No aplica. | Frontend: "sin cambios salvo un valor". No entrega código porque faltan la URL y el nombre de la propiedad. | T-16, T-19, T-20, T-21, T-30, T-31, T-32, T-33, T-38, M-2 y M-3. | SEC-08 (URL sin credenciales), SEC-09 (`/health` y OpenAPI), SEC-04. | **Cubierto en diseño.** El valor depende de un dato humano (OBS-06). |
| **Transversal:** sin cambios en API, persistencia ni pruebas existentes | `api/app`, `api/tests` y `requirements*.txt` sin cambios. `api/h01_checks/` es el único directorio nuevo (B-1, opción a). | T-25 (sin `.sql` ni migraciones nuevas). | Consistente entre los cuatro entregables. | T-22, T-23, T-24, T-25, T-26, T-34, T-35, T-36 y la comprobación `--collect-only` de B-1. | SEC-06 (`H01_BASE_REF` validada). | **Cubierto.** Ver OBS-02. |

**Resultado de cobertura:** ningún criterio queda sin diseño ni prueba asociada.

---

## 3. Verificación de contratos entre entregables

**Compatibles (revisados por lectura):**
- **`GET /health`:** Arquitecto, Backend, Frontend, Pruebas y Seguridad coinciden en `200`, sin autenticación y cuerpo no especificado y no verificado. Nadie inventa endpoint ni cuerpo.
- **Valores de `.env`:** coinciden en Arquitecto, Backend (comando `grep`) y Pruebas (`EXPECTED_ENV`).
- **Regla de URL:** Frontend exige `http`/`https` sin credenciales ni query. Pruebas la implementa en `validate_mock_url` y la prueba T-38.
- **Estructura de archivos:** Arquitecto, Backend y Pruebas coinciden en `api/h01_checks/` (`h01_support.py` y tres `check_h01_*.py`). `api/tests/` queda intacto.
- **Persistencia:** nadie emite SQL. La decisión de "eventos en memoria" es coherente entre Arquitecto, Backend y Seguridad.
- **Lógica de las pruebas:** leí `h01_support.py` y los tres archivos `check_*`, sin ejecutarlos, y comparé aserciones con implementación. Los casos centrales son coherentes:
  - comillas, espacios finales y `True` se rechazan;
  - CRLF y comentarios se toleran;
  - los mensajes no incluyen el valor leído (SEC-07);
  - `H01_BASE_REF` empezada por `-` se rechaza (SEC-06);
  - la plantilla con `<RELLENAR>` se rechaza;
  - los temas "mencionado pero abierto" se reportan como no cerrados.
- **Fases:** la separación entre fase 1 (línea base) y fase 2 (cambio) está bien definida. Las pruebas de fase 2 no cuentan como regresión si fallan en la línea base.

**Inconsistencias detectadas (ninguna es bloqueante, ver OBS-02, OBS-03 y OBS-05):**
1. **Existencia de `api/app`.** Arquitecto y Backend la describen como existente ("`config.py` y `requirements.txt` ya existen"). Pruebas dice que "no existe en la base" y que T-26 exige que siga sin existir.
2. **Estado de 1.3.** El Arquitecto afirma en la sección 4 que las seis decisiones están cerradas. Sus propias secciones 5 y "Preguntas pendientes" y la tabla del Backend ("Propuesto, no cerrado", "a confirmar") todavía las tratan como propuestas pendientes. Frontend y Seguridad las dan por aprobadas.
3. **Orden de la línea base.** Backend (sección 8) la mide después de crear `.env`. Pruebas (sección 2) la mide "antes de aplicar el cambio".

---

## 4. Observaciones

Severidad: **Alta** si afecta la validez de la evidencia o del veredicto, **Media** si afecta calidad o seguridad, **Baja** si es una mejora.

### OBS-01 (Alta): ejecuciones declaradas por agentes sin evidencia verificable
- **Dónde:**
  - Pruebas, sección 10: "35 pruebas, todas pasan"; "8 pasan"; "Python 3.13".
  - Seguridad, sección 6: V-02 a V-04 "EJECUTADO", con salidas copiadas.
- **Problema:** en este flujo los agentes no ejecutan código, así que esas afirmaciones no pueden tomarse como evidencia. No las uso para justificar el veredicto.
- **Responsable:** Ingeniero de pruebas y Revisor de seguridad (corrigen el rótulo). Una persona ejecuta.
- **Cambio requerido:** reetiquetar esos resultados como "reportados, no verificados". Sustituirlos por la salida real que adjunte la persona.
- **Verificación:**
  ```bash
  cd api && python -m pytest -rA -p no:cacheprovider h01_checks/check_h01_support_logic.py h01_checks/check_h01_guardrails.py
  cd .. && git check-ignore -v .env; git ls-files --error-unmatch .env; git log --all --oneline -- .env
  ```
  Esperado (NO EJECUTADO): 0 `failed`, 0 `error`, 0 `skipped`. `.env` ignorado, no versionado y sin historial.

### OBS-02 (Media): contradicción sobre la existencia de `api/app`
- **Responsable:** Arquitecto, con Pruebas.
- **Por qué no bloquea:**
  - Ningún criterio 1.1 a 1.4 depende de `api/app`.
  - T-26 contempla ambos casos: si existe en la base, importa `app.main:app`; si no, exige que siga sin existir.
  - Se resuelve con un comando.
- **Cambio requerido:** confirmar el estado real y alinear los textos. Si `api/app` no existe, quitar de las verificaciones `uvicorn app.main:app` y el supuesto de que `config.py` ya existe. Confirmar también que `tools/lab.py` y `api/tests/` existen.
- **Verificación:**
  ```bash
  git ls-tree -r --name-only HEAD -- api/app api/tests api/requirements.txt tools/lab.py
  ```
  Esperado (NO EJECUTADO): lista coherente con lo que cada documento afirma.

### OBS-03 (Media): estado de la tarea 1.3 documentado de forma contradictoria
- **Responsable:** Arquitecto y Backend (actualizan sus documentos).
- **Cambio requerido:**
  - Dejar `spec.md` como fuente única del estado.
  - Quitar de las listas "pendientes" lo ya resuelto: responsable de aprobar, definición de "usuario activo" y fuente del gasto.
  - Mantener como pendiente real solo el origen CORS (OBS-07).
- **Verificación:**
  ```bash
  cd api && python -m pytest -rA -p no:cacheprovider h01_checks/check_h01_change_state.py -k "spec_real or tasks_1_1"
  ```
  La salida debe indicar 6 temas con responsable y fecha y sin marcadores.
- **Si falla** (la spec real tiene marcadores abiertos o faltan temas): pasa a **bloqueante** (criterio 1.3 sin cerrar). Se re-emite el veredicto.

### OBS-04 (Alta, aprobación humana): la aprobación de 1.3 se registró "por delegación expresa" (OBS-01 del Arquitecto)
- **Responsable:** Miguel Ochoa Gallegos (persona), con el Arquitecto.
- **Problema:** no puedo verificar la delegación ni su soporte. Este informe no la valida ni sustituye la aprobación.
- **Cambio requerido:** que Miguel Ochoa Gallegos confirme por escrito las seis decisiones (comentario del PR, mensaje enlazado o firma en la spec) y que ese soporte quede enlazado en el PR.
- **Verificación:** enlace al comentario o confirmación en la descripción del PR. Revisar `git log -p -- openspec/changes/registro-activacion-wallet/specs/wallet-onboarding/spec.md` para ver quién y cuándo escribió "Responsable" y "Fecha".

### OBS-05 (Media): orden de la línea base respecto de `.env`
- **Problema:** `verify.py` puede leer `.env` (desconocido). Medir la línea base antes o después de 1.1 puede dar resultados distintos.
- **Responsable:** Backend (plantilla) y Pruebas (comando).
- **Cambio requerido:** añadir a `baseline.md` los campos "SHA base (`H01_BASE_REF`)", "¿`.env` presente al medir? (sí/no)" y "versión de Python". Fijar el orden: primero la línea base con el SHA anotado, luego se aplica el cambio.
- **Verificación:**
  ```bash
  export H01_BASE_REF="$(git rev-parse HEAD)"; echo "$H01_BASE_REF"
  python tools/verify.py; echo "codigo_salida=$?"
  ```
  T-27 debe seguir pasando con los campos nuevos.

### OBS-06 (Media): `environment.ts` pendiente por falta de dato
- **Problema:** URL del mock y nombre de la propiedad existente son desconocidos. El cambio no puede escribirse hasta que `GET /health` devuelva `200`. Por eso lo trato como condición previa al merge y no como entregable ausente.
- **Responsable:** Desarrollador frontend, con la persona que levanta el mock.
- **Cambio requerido:**
  - Cambiar solo el valor de la propiedad existente, con `http://localhost:<puerto>` o `https://<host-del-grupo>`.
  - La URL no lleva credenciales, query ni sufijo `/health`.
  - Debe coincidir como literal con `MOCK_W1_URL`. Si `environment.ts` compone la URL con otras partes, T-30 no la reconocerá. En ese caso, ajustar la prueba o documentar la excepción.
- **Verificación:**
  ```bash
  curl -i "$MOCK_W1_URL/health"
  grep -nE "https?://" src/environments/environment.ts
  grep -nE "https?://[^'\"\` ]*@" src/environments/environment.ts
  cd api && python -m pytest -rA -p no:cacheprovider h01_checks/check_h01_change_state.py -k "mock_w1 or url_del_mock or diff_frontend"
  ```
  Esperado (NO EJECUTADO): `HTTP 200`. La URL en `environment.ts` coincide con la usada. El segundo `grep` no devuelve nada. T-21, T-30 y T-33 pasan.

### OBS-07 (Media): CORS decidido sobre un origen supuesto y sin verificar contra el mock
- **Problema:** `http://localhost:4200` es un **[Supuesto]**. No hay aserción automática. SEC-04 sigue abierta.
- **Responsable:** Desarrollador frontend (confirma el origen real) y responsable del mock W1 (configuración).
- **Cambio requerido:** confirmar el origen y dejar el resultado en la spec. No usar `*`, no reflejar `Origin` y no habilitar credenciales sin justificación.
- **Verificación:**
  ```bash
  grep -n '"port"' angular.json; grep -n '"start"' package.json
  curl -si -H "Origin: https://evil.example" "$MOCK_W1_URL/health" | grep -i '^access-control-'
  curl -si -H "Origin: http://localhost:4200" "$MOCK_W1_URL/health" | grep -i '^access-control-'
  curl -si -X OPTIONS "$MOCK_W1_URL/health" -H "Origin: http://localhost:4200" -H "Access-Control-Request-Method: DELETE" | grep -i '^access-control-'
  ```
  Esperado (NO EJECUTADO):
  1. Sin `Access-Control-Allow-Origin` para el origen ajeno.
  2. Exactamente `http://localhost:4200` para el origen propio.
  3. `DELETE` no figura entre los métodos permitidos.

### OBS-08 (Media): semántica de `CREWAI_INCLUDE_DATA=true` desconocida (SEC-01)
- **Problema:** el valor lo exige el Issue y no se discute. Falta saber qué datos incluye y adónde van.
- **Responsable:** Arquitecto y Revisor de seguridad.
- **Cambio requerido:** documentar en la spec o en `baseline.md` qué datos incluye la variable. Mientras tanto, usar solo datos sintéticos en el mock, los fixtures y la salida de `verify.py`.
- **Verificación:**
  ```bash
  grep -rn "CREWAI_INCLUDE_DATA" --exclude-dir=.git --exclude-dir=node_modules .
  ```
  Esperado: se localiza el punto de lectura y queda anotada la lista de datos incluidos.

### OBS-09 (Media): `baseline.md` puede filtrar salida sensible (SEC-03)
- **Responsable:** persona que ejecuta `verify.py`, con revisión de Seguridad.
- **Cambio requerido:** registrar un resumen (conteos y nombres de pruebas fallidas), no la salida completa. Revisarlo antes del commit.
- **Verificación:**
  ```bash
  grep -nEi '(token|secret|password|passwd|authorization|bearer|api[_-]?key|ghp_|github_pat_|-----BEGIN)' openspec/changes/registro-activacion-wallet/baseline.md
  ```
  Esperado (NO EJECUTADO): sin coincidencias (código de salida 1). Más revisión humana, porque el patrón no detecta datos personales.

### OBS-10 (Media): `.env` no debe viajar en el PR
- **Problema:** el Backend lo entrega como "archivo". Si el flujo de publicación lo recoge, quedaría versionado.
- **Responsable:** Backend y Arquitecto.
- **Cambio requerido:** excluir `.env` de lo que publica `crew/publish_pr.py`. Si no es posible, dejarlo fuera del PR manualmente.
- **Verificación:**
  ```bash
  git status --short
  git diff --name-only <SHA_BASE>..HEAD | grep -x '.env'
  ```
  Esperado (NO EJECUTADO): `.env` no aparece en `git status`. El segundo comando no devuelve nada.

### OBS-11 (Baja): supuestos de infraestructura de las pruebas sin comprobar
- **Problema:** S9 asume que `httpx` está instalado. El Issue no actualiza `requirements*.txt`. Los `check_*` dependen además de `tools/lab.py` y de que `pytest` no use `--import-mode=importlib`, porque se importa `h01_support` sin `__init__.py`.
- **Responsable:** Ingeniero de pruebas.
- **Verificación:**
  ```bash
  cd api && python -c "import httpx, fastapi, pytest; print(httpx.__version__)"
  grep -rn "import-mode\|python_files\|testpaths" pytest.ini pyproject.toml setup.cfg tox.ini 2>/dev/null
  python -m pytest --collect-only -q -p no:cacheprovider tests/ | grep -ci "h01"
  python -m pytest --collect-only -q -p no:cacheprovider | grep -ci "h01"
  ```
  Esperado (NO EJECUTADO): imports sin error. Cada conteo de `h01` es `0`.
- **Si falta `httpx`:** no se añade a `requirements*.txt` en H01. Se instala en el entorno local y se escala al Arquitecto.

### OBS-12 (Baja): retirada posterior de `api/h01_checks/`
- **Responsable:** Arquitecto.
- **Cambio requerido:** registrar el compromiso de retirar `check_h01_change_state.py` y las guardas con `git diff` en un PR posterior. Pierden sentido tras el merge. No tocar `api/tests/`.
- **Verificación:** existencia de una tarea o issue de seguimiento.

### Hallazgos de seguridad abiertos o informativos (sin acción de código en H01)
- **SEC-05, identidad y autorización:** son requisitos para las historias que implementen recursos por usuario. No hay endpoints por usuario en H01. Debe llevar sus pruebas A/B a `api/tests/` cuando exista el recurso.
- **SEC-09, `/health` mínimo y `/openapi.json` fuera de desarrollo:** requiere decisión del Arquitecto en una historia posterior. Si se deshabilita OpenAPI, T-26 debe ajustarse (rama con `api/app`).
- **SEC-06, SEC-07 y SEC-08:** reportados como aplicados en las pruebas. Pendiente de confirmar con la ejecución de T-35 a T-38.

---

## 5. Pruebas pendientes de ejecución (todas NO EJECUTADO)

| ID | Qué | Responsable | Comando exacto (desde la raíz de `wallet-app-g6`) | Esperado (predicción) |
|---|---|---|---|---|
| P-01 | Fijar la base | Persona que ejecuta | `export H01_BASE_REF="$(git rev-parse HEAD)"` | SHA impreso. Anotarlo en `baseline.md` (OBS-05). |
| P-02 | Suite existente (T-01) | Persona que ejecuta | `python tools/lab.py test api` | Desconocido. Se registra tal cual. |
| P-03 | Suite directa (detalle) | Ingeniero de pruebas | `cd api && python -m pytest -rA -p no:cacheprovider tests/ && cd ..` | Desconocido. `skipped` = 0. |
| P-04 | Pruebas de lógica y guardas, fase 1 | Ingeniero de pruebas | `cd api && python -m pytest -rA -p no:cacheprovider h01_checks/check_h01_support_logic.py h01_checks/check_h01_guardrails.py && cd ..` | 0 `failed`, 0 `error`, 0 `skipped`. |
| P-05 | Línea base `verify.py` (1.2, M-1) | Persona que ejecuta | `python tools/verify.py; echo "codigo_salida=$?"` | Desconocido. Resumen redactado a `baseline.md`. |
| P-06 | `.env` (1.1, V-12) | Persona que ejecuta | `grep -cE '^(GITHUB_OWNER=user-bcp-student04\|PR_REPO=wallet-app-g6\|CREWAI_INCLUDE_DATA=true)$' .env` | `3`. |
| P-07 | `.env` no versionado (SEC-02) | Persona que ejecuta | `git check-ignore -v .env; git ls-files --error-unmatch .env; git log --all --oneline -- .env` | Regla impresa. Error. Sin salida. |
| P-08 | Mock responde (1.4) | Persona que levanta el mock | `export MOCK_W1_URL="<URL>"; curl -i "$MOCK_W1_URL/health"` | `HTTP 200`. |
| P-09 | Caso de error del mock | Persona que ejecuta | `curl -i http://localhost:59999/health; echo "codigo_salida=$?"` | Sin respuesta HTTP. Código distinto de 0 (típico 7). |
| P-10 | CORS y `/health` (SEC-04, SEC-09) | Persona que ejecuta, con Seguridad | Los tres `curl` de OBS-07 y `curl -si "$MOCK_W1_URL/health"` | Ver OBS-07. Cuerpo mínimo en `/health`. |
| P-11 | Fijar URL y compilar | Desarrollador frontend | `npm run build` (o `ng build`) | Desconocido. Debe compilar. |
| P-12 | Fase 2: estado del cambio | Ingeniero de pruebas | `cd api && python -m pytest -rA -p no:cacheprovider h01_checks/check_h01_change_state.py && cd ..` | T-17, T-18, T-21, T-27 a T-30 y T-33 pasan. |
| P-13 | Regresión | Ingeniero de pruebas | `python tools/lab.py test api` | Igual que en P-02. |
| P-14 | Alcance | Persona que ejecuta | `git status --short && git diff --stat` | Solo documentación de la historia, `environment.ts` y `api/h01_checks/`. Nada en `api/app/` ni en `api/tests/`. `.env` no aparece. |
| P-15 | Sanitización de `baseline.md` | Seguridad | `grep` de OBS-09 | Sin coincidencias. |
| P-16 | Prueba de `base_ref` (SEC-06) | Seguridad | `cd api && H01_BASE_REF='--output=/tmp/h01_pwned' python -m pytest -q h01_checks/check_h01_guardrails.py; ls /tmp/h01_pwned` | Falla con `ValueError`. `/tmp/h01_pwned` no existe. |

**Criterio de aceptación de la ejecución:**
- 0 `failed`, 0 `error` y 0 `skipped` en `api/h01_checks/` en fase 2.
- La suite existente da el mismo resultado que en la línea base.
- No se afirma cobertura porcentual. Para medirla haría falta `pytest --cov` con su salida real.

---

## 6. Evidencia utilizada

| Evidencia | Origen | Estado |
|---|---|---|
| Texto del Issue (1.1 a 1.4) | Entrada del laboratorio | Leída. |
| Plan, componentes, contrato `GET /health`, trazabilidad y límites de alcance | Arquitecto | Leída. Contiene inconsistencias de estado (sección 3). |
| `.env` de tres líneas, plantilla `baseline.md`, verificaciones, "sin SQL" y "sin cambios en `api/app`" | Backend | Leída. Código nuevo en el API: ninguno. |
| "Sin cambios en el frontend salvo un valor" y regla de URL (SEC-08) | Frontend | Leída. |
| Trazabilidad T-01 a T-39, fases, comandos y código de `h01_support.py` y de tres archivos `check_*` | Pruebas | Leída y revisada por lectura. **No ejecutada**; su sección 10 es no verificable (OBS-01). |
| SEC-01 a SEC-09, V-01 a V-16 | Seguridad | Leída. Los V-02 a V-04 son no verificables (OBS-01). |
| Contenido de `spec.md`, `verify.py`, `environment.ts`, mock W1 y `api/app` | Repositorio | **No recibido.** Ninguna conclusión sobre su contenido. |

---

## 7. Veredicto

### Motivos

1. **Cobertura completa de diseño.** Cada criterio (1.1 a 1.4) y el alcance transversal tienen componente, implementación o decisión documental, y una o más pruebas asociadas con comando reproducible.
2. **Contratos compatibles.** El único contrato (`GET /health`: `200`, sin autenticación, cuerpo no especificado) y los valores de `.env` coinciden entre los entregables. No hay endpoints, SQL ni esquemas nuevos que puedan chocar.
3. **Stack coherente.** Ningún entregable mezcla Java/Maven/Quarkus con Python, ni implementa otro stack (sección 1). Es un supuesto confirmado, sin rechazo.
4. **Alcance respetado.** No se tocan `api/app`, `api/tests`, `requirements*.txt` ni `tools/verify.py`.
   - El único añadido es `api/h01_checks/`, decidido por el Arquitecto (B-1, opción a). Se retira después del merge (OBS-12).
   - Las guardas T-22 a T-26 y T-34 lo verifican.
5. **Sin marcadores sin resolver en decisiones necesarias.**
   - `<RELLENAR>` en `baseline.md` y `<URL_MOCK_W1>` son datos que producirá la ejecución humana, no decisiones de diseño. Las pruebas T-11, T-27 y T-31 los rechazan hasta que se rellenen.
   - Las inconsistencias de las secciones 3 y 4 (OBS-02, OBS-03, OBS-05) son documentales o de orden de ejecución, y tienen verificación concreta.
   - Si OBS-03 o P-12 muestran que la spec real tiene preguntas abiertas, el veredicto pasa a RECHAZADO (criterio 1.3 sin cerrar).

### Bloqueantes de diseño

**Ninguno.**

### Condiciones previas al merge (no son motivo de rechazo por sí solas)

| # | Condición | Responsable |
|---|---|---|
| C-1 | Ejecutar P-01 a P-16 y adjuntar la salida real (sin secretos) a `baseline.md` o al PR. | Persona que ejecuta, Ingeniero de pruebas y Seguridad. |
| C-2 | Rellenar `baseline.md` con SHA, estado de `.env`, fecha, código de salida y resumen redactado (OBS-05, OBS-09). | Persona que ejecuta. |
| C-3 | Fijar la URL real del mock en `environment.ts` tras `HTTP 200`, sin credenciales y coincidente con `MOCK_W1_URL` (OBS-06). | Desarrollador frontend. |
| C-4 | Confirmar el origen CORS real y verificarlo contra el mock (OBS-07). | Desarrollador frontend y responsable del mock. |
| C-5 | Aprobación humana explícita de las seis decisiones de 1.3 por Miguel Ochoa Gallegos, con soporte enlazado (OBS-04). | Miguel Ochoa Gallegos. |
| C-6 | Reetiquetar como no verificadas las ejecuciones declaradas por agentes (OBS-01). | Ingeniero de pruebas y Seguridad. |
| C-7 | Alinear los documentos sobre `api/app` y el estado de 1.3, y retirar de las listas "pendientes" lo ya resuelto (OBS-02, OBS-03). | Arquitecto y Backend. |
| C-8 | Documentar la semántica de `CREWAI_INCLUDE_DATA` (OBS-08) y dejar `.env` fuera del PR (OBS-10). | Arquitecto, Seguridad y Backend. |
| C-9 | Comprobar `httpx`, la configuración de `pytest` y la colección de `h01_checks` (OBS-11). | Ingeniero de pruebas. |
| C-10 | Marcar `[x]` las tareas 1.1 a 1.4 solo cuando existan las evidencias anteriores (T-29). | Persona responsable de la tarea. |
| C-11 | Aprobación final del merge por la persona designada. | Persona designada por el equipo. |

### Correcciones solicitadas

Son las de las observaciones OBS-01 a OBS-12. Ninguna exige rediseñar ni cambiar el alcance del Issue.

**La aprobación final depende de la evidencia ejecutada y de las aprobaciones humanas.** Este veredicto no sustituye a ninguna de ellas.

VEREDICTO: APROBADO — sin bloqueantes de diseño; el merge queda condicionado a las condiciones C-1 a C-11, a la evidencia real de ejecución y a las aprobaciones humanas.