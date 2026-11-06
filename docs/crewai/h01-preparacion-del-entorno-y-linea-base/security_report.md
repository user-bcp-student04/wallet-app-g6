# security_report.md

**Feature:** [H01] Preparación del entorno y línea base
**Rol:** Revisor de seguridad de aplicaciones
**Fecha:** 2026-11-06
**Alcance:** revisión estática de los artefactos de los pasos anteriores (Arquitecto, Backend, Frontend, Pruebas).

> **Estado global: NO EJECUTADO, salvo V-02 a V-04 y la ejecución parcial de T-35 a T-38 (sección 6).** Todo lo marcado como "esperado" es una predicción, no una observación. La persona que ejecute las comprobaciones debe adjuntar la salida real y actualizar la sección 6.

---

## 1. Convención de estados

| Estado | Significado en este informe |
|---|---|
| **DETECTADO** | Riesgo identificado leyendo el contexto. Se cita la evidencia textual. No está explotado ni reproducido. |
| **PROPUESTO** | Corrección o decisión sugerida. No está aplicada. |
| **VERIFICADO** | Comprobación ejecutada con salida real adjunta. **Ninguna** en este informe. |
| **NO EVALUABLE** | Falta el artefacto necesario (código, spec o mock no incluidos en el contexto). No se emite conclusión. |

---

## 2. Resumen ejecutivo

H01 es una historia de preparación de entorno. No añade endpoints, persistencia ni lógica de negocio en `api/app/`, y el frontend solo recibe una URL en `environment.ts`. Por eso **no se detectó ninguna vulnerabilidad explotable confirmada** en código de la aplicación. Esto se debe a que ese código no forma parte del cambio ni del contexto, no a que se haya demostrado su ausencia.

Sí se detectaron riesgos de configuración, de manejo de secretos y datos, y de las propias pruebas. También hay decisiones abiertas de la tarea 1.3 (CORS, usuario activo, fuente del gasto) que condicionan la seguridad de las historias siguientes.

| ID | Severidad | Título | Estado |
|---|---|---|---|
| SEC-01 | Media | `CREWAI_INCLUDE_DATA=true` podría sacar datos de la aplicación hacia un servicio externo (semántica sin confirmar) | DETECTADO / PROPUESTO |
| SEC-02 | Media | `.env` no estaba confirmado como ignorado por git y se entrega como archivo | VERIFICADO (repositorio actual) |
| SEC-03 | Media | `baseline.md` (se versiona) puede contener salida sensible de `verify.py` | DETECTADO / PROPUESTO |
| SEC-04 | Media | CORS del mock sin decisión aprobada ni verificación | DETECTADO / PROPUESTO |
| SEC-05 | Media (preventivo) | Autenticación y autorización sin definir: "usuario activo" pendiente | DETECTADO / PROPUESTO |
| SEC-06 | Baja | Inyección de argumentos de git vía `H01_BASE_REF` en las pruebas | APLICADO (código y pruebas T-35 y T-36) |
| SEC-07 | Baja | Las pruebas imprimían valores de `.env` en mensajes y detectaban secretos solo por nombre de clave | APLICADO (código y prueba T-37) |
| SEC-08 | Baja | URL del mock sin validar y publicada en `environment.ts` | APLICADO en las pruebas (T-38); la URL real se revisa al fijarla |
| SEC-09 | Informativa | `GET /health` sin autenticación y `/openapi.json` expuesto | DETECTADO / PROPUESTO |

---

## 3. Hallazgos

### SEC-01: `CREWAI_INCLUDE_DATA=true` puede exponer datos fuera de la aplicación (Media)

- **Archivo:** `.env` (contenido entregado por Backend, tercera línea). Requisito en `tasks.md`, tarea 1.1.
- **Ubicación:** `CREWAI_INCLUDE_DATA=true`.
- **Evidencia:** el Issue exige ese valor. El nombre sugiere que el flujo de CrewAI incluye "data" en lo que procesa o envía. **No he visto el código que lee la variable ni qué datos incluye**, y no hay descripción en el contexto. La inferencia sobre su efecto no está comprobada.
- **Impacto:** si `true` hace que el flujo envíe datos del repositorio o de la aplicación a un proveedor de modelos o a una descripción de PR, esos datos salen del entorno. En una wallet pueden ser identidades, saldos o datos de KYC. El riesgo crece si el mock o los fixtures contienen datos reales.
- **Corrección propuesta (no aplicada):**
  1. Mantener el valor exigido por el Issue, pero documentar por escrito en la spec qué datos incluye y adónde van.
  2. Mientras se confirma, usar solo datos sintéticos en el mock, los fixtures y la salida de `verify.py`.
  3. Si el flujo admite un filtro de campos, excluir identificadores personales y secretos.
- **Comprobación reproducible (NO EJECUTADO):**
  ```bash
  # 1. localizar quién lee la variable y qué incluye
  grep -rn "CREWAI_INCLUDE_DATA" --exclude-dir=.git --exclude-dir=node_modules .
  # 2. revisar los datos semilla del mock y los fixtures: ¿hay valores reales?
  #    (revisión manual; anotar el resultado en baseline.md)
  ```
  Esperado: se identifica el punto de lectura y la lista de datos incluidos. Si no se puede identificar, el hallazgo queda abierto.
- **Estado:** DETECTADO (semántica sin confirmar), PROPUESTO. Verificado: ninguno.

### SEC-02: `.env` no confirmado como no versionado (Media)

- **Archivos:** `.env`, `.gitignore` (no visto).
- **Ubicación:** supuesto S1 del Arquitecto y S2 de Pruebas ("`.env` está en `.gitignore`"). Backend lo entrega como archivo ("# Archivos entregados").
- **Evidencia:** el propio texto declaraba el `.gitignore` como **[Supuesto]**. Se comprobó en el repositorio (sección 6, V-02 a V-04): `.gitignore` ya contiene `.env`, `.env.*` y `!.env.example`; `.env.example` ya existe y está versionado; `.env` está ignorado y nunca se versionó. El contenido actual solo tiene tres variables no secretas, así que el riesgo es **a futuro**: el backend ya anticipa que `GITHUB_TOKEN` "se inyectaría por variable de entorno" (supuesto 10).
- **Impacto:** si `.env` se versionara, un token pegado después quedaría en el historial de git y sería difícil de retirar.
- **Decisión (OBS-05):** no hay cambios en `.gitignore` ni en `.env.example`; quedan fuera del alcance de H01. Mantener los secretos fuera del repositorio (variables del sistema o gestor de secretos). Si la comprobación V-02 falla en otro clon, el cambio de `.gitignore` va en un PR aparte aprobado por el Arquitecto.
- **Comprobación reproducible (NO EJECUTADO):**
  ```bash
  git check-ignore -v .env           # esperado: imprime la regla de .gitignore (código 0)
  git ls-files --error-unmatch .env  # esperado: error (código != 0): no está versionado
  git log --all --oneline -- .env    # esperado: sin salida: nunca se versionó
  ```
- **Estado:** VERIFICADO en el repositorio actual (V-02 a V-04). Repetir en cada clon antes del merge.

### SEC-03: `baseline.md` puede filtrar salida sensible (Media)

- **Archivo:** `openspec/changes/registro-activacion-wallet/baseline.md` (ruta supuesta).
- **Ubicación:** campo "Salida resumida o fallos preexistentes" de la plantilla entregada por Backend.
- **Evidencia:** la plantilla pide pegar la salida de `python tools/verify.py`, y el Ingeniero de pruebas indica "se pega en `baseline.md`" (M-1). El contenido de `verify.py` no está en el contexto, así que no se sabe qué imprime (rutas, variables de entorno, URLs, trazas, datos). El archivo se versiona y puede acabar en un PR.
- **Impacto:** fuga de rutas internas, tokens impresos por un error, datos de usuario, y exposición adicional si `CREWAI_INCLUDE_DATA=true` hace que ese contenido se procese externamente (ver SEC-01).
- **Corrección propuesta (no aplicada):** pegar solo un resumen (conteo de pasa/falla y nombres de pruebas fallidas), nunca la salida completa. Revisar y redactar antes de hacer commit.
- **Comprobación reproducible (NO EJECUTADO):**
  ```bash
  grep -nEi '(token|secret|password|passwd|authorization|bearer|api[_-]?key|ghp_|github_pat_|-----BEGIN)' \
    openspec/changes/registro-activacion-wallet/baseline.md
  ```
  Esperado: sin coincidencias (código de salida 1 de `grep`). Complementar con revisión humana, porque el patrón no detecta datos personales.
- **Estado:** DETECTADO, PROPUESTO.

### SEC-04: CORS del mock sin decisión aprobada ni verificación (Media)

- **Archivos:** mock W1 (stack y código no incluidos), `spec.md` (decisión de 1.3).
- **Ubicación:** pregunta bloqueante "CORS del mock".
- **Evidencia:** la decisión de Arquitectura/Backend es solo una propuesta: origen `http://localhost:4200` **[Supuesto]**, métodos `GET` y `POST`, sin `*`. Pruebas la deja como "complemento manual NO EJECUTADO" y no hay aserción automatizada. No se ha visto la configuración real del mock.
- **Impacto:** un CORS permisivo (`*`, reflejo del `Origin` recibido o credenciales habilitadas) permite que una página de cualquier origen lea respuestas del mock desde el navegador del usuario. En historias posteriores esto alcanza datos de onboarding.
- **Corrección propuesta (no aplicada):** lista blanca explícita con el origen real del frontend, sin `*`, sin reflejar `Origin` y sin credenciales salvo necesidad demostrada. Ejemplo **solo si el mock fuera FastAPI**, lo cual no está confirmado:
  ```python
  from fastapi.middleware.cors import CORSMiddleware
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:4200"],   # confirmar el origen real
      allow_methods=["GET", "POST"],
      allow_headers=["Content-Type"],
      allow_credentials=False,
  )
  ```
- **Comprobación reproducible (NO EJECUTADO):**
  ```bash
  curl -si -H "Origin: https://evil.example" "$MOCK_W1_URL/health" | grep -i '^access-control-'
  curl -si -H "Origin: http://localhost:4200" "$MOCK_W1_URL/health" | grep -i '^access-control-'
  curl -si -X OPTIONS "$MOCK_W1_URL/health" \
    -H "Origin: http://localhost:4200" -H "Access-Control-Request-Method: DELETE" | grep -i '^access-control-'
  ```
  Esperado: (1) sin `Access-Control-Allow-Origin`; (2) exactamente `http://localhost:4200`, nunca `*` ni credenciales habilitadas sin justificación; (3) `DELETE` no figura entre los métodos permitidos.
- **Estado:** DETECTADO (decisión abierta), PROPUESTO.

### SEC-05: Autenticación y autorización sin definir; riesgo de acceso a recursos de otra persona (Media, preventivo)

- **Archivos:** `spec.md` (pregunta "usuario activo" y "fuente de gasto de adquisición"), futuros `api/app/routers/` y `services.py` (no tocados en H01).
- **Evidencia:**
  - La definición de "usuario activo" figura como **pendiente** en Arquitectura y Backend.
  - El origen del gasto de adquisición está pendiente ("dato de configuración o semilla del mock").
  - No hay endpoints de recursos por usuario en H01, así que **no se detectó IDOR ni salto de autorización confirmado**. Es un riesgo de diseño que debe cerrarse antes de implementar.
- **Impacto:** si un historial posterior toma el identificador de usuario del cliente (cuerpo, ruta o cabecera sin validar), una persona podría leer o activar la wallet de otra. Si el cliente envía el gasto de adquisición, podría manipularlo.
- **Corrección propuesta (no aplicada):**
  1. Aprobar por escrito en la spec, con responsable y fecha, que la identidad la determina el servidor (dependencia de FastAPI) y nunca un valor enviado por el cliente.
  2. Verificar la pertenencia del recurso al usuario autenticado en **cada** operación (lectura, activación, eventos).
  3. Elegir y documentar una política uniforme (404 o 403) para recursos ajenos, sin distinguir "no existe" de "no es tuyo" en el mensaje.
  4. Calcular y guardar el gasto de adquisición solo en servidor.
  5. Si se persiste por archivos, no usar el identificador crudo en rutas. Usar un hash con sal o clave del servidor si el identificador es adivinable (por ejemplo, un correo), porque un SHA-256 sin sal se puede revertir por diccionario. Cubrir además la concurrencia por usuario y los archivos preexistentes.
- **Comprobación reproducible para la historia que implemente el recurso (NO EJECUTADO, endpoints por definir):**
  1. Crear las identidades A y B con un recurso propio cada una.
  2. Con la identidad A, solicitar el recurso de B: `<METODO> <RUTA_DEL_RECURSO_DE_B>`.
  3. Esperado: respuesta de denegación acorde a la política (`403` o `404`) en formato `{"code": "...", "message": "..."}`, sin datos de B.
  4. Repetir sin identidad: esperado `401`.
  5. Enviar en el cuerpo o la ruta un identificador de B con la identidad de A: esperado que se ignore o rechace, sin cambio de propietario.
  6. Convertir estos casos en pruebas de la suite permanente del API (`api/tests/`) en la historia que implemente el recurso; no en H01.
- **Estado:** DETECTADO (preventivo), PROPUESTO. Sin código evaluable en H01.

### SEC-06: Inyección de argumentos de git vía `H01_BASE_REF` en las pruebas (Baja)

- **Archivos:** `api/h01_checks/h01_support.py`, `api/h01_checks/check_h01_guardrails.py`, `api/h01_checks/check_h01_change_state.py`.
- **Ubicación:** `base_ref()` y `run_git()` en `h01_support.py`. Uso en `_git_lines("diff", "--name-only", base_ref(), "--", path)` (T-22 a T-25) y en `test_diff_frontend_limitado_a_environment_ts` (T-33).
- **Evidencia:** `base_ref()` devuelve `os.environ.get("H01_BASE_REF", "HEAD")` sin validar y se coloca **antes** de `--` en `git diff`. `subprocess.run` usa lista de argumentos sin `shell=True`, así que **no hay inyección de shell**. Pero un valor que empiece por `-` se interpreta como opción de git. Según la documentación de `git diff`, existe la opción `--output=<archivo>`, que escribe el resultado en un archivo.
- **Impacto:** bajo. La variable la controla quien ejecuta las pruebas. Pasa a ser relevante si el entorno proviene de un CI alimentado por datos de un PR externo: podría sobrescribir archivos del runner o alterar el resultado de las guardas.
- **Corrección aplicada:** `base_ref()` valida el valor con `[0-9A-Za-z][0-9A-Za-z._/~^@{}-]*` (no puede empezar por `-`), lo resuelve con `git rev-parse --verify --quiet <ref>^{commit}` y usa el SHA resuelto; si falla lanza `ValueError`.
- **Comprobación reproducible (NO EJECUTADO contra el repositorio real; T-35 y T-36 cubren la lógica):**
  ```bash
  cd api
  H01_BASE_REF='--output=/tmp/h01_pwned' python -m pytest -q h01_checks/check_h01_guardrails.py
  ls /tmp/h01_pwned
  ```
  Esperado: las pruebas fallan con `ValueError` y `/tmp/h01_pwned` no existe.
- **Estado:** APLICADO. T-35 y T-36 pasan en la ejecución parcial del informe de Pruebas (sección 10).

### SEC-07: Valores de `.env` en mensajes de prueba y detección de secretos solo por nombre de clave (Baja)

- **Archivos:** `api/h01_checks/h01_support.py` (`validate_env`), `api/h01_checks/check_h01_change_state.py` (`test_env_real_no_versionado`).
- **Evidencia:**
  - `validate_env` genera `f"valor incorrecto en {key}: {values[key]!r} != {expected!r}"`, que imprime el valor real. Si alguien pega un token en `PR_REPO`, el valor queda en el log de la prueba o del CI.
  - La prueba T-18 usa su propia comprobación (`"TOKEN" in k.upper() or "SECRET" in k.upper()`), más débil que `SECRET_KEY_RE`, que cubre también `PASSWORD`, `API_KEY` y `PRIVATE`.
  - Ambas detectan secretos **por nombre de clave**, no por valor. Un token dentro de un valor de una clave permitida no se detecta.
- **Impacto:** fuga accidental de un secreto en logs y cobertura incompleta de la comprobación "sin secretos".
- **Corrección aplicada:**
  - `validate_env` informa `valor incorrecto en {key} (longitud N)` sin imprimir el valor. T-04, T-05 y T-08 siguen coincidiendo con el prefijo `valor incorrecto en`.
  - `test_env_real_no_versionado` (T-18) ya no tiene su propia comprobación de secretos: `read_env_problems` (T-17) usa `SECRET_KEY_RE` completa.
  - Se añadió un patrón de valores sospechosos (`ghp_`, `github_pat_`, `-----BEGIN`) que reporta `valor con aspecto de secreto en {key}` sin el valor (T-37).
- **Comprobación reproducible:**
  ```bash
  mkdir -p /tmp/h01_env && printf 'GITHUB_OWNER=user-bcp-student04\nPR_REPO=ghp_FAKE123456\nCREWAI_INCLUDE_DATA=true\n' > /tmp/h01_env/.env
  cd api/h01_checks && H01_REPO_ROOT=/tmp/h01_env python -c "from h01_support import read_env_problems, repo_root; print(read_env_problems(repo_root()))"
  ```
  Esperado: el resultado no contiene `ghp_FAKE123456`.
- **Estado:** APLICADO. T-37 pasa en la ejecución parcial del informe de Pruebas (sección 10).

### SEC-08: URL del mock sin validar y publicada en `environment.ts` (Baja)

- **Archivos:** `src/environments/environment.ts` (ruta supuesta), `api/h01_checks/h01_support.py` (`get_mock_url`, `validate_mock_url`, `url_in_environment_ts`).
- **Evidencia:**
  - La URL puede ser "local o del grupo" (tarea 1.4), es decir, un host compartido posiblemente por `http`.
  - `get_mock_url()` solo comprueba que no esté vacía. `url_in_environment_ts` acepta cualquier literal `http(s)://...`, incluidas URLs con credenciales embebidas (`http://usuario:clave@host`).
  - Todo lo que vaya en `environment.ts` termina en el bundle del navegador y en el repositorio, por lo que es público.
- **Impacto:** se podrían publicar credenciales, hosts internos o tokens en la URL. El tráfico `http` a un host compartido no está cifrado.
- **Corrección aplicada en las pruebas:** `get_mock_url()` llama a `validate_mock_url()`, que exige `http`/`https` con host y rechaza credenciales, query y fragmento (T-38).
- **Pendiente para quien fija la URL (rol Frontend, OBS-06):**
  - Para desarrollo, usar `http://localhost:<puerto>`. Para un host del grupo, usar `https`.
  - Nunca incluir usuario, clave, tokens ni parámetros sensibles en la URL.
- **Comprobación reproducible (NO EJECUTADO):**
  ```bash
  grep -nE "https?://[^'\"\` ]*@" src/environments/environment.ts   # esperado: sin coincidencias
  grep -nE "https?://" src/environments/environment.ts              # revisar el host y el esquema
  ```
- **Estado:** APLICADO en las pruebas (T-38 pasa en la ejecución parcial). La revisión de la URL real queda como V-10.

### SEC-09: `GET /health` sin autenticación y `/openapi.json` expuesto (Informativa)

- **Archivos:** mock W1 (no visto), `api/app/main.py` (no visto).
- **Evidencia:**
  - `GET /health` se asume sin autenticación (supuesto 2 de Arquitectura). El cuerpo es desconocido.
  - La prueba T-26 espera que `/openapi.json` devuelva `200`. Eso describe el estado actual del API en desarrollo, **no hay evidencia sobre producción**.
- **Impacto:** un `/health` que devuelva versión, configuración o estado de dependencias facilita el reconocimiento. Un esquema OpenAPI público revela la superficie de ataque.
- **Corrección propuesta (no aplicada):** respuesta mínima de `/health` sin detalles internos. Deshabilitar docs y OpenAPI fuera de desarrollo (`FastAPI(docs_url=None, redoc_url=None, openapi_url=None)` mediante configuración por entorno). Si se quita OpenAPI en algún entorno, ajustar T-26, que espera `200`.
- **Comprobación reproducible (NO EJECUTADO):**
  ```bash
  curl -si "$MOCK_W1_URL/health"   # esperado: 200 y cuerpo sin versiones, rutas ni configuración
  ```
- **Estado:** DETECTADO, PROPUESTO.

---

## 4. Revisión por área solicitada

| Área | Conclusión | Detalle |
|---|---|---|
| Autenticación | **NO EVALUABLE** | H01 no implementa autenticación. Ver SEC-05 y SEC-09. |
| Autorización / acceso a recursos de otra persona | **Sin hallazgo confirmado, riesgo preventivo** | No hay endpoints por usuario en H01. Ver SEC-05 para los requisitos y la comprobación A/B. |
| Validación de entradas | **Sin entradas de cliente en H01** | Las únicas entradas son `.env` y las variables `H01_BASE_REF`, `H01_REPO_ROOT` y `MOCK_W1_URL` de las pruebas. Ver SEC-06 y SEC-08. |
| Inyección (SQL, comandos, rutas) | **Sin hallazgo confirmado** | H01 no emite SQL (consultas parametrizadas exigidas en historias futuras). `subprocess.run` usa lista de argumentos sin shell. Único riesgo menor: inyección de argumentos de git (SEC-06). Futuro: validar rutas si se persiste en archivos (SEC-05). |
| Secretos | **Riesgos detectados** | El `.env` entregado no contiene secretos, pero SEC-02, SEC-03 y SEC-07 describen cómo podrían filtrarse. |
| Exposición de datos sensibles | **Riesgos detectados** | SEC-01 (posible salida a servicio externo), SEC-03 y SEC-09. |
| Dependencias | **NO EVALUADO** | H01 no cambia `requirements*.txt` y no se consultaron PyPI ni OSV. No se afirma nada sobre versiones ni CVE. |

---

## 5. Decisiones de 1.3: observaciones de seguridad

Las decisiones se cerraron en `spec.md` el 2026-11-06 con aprobación delegada de Miguel Ochoa Gallegos. Las observaciones de seguridad siguen aplicando a las historias que las implementen.

| Pregunta | Propuesta previa | Observación de seguridad |
|---|---|---|
| Frontera de eventos | El servidor registra los eventos | Correcto. El cliente no debe declarar eventos ni identidad. |
| Pasos adicionales al KYC simulado | Ninguno | Aceptable. Un cambio de spec exige revisión, y el KYC simulado no debe tratarse como real. |
| Persistencia de eventos | En memoria, sin migración | Reduce la exposición. Los eventos en memoria se pierden al reiniciar y no sirven como auditoría. Si pasan a archivos: concurrencia por usuario, archivos preexistentes, rutas sin identificadores crudos (SEC-05: HMAC-SHA-256 con clave del servidor, no SHA-256 sin sal). |
| CORS del mock | `http://localhost:4200`, `GET` y `POST`, sin `*` | Ver SEC-04. Confirmar el origen real y verificarlo con `curl`. |
| Usuario activo | Se determina en servidor | Ver SEC-05. La definición (wallet que pasa a `ACTIVE` al cerrar un onboarding exitoso) está aprobada en `spec.md` (2026-11-06). SEC-05 sigue vigente para las historias que implementen identidad. |
| Fuente de gasto de adquisición | Configuración mensual cargada en el servidor | Correcto: el cliente no lo calcula ni lo envía. Aprobada en `spec.md` (2026-11-06); el responsable de cargar el dato real se define en la historia de la salida analítica. |

---

## 6. Registro de verificaciones

**Verificaciones ejecutadas contra el repositorio real: 3 (V-02 a V-04, ver abajo).** El resto lista lo que debe ejecutarse. La persona que lo haga rellena las dos últimas columnas.

| # | Hallazgo | Comando o procedimiento | Resultado esperado (no observado) | Estado | Salida real |
|---|---|---|---|---|---|
| V-01 | SEC-01 | `grep -rn "CREWAI_INCLUDE_DATA" ...` y revisión de datos del mock | Punto de lectura localizado y datos documentados | NO EJECUTADO | – |
| V-02 | SEC-02 | `git check-ignore -v .env` | Regla impresa, código 0 | EJECUTADO (2026-11-06) | `.gitignore:1:.env	.env` |
| V-03 | SEC-02 | `git ls-files --error-unmatch .env` | Error (no versionado) | EJECUTADO (2026-11-06) | `error: pathspec '.env' did not match any file(s) known to git` |
| V-04 | SEC-02 | `git log --all --oneline -- .env` | Sin salida | EJECUTADO (2026-11-06) | Sin salida (0 commits) |
| V-05 | SEC-03 | `grep -nEi '(token\|secret\|...)' baseline.md` | Sin coincidencias | NO EJECUTADO | – |
| V-06 | SEC-04 | Tres `curl` con `Origin` (sección 3, SEC-04) | Sin ACAO para origen ajeno. Exacto para el propio. Sin `*` | NO EJECUTADO | – |
| V-07 | SEC-05 | Procedimiento A/B (cuando existan los recursos) | `403`/`404` sin datos de B. `401` sin identidad | NO EJECUTADO | – |
| V-08 | SEC-06 | T-35 y T-36 (`check_h01_support_logic.py`) | Rechazo con `ValueError` de opciones de git y de refs inexistentes | EJECUTADO parcialmente (2026-11-06, entorno de desarrollo) | 35 pasan en `check_h01_support_logic.py` |
| V-09 | SEC-07 | T-37: `.env` de prueba con valor falso en `PR_REPO` | El mensaje no contiene el valor | EJECUTADO parcialmente (2026-11-06, entorno de desarrollo) | Incluido en las 35 que pasan |
| V-10 | SEC-08 | T-38 y `grep` de credenciales en `environment.ts` | Rechazo de URL con credenciales; sin coincidencias en `environment.ts` | T-38 ejecutada; `grep` NO EJECUTADO | T-38 incluida en las 35 que pasan |
| V-11 | SEC-09 | `curl -si "$MOCK_W1_URL/health"` | `200` con cuerpo mínimo | NO EJECUTADO | – |
| V-12 | Base (1.1) | `grep -cE '^(GITHUB_OWNER=user-bcp-student04\|PR_REPO=wallet-app-g6\|CREWAI_INCLUDE_DATA=true)$' .env` | `3` | NO EJECUTADO | – |
| V-13 | Base (1.2) | `python tools/verify.py; echo "codigo_salida=$?"` | Desconocido (`verify.py` no visto) | NO EJECUTADO | – |
| V-14 | Base (1.4) | `curl -i "$MOCK_W1_URL/health"` | `HTTP 200` (supuesto) | NO EJECUTADO | – |
| V-15 | Alcance | `git status --short && git diff --stat` | Cambios solo en documentación de la historia, `environment.ts` y `api/h01_checks/`. Nada en `api/app/` ni `api/tests/`. `.env` no aparece | NO EJECUTADO | – |
| V-16 | Pruebas | `cd api && python -m pytest -rA -p no:cacheprovider tests/` y `h01_checks/check_h01_*.py` | 0 `failed`, 0 `error`, 0 `skipped` en `h01_checks/`. Resultado de la suite existente desconocido | NO EJECUTADO | – |

**Orden recomendado:** V-02 a V-04, V-12 y V-15 primero, porque solo exigen el repositorio. Después V-13 y V-14, y con sus resultados rellenar `baseline.md` redactando la salida (V-05). El resto depende de que exista la corrección o del mock.

---

## 7. Qué no se revisó (límites)

- **Contenido no disponible en el contexto:** `tools/verify.py`, `spec.md`, `tasks.md` real, `environment.ts`, el mock W1 (stack, CORS, cuerpo de `/health`), `api/app/*`, `.gitignore` y `requirements*.txt`.
- **Código de pruebas:** revisado por lectura y con la ejecución parcial descrita en el informe de Pruebas (sección 10). No se ejecutó contra el repositorio real ni contra el mock.
- **Dependencias:** sin análisis de versiones ni vulnerabilidades. Sin datos de PyPI ni OSV, no se emite ninguna afirmación. Si el Issue pidiera actualizar dependencias, deberían usarse pines exactos (`paquete==versión`, incluido `starlette==`) con versiones confirmadas en esas fuentes.
- **Pruebas dinámicas:** no se hizo ningún análisis dinámico, fuzzing ni escaneo de secretos del historial de git.

---

## 8. Preguntas pendientes para cerrar los hallazgos

1. ¿Qué datos incluye `CREWAI_INCLUDE_DATA=true` y adónde se envían? (SEC-01)
2. ¿`.env` está en `.gitignore` y nunca se versionó? (SEC-02)
3. ¿Qué imprime `tools/verify.py`? ¿Puede incluir datos sensibles? (SEC-03)
4. ¿Cuál es el origen real del frontend y la configuración CORS del mock? (SEC-04)
5. ¿Quién aprueba las decisiones de 1.3 y cuál es la definición de "usuario activo" y la fuente del gasto? (SEC-05)
6. ¿Las pruebas se ejecutan en un CI con variables controladas por terceros? (SEC-06)
7. ¿La URL del mock es local o de un host compartido, y con qué esquema? (SEC-08)
8. ¿Se deshabilitarán `/docs` y `/openapi.json` fuera de desarrollo? (SEC-09)