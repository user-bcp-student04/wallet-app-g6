# chapter_review.md

**Feature:** [H01] Preparación del entorno y línea base
**Revisor:** Chapter (revisor transversal del Issue)
**Fecha:** 2026-11-06
**Entregables revisados:** Arquitecto (`user_story.md`), Backend (`backend_spec.md`), Frontend (`frontend_spec.md`), Pruebas (`testing_report.md` y código de pruebas), Seguridad (`security_report.md`).

> **Estado de la evidencia: NO EJECUTADO.** Los agentes no ejecutan código. Ningún resultado de este informe es observado: todo es lectura estática del material. Este informe **no sustituye ninguna aprobación humana**.
> **Material:** llegó completo, sin truncamiento visible. No faltan secciones de ningún entregable.

---

## 1. Supuesto de stack (confirmado, no es motivo de rechazo)

- El API es Python + FastAPI en `api/`, decisión del equipo ya confirmada por una persona.
- Arquitecto, Backend, Pruebas y Seguridad trabajan sobre ese stack (`api/app/`, `pytest`, `TestClient`, `Depends`, `httpx`).
- Las referencias Java/Maven/Quarkus no aparecen en las tareas 1.1 a 1.4. El Backend las descarta de forma explícita (supuesto 6).
- Ningún entregable mezcla stacks ni implementa otro distinto.
- **Resultado:** sin contradicción de stack. Se registra solo como supuesto confirmado.

---

## 2. Cobertura por criterio de aceptación

El Issue no enumera criterios separados, así que cada tarea 1.1 a 1.4 se toma como criterio.

Persistencia es N/A en los cuatro criterios: H01 no emite SQL ni migración (Backend §7; guarda T-25).

| Criterio | Arquitectura | Implementación | Pruebas | Seguridad | Estado de cobertura |
|---|---|---|---|---|---|
| **1.1** `.env` con 3 variables exactas | Límite definido (solo 3 variables, no versionado como supuesto) | `.env` entregado con las 3 líneas exactas, sin secretos | T-02 a T-09 (lógica), T-17 y T-18 (repo real), `grep -cE` esperado `3` | SEC-02 (`.gitignore` no confirmado), SEC-07 | **Cubierto en diseño.** Ejecución pendiente. |
| **1.2** Línea base ejecutada y registrada | `baseline.md` (ruta supuesta), `verify.py` no se modifica | Comando y plantilla con `<RELLENAR>` (son datos de ejecución, no de diseño) | T-10 a T-12 y T-27. M-1 manual. | SEC-03 (salida sensible en un archivo versionado) | **Cubierto en diseño.** Depende de ejecución humana. |
| **1.3** Seis preguntas cerradas | Tabla de 6 decisiones **propuestas** | No se entrega texto de spec (no estaba en el contexto). Las decisiones son propuestas. | T-13, T-14, T-15, T-28, T-29 | SEC-01, SEC-04, SEC-05 y §5 del informe de seguridad | **Cubierto parcialmente.** Hay propuesta y prueba, pero `usuario activo` y `fuente de gasto` quedan con detalle "pendiente" y la aprobación es humana (OBS-01). |
| **1.4** Mock responde y URL fijada | `GET /health` y `environment.ts`; solo cambia el valor de la URL | `curl` entregado. `environment.ts` no se entrega porque la URL y la propiedad son desconocidas. | T-16, T-19 a T-21, T-30 a T-33, M-2, M-3 | SEC-04, SEC-08, SEC-09 | **Cubierto en diseño.** Ejecución e input (URL real) pendientes. |

**Criterios sin diseño ni prueba asociada: ninguno.**

---

## 3. Contratos, supuestos e incompatibilidades entre entregables

| # | Punto | Entregables | Resultado |
|---|---|---|---|
| C-1 | Stack Python/FastAPI | Todos | Coherente. |
| C-2 | Contrato `GET /health`: `200`, sin autenticación, cuerpo no especificado | Arquitecto, Backend, Frontend, Pruebas, Seguridad | Coherente. Nadie inventa cuerpo. |
| C-3 | Ruta de `baseline.md` y de `environment.ts` | Todos | Coherente (supuestos declarados y no confirmados, OBS-12). |
| C-4 | **Pruebas nuevas en `api/tests/`** | Arquitecto: supuesto 7 ("No se añaden pruebas en `api/tests/`") y alcance ("pruebas nuevas" fuera). Backend: `api/tests/` "SIN CAMBIOS" y V-15 "Nada en `api/tests/`". Pruebas: añade 4 archivos nuevos en `api/tests/` (S13, §7). | **INCOMPATIBLE (bloqueante B-1).** |
| C-5 | Derivación de directorio por propietario: Arquitecto §3.2 dice "SHA-256 del identificador"; Seguridad SEC-05 dice que SHA-256 sin sal es reversible por diccionario y exige sal o clave del servidor | Arquitecto vs Seguridad | Contradicción de convención futura. No se implementa en H01 (los eventos van en memoria). Se registra como OBS-04, no como bloqueante. |
| C-6 | Tabla de trazabilidad de Pruebas: asigna T-02 a T-18 a `test_h01_support_logic.py` ("todas pasan en línea base"), pero T-17 y T-18 están en `test_h01_change_state.py` y fallarán legítimamente si `.env` aún no existe. Además §1 cita T-23 para el diff de `api/app`, cuando ese diff es T-22. | Pruebas (interno) | Inconsistencia documental (OBS-03). |
| C-7 | Responsable de `environment.ts`: Arquitecto y Backend dicen "rol Frontend"; Frontend dice "la persona responsable". | Arquitecto, Backend, Frontend | Ambigüedad de responsable (OBS-06). |

---

## 4. Bloqueantes de diseño

### B-1: El alcance sobre `api/tests/` se contradice entre entregables, y las pruebas añadidas se acoplan a la suite permanente de la API

**Evidencia:**
- El Arquitecto excluye pruebas nuevas y fija como supuesto 7: "No se añaden pruebas en `api/tests/` en H01, porque no cambia código del API".
- El Backend declara `api/tests/` "SIN CAMBIOS (no se tocan)" y su verificación 7 (`git status`/`git diff`) espera "Nada en `api/app/` ni en `api/tests/`".
- El Ingeniero de pruebas entrega `h01_support.py`, `test_h01_support_logic.py`, `test_h01_guardrails.py` y `test_h01_change_state.py` dentro de `api/tests/`. Su limpieza espera "solo los archivos del cambio y las 4 pruebas nuevas".
- Seguridad revisa y propone correcciones sobre esos archivos (SEC-06, SEC-07, SEC-08). Con ello se da por bueno un alcance que Arquitectura excluyó.
- Esto es un cambio fuera del alcance acordado, y los criterios de verificación del Backend y del Arquitecto fallarían contra el propio entregable de Pruebas.

**Efecto de diseño (no es una cuestión de ejecución):**
- Los archivos de `api/tests/` se recogen con `python tools/lab.py test api` y `pytest tests/`.
- `test_h01_change_state.py` exige `.env`, que está en `.gitignore` y por tanto **no existe en un clon limpio ni en CI** (T-17, T-18, T-27).
- También exige `MOCK_W1_URL` (T-21, T-30). Si falta, **falla**, porque el informe prohíbe `skip`.
- Depende de `git diff` contra un `H01_BASE_REF` (T-22 a T-25, T-33), que pierde sentido tras el merge.
- Resultado: la suite permanente de la API quedaría roja o dependiente del entorno de cada persona.
- El informe de Pruebas admite que `tools/verify.py` podría invocar pytest (S12). En ese caso la línea base de 1.2 incluiría estas pruebas y dejaría de ser una línea base "antes del cambio".
- La fila de baseline "T-02 a T-18 pasan" tampoco es coherente (C-6).

**Responsables:** Arquitecto (decide el alcance), Ingeniero de pruebas (reubica o ajusta las pruebas), Backend (alinea sus verificaciones).

**Cambio requerido (elegir una opción y reflejarla en los tres entregables):**
- **Opción a (preferida):**
  - Sacar las comprobaciones del estado del cambio (`test_h01_change_state.py` y las guardas de git) de la colección por defecto de `api/tests/`.
  - Ubicarlas, por ejemplo, en `tools/h01_checks/` o bajo un marcador `h01` excluido por defecto.
  - Dejar `python tools/lab.py test api` y `tools/verify.py` sin esas pruebas.
  - Mantener en `api/tests/` solo lo que no dependa de `.env`, del mock ni de git, si el equipo lo quiere.
- **Opción b:**
  - El Arquitecto amplía por escrito el alcance (actualiza el supuesto 7 y la sección de fuera de alcance).
  - Esa ampliación resuelve el comportamiento de las pruebas en un clon limpio y en CI.
  - Backend actualiza la verificación 7 y Pruebas actualiza su limpieza.
- En ambas opciones:
  - Corregir la numeración y la fila de línea base (C-6).
  - Definir que la línea base de 1.2 se mida antes de añadir las pruebas, o con ellas excluidas.

**Verificación (NO EJECUTADO):**
```bash
git status --short && git diff --stat
# esperado: coincide exactamente con el alcance declarado por el Arquitecto tras la corrección

cd api && python -m pytest --collect-only -q tests/ | grep -ci "h01"
# opción a: esperado 0 en la colección por defecto de la suite de la API

# en un clon limpio sin .env ni MOCK_W1_URL:
cd api && python -m pytest -rA -p no:cacheprovider tests/
# esperado: mismo resultado que la suite existente en la línea base; 0 fallos atribuibles a H01
```

---

## 5. Observaciones no bloqueantes

| ID | Sev. | Observación | Responsable | Cambio requerido | Verificación (NO EJECUTADO) |
|---|---|---|---|---|---|
| OBS-01 | Alta | Decisiones de 1.3 incompletas. `usuario activo`: definición exacta "pendiente". `fuente de gasto de adquisición`: origen "pendiente". CORS usa un origen supuesto (`http://localhost:4200`). La spec no se vio, así que las decisiones no están verificadas contra ella. Aquí no se marca como bloqueante porque cerrarlas es una decisión humana que el rol de diseño no puede tomar sin la spec. | Arquitecto (redacta); persona aprobadora por designar (aprueba, con fecha). | Escribir en `spec.md` una decisión por cada una de las seis preguntas, con responsable y fecha, y definir `usuario activo` y la fuente del gasto sin marcadores abiertos. | `grep -nEi '\[PENDIENTE\]\|\[ABIERTA\]\|NEEDS CLARIFICATION\|\bTBD\b\|\bTODO\b\|PREGUNTA ABIERTA' openspec/changes/registro-activacion-wallet/specs/wallet-onboarding/spec.md` sin coincidencias. Revisión humana de las 6 decisiones. |
| OBS-02 | Media | T-28 comprueba que cada tema aparezca (`KYC`, `CORS`...) y que no haya ciertos marcadores (S5, no confirmado). Una pregunta aún abierta, redactada de otra forma, pasaría. | Ingeniero de pruebas | Exigir una decisión explícita con responsable y fecha por tema, o ajustar `PENDING_MARKERS` tras ver la spec real. | Spec sintética con el tema mencionado pero abierto: la prueba debe fallar. |
| OBS-03 | Baja | IDs y filas inconsistentes en la trazabilidad (C-6). | Ingeniero de pruebas | Reasignar T-17 y T-18 a "Fase 2" y corregir la referencia T-22/T-23. | Revisión de `testing_report.md`: cada ID aparece una vez, con archivo y fase correctos. |
| OBS-04 | Media | SHA-256 sin sal (Arquitecto §3.2) frente a sal o clave del servidor (SEC-05). | Arquitecto (con Seguridad) | Actualizar la convención a HMAC-SHA-256 con clave del servidor, o justificar por escrito que el identificador no es adivinable. | Revisión documental. Cuando se implemente: prueba de que la ruta no contiene el identificador crudo. |
| OBS-05 | Media | `.gitignore` y `.env.example` (SEC-02) no están en el alcance declarado, y la verificación 7 del Backend no los lista. Si `.env` no está ignorado, T-18 falla. | Arquitecto (decide si entra en el alcance); Backend (lo entrega). | Aprobar la inclusión mínima de `.gitignore` y `.env.example` con las 3 claves no secretas, o confirmar que `.env` ya está ignorado. | `git check-ignore -v .env`; `git ls-files --error-unmatch .env` (error esperado); `git log --all --oneline -- .env` (sin salida). |
| OBS-06 | Media | Dueño de `environment.ts` ambiguo (C-7). | Arquitecto (asigna); Desarrollador frontend (ejecuta). | Asignar al rol Frontend el cambio de un solo valor, con el nombre de propiedad existente, tras el `200` del mock. | `grep -nF "<URL_MOCK_W1>" src/environments/environment.ts`; `git diff --stat -- src/` (solo `environment.ts`). |
| OBS-07 | Media | Las correcciones de SEC-06 (validar `H01_BASE_REF`), SEC-07 (no imprimir valores de `.env`) y SEC-08 (validar la URL) están propuestas pero **no aplicadas** al código de pruebas. Ya revisé que siguen siendo compatibles con T-04, T-05, T-08 y T-31 por lectura, sin ejecutar. Si se aplica B-1 con la opción a, estas correcciones se aplican al código reubicado. | Ingeniero de pruebas | Incorporar las tres correcciones. | Comandos de V-08, V-09 y V-10 del informe de seguridad. |
| OBS-08 | Media | SEC-01: se desconoce qué datos incluye `CREWAI_INCLUDE_DATA=true` y adónde van. | Persona responsable del flujo (por designar); Seguridad. | Documentar en la spec qué datos incluye. Mientras tanto, solo datos sintéticos en mock y fixtures. | `grep -rn "CREWAI_INCLUDE_DATA" --exclude-dir=.git --exclude-dir=node_modules .` |
| OBS-09 | Media | SEC-03: `baseline.md` se versiona y puede incluir salida sensible de `verify.py`. | Persona que ejecuta la línea base. | Registrar solo un resumen (conteos, nombres de pruebas fallidas) y revisarlo antes del commit. | `grep -nEi '(token\|secret\|password\|passwd\|authorization\|bearer\|api[_-]?key\|ghp_\|github_pat_\|-----BEGIN)' openspec/changes/registro-activacion-wallet/baseline.md` sin coincidencias, más revisión humana. |
| OBS-10 | Media | SEC-04: CORS sin decisión aprobada ni aserción automática. | Responsable del mock W1 (por designar); Arquitecto. | Confirmar el origen real y la lista blanca, sin `*`, sin reflejar `Origin`. | Los 3 `curl` de SEC-04 (origen ajeno, origen propio, `OPTIONS` con `DELETE`). |
| OBS-11 | Baja | SEC-05 (preventivo) y SEC-09. T-26 espera `200` en `/openapi.json`: si se deshabilita fuera de desarrollo, T-26 debe ajustarse. | Arquitecto, Ingeniero de pruebas | Registrar SEC-05 como requisito de las historias siguientes. Coordinar T-26 con la decisión sobre OpenAPI. | `curl -si "$MOCK_W1_URL/health"` con cuerpo mínimo. Procedimiento A/B de SEC-05 en la historia que lo implemente. |
| OBS-12 | Baja | Supuestos no confirmados: existencia de `tools/lab.py`, `app.main:app` importable desde `api/`, rutas de `environment.ts` y `baseline.md`. | Backend, Ingeniero de pruebas | Confirmarlos o ajustar las rutas. | `ls tools/lab.py src/environments/environment.ts`; `cd api && python -c "from app.main import app"` |

---

## 6. Pruebas pendientes y condiciones previas al merge

Estas condiciones **no son motivo de rechazo por sí solas**. Son condiciones previas al merge. El responsable de ejecutarlas es la persona que designe el equipo (no se asigna nombre). Hay que adjuntar la salida real de cada comando.

| # | Condición | Comando exacto | Resultado esperado (no observado) |
|---|---|---|---|
| P-1 | 1.1: contenido de `.env` | `grep -cE '^(GITHUB_OWNER=user-bcp-student04\|PR_REPO=wallet-app-g6\|CREWAI_INCLUDE_DATA=true)$' .env` | `3` |
| P-2 | `.env` no versionado | `git check-ignore -v .env && git ls-files --error-unmatch .env; git log --all --oneline -- .env` | Regla impresa; error del segundo comando; sin salida del tercero |
| P-3 | 1.2: línea base | `python tools/verify.py; echo "codigo_salida=$?"` | Desconocido. Se registra, redactado, en `baseline.md`. |
| P-4 | 1.4: mock responde | `curl -i "$MOCK_W1_URL/health"` | `HTTP 200` (supuesto) |
| P-5 | 1.4: caso de error | `curl -i http://localhost:59999/health; echo "codigo_salida=$?"` | Sin respuesta HTTP, código típico 7 |
| P-6 | 1.4: URL fijada | `grep -nF "$MOCK_W1_URL" src/environments/environment.ts` | Una coincidencia |
| P-7 | Alcance | `git status --short && git diff --stat` | Coincide con el alcance corregido tras B-1 |
| P-8 | Suite de la API (para detectar regresión) | `python tools/lab.py test api` y `cd api && python -m pytest -rA -p no:cacheprovider tests/` | Mismo resultado que en la línea base. 0 `skipped` en lo nuevo. |
| P-9 | Compilación del frontend | `npm run build` (o `ng build`) | Desconocido hasta ejecutarlo |
| P-10 | CORS | `curl -si -H "Origin: https://evil.example" "$MOCK_W1_URL/health" \| grep -i '^access-control-'` (y los otros dos de SEC-04) | Sin `Access-Control-Allow-Origin` para el origen ajeno; exacto para el propio; nunca `*` |
| P-11 | Redacción de `baseline.md` | grep de OBS-09 | Sin coincidencias |
| P-12 | Spec cerrada | grep de marcadores de OBS-01 | Sin coincidencias |

**Aprobaciones humanas que se conservan (este informe no las sustituye):**
- Aprobación de las seis decisiones de 1.3 (responsable y fecha en la spec).
- Aprobación del PR.
- Confirmación de la URL del mock y del origen CORS.
- Confirmación de la semántica de `CREWAI_INCLUDE_DATA`.
- Aceptación del resultado de la línea base (limpia, o con fallos preexistentes documentados).

---

## 7. Evidencia revisada

- **Arquitecto:** alcance, supuestos 1 a 7, trazabilidad por tarea y decisiones propuestas de 1.3. Fuente de C-4 (supuesto 7) y de C-5 (§3.2).
- **Backend:** `.env` con 3 líneas exactas, plantilla `baseline.md`, sin SQL, sin cambios en `api/app/`, verificaciones 1 a 7 (la 7 espera "Nada en `api/tests/`").
- **Frontend:** sin cambios; solo el valor en `environment.ts`, sin entregar código por URL y propiedad desconocidas.
- **Pruebas:** 4 archivos en `api/tests/`; trazabilidad T-01 a T-33; S1 a S13; la fila de línea base y la numeración (C-6).
- **Seguridad:** SEC-01 a SEC-09 como DETECTADO/PROPUESTO. Verificaciones ejecutadas: 0.
- **No disponible en el contexto:** `tools/verify.py`, `spec.md`, `tasks.md` real, `environment.ts`, el mock W1, `.gitignore`, `api/app/*`. Es una limitación declarada por todos los roles, no un entregable ausente: ninguna tarea exigía entregar esos archivos.

---

## 8. Veredicto

**Motivos.** Cada criterio 1.1 a 1.4 tiene diseño, implementación o comando de verificación y pruebas asociadas. No hay contradicción de stack ni marcadores de diseño sin resolver (`<RELLENAR>`, `<URL_MOCK_W1>` son datos de ejecución). Hay un bloqueante de diseño: los entregables se contradicen sobre el alcance de `api/tests/` (C-4), y las pruebas añadidas dejarían la suite permanente de la API dependiente de `.env`, del mock y de git.

**Bloqueantes de diseño:**
- **B-1:** conflicto de alcance entre Arquitecto/Backend (sin cambios en `api/tests/`) y Pruebas (4 archivos nuevos en `api/tests/`), con efecto sobre la suite de la API y sobre la línea base de 1.2.

**Correcciones requeridas para levantar el rechazo:**
1. Resolver B-1 con la opción a o la opción b, y alinear Arquitecto, Backend y Pruebas.
2. Corregir la numeración y la fila de línea base de Pruebas (OBS-03).
3. Aplicar las correcciones de SEC-06, SEC-07 y SEC-08 al código de pruebas (OBS-07).
4. Reconciliar SHA-256 frente a HMAC (OBS-04).
5. Decidir el alcance de `.gitignore` y `.env.example` (OBS-05) y asignar el dueño de `environment.ts` (OBS-06).
6. Documentar `usuario activo` y `fuente de gasto` en la spec (OBS-01).

**Condiciones previas al merge (no motivo de rechazo):** P-1 a P-12 con salida real adjunta, más las aprobaciones humanas de la sección 6. Una vez corregido B-1, la aprobación final depende de la evidencia ejecutada.

VEREDICTO: RECHAZADO