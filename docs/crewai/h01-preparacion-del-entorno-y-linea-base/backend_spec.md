# backend_spec.md

**Feature:** [H01] Preparación del entorno y línea base
**Rol:** Desarrollador backend (Python / FastAPI)
**Fecha:** 2026-11-06

## 1. Resumen de la solución

H01 es una historia de **preparación de entorno**. El Issue no pide endpoints, servicios, esquemas ni persistencia nuevos en `api/app/`. El Arquitecto lo confirmó en su análisis: "API FastAPI: sin cambios en H01".

Por eso el backend entrega solo lo que el Issue exige y puede entregarse sin inventar contenido:

| Tarea | Qué entrega el backend | Estado |
|---|---|---|
| 1.1 | Archivo `.env` con las tres variables exactas (bloque de código más abajo) | Entregado |
| 1.2 | Comando para ejecutar `python tools/verify.py` y plantilla de registro de la línea base (sin resultados) | Comando entregado; resultado **NO EJECUTADO** |
| 1.3 | Decisiones conservadoras propuestas, pendientes de aprobación humana (sección 8) | Propuesto, no cerrado |
| 1.4 | Comando `curl` para verificar `GET /health` del mock W1 | URL desconocida; **NO EJECUTADO** |

**No se entrega** código Python nuevo, `api/requirements.txt`, `api/app/config.py` ni SQL. Los motivos están en las secciones 2, 7 y 9.

## 2. Stack y estructura de archivos

- **Stack del API:** Python + FastAPI (Starlette), según el Issue y el plan de Arquitectura. No se usa Java, Quarkus ni Maven.
- **Estructura del repositorio** (solo lo relevante para H01):

```text
wallet-app-g6/
├── .env                                  <- NUEVO/ACTUALIZADO (1.1)
├── tools/
│   └── verify.py                         <- se ejecuta, NO se modifica (1.2)
├── src/environments/environment.ts       <- URL del mock W1 (1.4, rol Frontend; ruta supuesta)
├── openspec/changes/registro-activacion-wallet/
│   ├── tasks.md                          <- se marcan tareas 1.1 a 1.4 al completarlas
│   ├── baseline.md                       <- registro de línea base (ruta supuesta)
│   └── specs/wallet-onboarding/spec.md   <- decisiones de 1.3
└── api/
    ├── app/                              <- SIN CAMBIOS en H01
    │   ├── main.py
    │   ├── routers/
    │   ├── services.py
    │   ├── schemas.py
    │   └── config.py
    ├── h01_checks/                       <- NUEVO: comprobaciones de H01 (rol Pruebas), fuera de api/tests/
    ├── tests/                            <- SIN CAMBIOS (no se tocan ni se añade nada)
    └── requirements.txt                  <- SIN CAMBIOS
```

**Por qué no se entregan `api/app/config.py` ni `api/requirements.txt`:**
- Ya existen en el repositorio y su contenido no está en el contexto.
- El Issue no pide cambiarlos.
- Entregar una versión "completa" sobrescribiría líneas existentes que no conozco. Las reglas piden conservarlas tal cual, y hacerlo a ciegas sería inventar.
- Si Arquitectura o el revisor piden que `config.py` lea `GITHUB_OWNER`, `PR_REPO` o `CREWAI_INCLUDE_DATA`, se hará en otra historia con el archivo actual a la vista.
- `api/h01_checks/` es el único directorio nuevo bajo `api/`. Lo entrega el rol de Pruebas, contiene solo comprobaciones de la historia y no toca `api/app/` ni `api/tests/`.

## 3. Tabla de endpoints

El backend FastAPI **no implementa ningún endpoint en H01**. El único endpoint involucrado es externo y pertenece al mock W1:

| Método | Ruta | Entrada | Respuesta | Errores |
|---|---|---|---|---|
| GET | `/health` (mock W1, no FastAPI de `api/app/`) | Ninguna. **[Supuesto]** sin autenticación ni cuerpo | **[Supuesto]** HTTP `200`. El cuerpo **no está especificado** y no se inventa | Si el mock no está levantado: error de conexión del cliente (sin cuerpo de API). H01 no define errores propios |

## 4. Reglas de validación

No hay entradas de usuario ni de cliente HTTP en H01. Las únicas reglas son sobre el archivo `.env`, y son comprobables:

| Regla | Valor exigido | Cómo se comprueba |
|---|---|---|
| `GITHUB_OWNER` | exactamente `user-bcp-student04` | `grep -E` con ancla `^…$` |
| `PR_REPO` | exactamente `wallet-app-g6` | ídem |
| `CREWAI_INCLUDE_DATA` | exactamente `true` | ídem |
| Sin secretos | El `.env` de H01 no contiene tokens ni contraseñas | Revisión visual |
| No versionado | `.env` está en `.gitignore` (ya contiene `.env` y `.env.*`; no se modifica) | `git check-ignore -v .env` |

## 5. Manejo de errores

- H01 no añade handlers ni formatos de error.
- Se mantiene la convención ya acordada para historias posteriores: `{"code": "...", "message": "..."}` con el código HTTP del contrato (400, 401/403, 404, 409, 413), incluidos los handlers de `HTTPException`, `RequestValidationError` y `Exception`, sin filtrar trazas, rutas ni secretos.
- Esta convención no se implementa ni se altera ahora. El código existente de `api/app/main.py` no se toca.

## 6. Límites y archivos

No aplica: H01 no tiene subidas de archivos ni límites de tamaño. Tampoco hay concurrencia de usuarios ni aislamiento por propietario, porque no se maneja identidad ni se escriben archivos de usuario.

## 7. Origen de la persistencia

- **H01 no usa base de datos ni persistencia de datos de negocio.** Por eso **no se emite SQL** (ni `-- schema.sql` ni migración).
- En el contexto no aparece un contrato de Datos aprobado, y el Issue no pide tablas. Si en una historia posterior se añade persistencia, se consumirá el contrato de Datos (si existe) o se emitirá SQL con primera línea `-- nombre.sql`, con consultas parametrizadas.
- Transacciones: no aplican.

## 8. Recorrido de un caso válido y de un caso de error

### Caso válido: `.env` correcto y mock W1 en marcha
1. Entrada: la persona edita `.env` en la raíz de `wallet-app-g6` con las tres variables.
2. Validación: `grep -E` comprueba valores exactos y devuelve 3 líneas.
3. Almacenamiento: solo el archivo local `.env` (sin base de datos, no versionado). Nada toca `api/app/`.
4. Línea base: `python tools/verify.py` se ejecuta y se registra fecha, comando, código de salida y resultado en `baseline.md`.
5. Mock: `curl -i <URL_MOCK_W1>/health` devuelve `200`. Esa URL se fija en `environment.ts`.

### Caso de error: mock W1 apagado o URL incorrecta
1. Entrada: se ejecuta `curl` contra una URL donde no hay servicio.
2. Resultado esperado: curl no recibe respuesta HTTP y termina con código de salida distinto de 0 (típicamente 7, "connection refused"). No hay cuerpo de API.
3. Acción: la tarea 1.4 **no** se marca; se corrige la URL o se levanta el mock. No se almacena nada.

### Decisiones propuestas para 1.3 (conservadoras, **a confirmar por una persona**)

| Pregunta | Decisión propuesta |
|---|---|
| Frontera de eventos | Los eventos se registran en el servidor (API/mock). El cliente solo dispara acciones |
| Pasos adicionales al KYC simulado | Ninguno. Cualquier paso adicional exige un cambio explícito de spec |
| Persistencia de eventos | No persistir en H01 (memoria del proceso, sin migración). Si luego se usan archivos, se deberá cubrir concurrencia por usuario, archivos preexistentes y migración |
| CORS del mock | Solo el origen de desarrollo del frontend (**[Supuesto]** `http://localhost:4200`), métodos `GET` y `POST`, sin `*` |
| Usuario activo | Se determina en el servidor con la identidad de una dependencia `Depends`. Definición propuesta en `spec.md`: wallet que pasa a `ACTIVE` al cerrar un onboarding exitoso, contada en el mes de la transición |
| Fuente de gasto de adquisición | Dato de configuración mensual (`attributedSpendPen`, en soles) cargado en el servidor, no calculado por el cliente. Redactada en `spec.md`; aprobación humana |

## 9. Supuestos y pendientes

**Supuestos**
1. `.env` está en `.gitignore` y no se versiona.
2. `GET /health` no requiere autenticación y devuelve `200` si el mock está operativo. El cuerpo es desconocido.
3. `environment.ts` está en `src/environments/environment.ts` y su cambio le corresponde al rol Frontend. El nombre de la propiedad debe seguir la convención ya existente en el archivo; no se inventa aquí.
4. La línea base se registra en `openspec/changes/registro-activacion-wallet/baseline.md`.
5. Las decisiones de 1.3 son propuestas y no están cerradas hasta que una persona las apruebe en la spec.
6. **Stack:** Si algún documento previo mencionara otro stack (Java/Quarkus/Maven), el Issue manda: Python + FastAPI.
7. No hay actualización de dependencias en este Issue. No se entrega `requirements.txt`, ni se proponen pines o versiones. Si se pidiera, se usarían pines exactos `paquete==versión` (incluido `starlette==`) con las versiones fijadas por el Arquitecto. Hoy no hay ninguna fijada, así que sería un **bloqueo**.
8. No se entregan pruebas de funcionalidad ni se toca `api/tests/`. Las comprobaciones de la historia las entrega el rol de Pruebas en `api/h01_checks/`.
9. No se entrega SQL: el Issue no usa base de datos.
10. No se registra `GITHUB_TOKEN` ni ningún secreto en `.env`; si el flujo lo necesitara, se inyectaría por variable de entorno del sistema, fuera del repositorio.

**Pendientes (requieren decisión humana)**
1. URL, puerto y stack del mock W1.
2. Cuerpo de respuesta de `GET /health`.
3. Ubicación definitiva de la línea base (archivo o descripción del PR).
4. Nombre de la propiedad en `environment.ts`.
5. Qué resultado de `python tools/verify.py` se considera aceptable (limpio o con fallos preexistentes documentados).
6. Responsable de aprobar las seis decisiones de 1.3.
7. Origen real del frontend para CORS.
8. Definición exacta de "usuario activo" y fuente concreta del gasto de adquisición.

**Nota sobre el formato pedido:** el formato estándar de entrega prevé código Python, `api/requirements.txt` y `api/app/config.py`. En este Issue no se entregan, porque el alcance los excluye y su contenido actual es desconocido. Esta ausencia es deliberada, no un olvido.

---

# Archivos entregados

```text
# .env
GITHUB_OWNER=user-bcp-student04
PR_REPO=wallet-app-g6
CREWAI_INCLUDE_DATA=true
```

Plantilla de registro de línea base (1.2). Es documentación **sin resultados**: la persona rellena los campos tras ejecutar el comando.

```text
# openspec/changes/registro-activacion-wallet/baseline.md
# Línea base H01

- Fecha y hora de ejecución: <RELLENAR>
- Comando: python tools/verify.py   (desde la raíz de wallet-app-g6)
- Código de salida: <RELLENAR>
- Resultado (pasa / falla): <RELLENAR>
- Salida resumida o fallos preexistentes: <RELLENAR>
- Ejecutado por: <RELLENAR>
```

---

# C. Verificación (todo **NO EJECUTADO**)

Ningún comando de esta sección se ha ejecutado. La persona los ejecuta y conserva la salida. Los resultados indicados son **esperados**, no observados.

### 1. Comprobar `.env` (tarea 1.1), caso válido

```bash
# desde la raíz de wallet-app-g6
grep -E '^(GITHUB_OWNER=user-bcp-student04|PR_REPO=wallet-app-g6|CREWAI_INCLUDE_DATA=true)$' .env
git check-ignore -v .env
```

- Esperado (NO EJECUTADO): tres líneas impresas por `grep` (código de salida 0). `git check-ignore -v` imprime la regla de `.gitignore` que ignora `.env` (el `.gitignore` actual ya la contiene). Si no imprime nada, se escala al Arquitecto: añadir la regla sería un cambio fuera del alcance (OBS-05).

### 2. Línea base (tarea 1.2)

```bash
python tools/verify.py
echo "codigo_salida=$?"
```

- Esperado (NO EJECUTADO): desconocido. El contenido de `verify.py` no está en el contexto. Se registra la salida real en `baseline.md`.

### 3. Mock W1 responde (tarea 1.4), caso válido

```bash
# sustituir <URL_MOCK_W1> por la URL local o del grupo (pendiente de confirmar)
curl -i <URL_MOCK_W1>/health
```

- Esperado (NO EJECUTADO): estado `HTTP/1.1 200 OK` (supuesto). El cuerpo es desconocido y no se inventa.

### 4. Caso de error: mock apagado o puerto incorrecto

```bash
# puerto sin servicio (ejemplo: 59999)
curl -i http://localhost:59999/health
echo "codigo_salida=$?"
```

- Esperado (NO EJECUTADO): sin respuesta HTTP; curl muestra `Failed to connect ... Connection refused` y `codigo_salida` distinto de 0 (típicamente 7). No se marca la tarea 1.4.

### 5. Caso de error de `.env`: variable ausente o con valor distinto

```bash
# debe imprimir 3; cualquier otro número indica que falta una variable o su valor no coincide
grep -cE '^(GITHUB_OWNER=user-bcp-student04|PR_REPO=wallet-app-g6|CREWAI_INCLUDE_DATA=true)$' .env
```

- Esperado (NO EJECUTADO): `3` si el archivo es correcto; un número menor indica error de configuración.

### 6. Levantar el API y ejecutar pruebas (sin cambios de código en H01)

```bash
cd api
uvicorn app.main:app --reload
```

```bash
# desde la raíz del repositorio: suite existente, sin las comprobaciones de H01 (están en api/h01_checks/)
python tools/lab.py test api
```

- Esperado (NO EJECUTADO): desconocido. No se afirma que pase o falle; sirve para confirmar que H01 no ha alterado el comportamiento previo del API.

### 7. Comprobar que el diff está limitado a lo pedido

```bash
git status --short
git diff --stat
```

- Esperado (NO EJECUTADO): cambios solo en la documentación de la historia, en `environment.ts` (rol Frontend) y en el directorio nuevo `api/h01_checks/` (rol Pruebas). `.env` no debe aparecer si está ignorado. Nada en `api/app/` ni en `api/tests/`.