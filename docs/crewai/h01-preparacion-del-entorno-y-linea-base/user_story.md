# user_story.md

**Feature:** [H01] Preparación del entorno y línea base
**Spec:** `openspec/changes/registro-activacion-wallet/specs/wallet-onboarding/spec.md`
**Tareas:** `openspec/changes/registro-activacion-wallet/tasks.md` (grupo 1)
**Fecha del análisis:** 2026-11-06

> **Limitaciones del análisis.** El contenido de la spec, de `tools/verify.py`, de `environment.ts` y del mock W1 no se incluyó en el contexto. Solo se dispone del texto del Issue (tareas 1.1 a 1.4). Todo lo demás se marca como **[Supuesto]** (decisión conservadora) o como **pregunta pendiente**. No se inventa ningún endpoint ni cuerpo de respuesta.

---

## Historia de usuario

**Como** integrante del equipo de `wallet-app-g6`,
**quiero** un entorno configurado, una línea base de verificación registrada, las preguntas bloqueantes de la spec cerradas y el mock W1 localizado y fijado en el frontend,
**para** empezar a implementar el registro y activación de la wallet sin ambigüedades y poder detectar regresiones desde un estado conocido.

---

## 1. Resumen del cambio y alcance

**Explícito en el Issue**
- 1.1 Configurar `.env` con `GITHUB_OWNER=user-bcp-student04`, `PR_REPO=wallet-app-g6` y `CREWAI_INCLUDE_DATA=true`.
- 1.2 Ejecutar `python tools/verify.py` en `wallet-app-g6` y registrar la línea base.
- 1.3 Cerrar seis preguntas bloqueantes de la spec: frontera de eventos, pasos adicionales al KYC simulado, persistencia de eventos, CORS del mock, usuario activo y fuente de gasto de adquisición.
- 1.4 Verificar que el mock W1 responde a `GET /health` en la URL local o del grupo, y fijar esa URL en `environment.ts`.

**Dentro del alcance**
- Configuración de entorno (`.env`).
- Ejecución y registro de la línea base.
- Decisiones documentadas para las seis preguntas.
- Una constante de URL del mock en `environment.ts`.

**Fuera del alcance**
- Lógica de negocio del registro y la activación.
- Nuevos endpoints o cambios en `api/app/`.
- Cambios en `tools/verify.py`.
- Actualización de dependencias: el Issue no la pide, por lo que no se proponen pins ni cambios en `requirements*.txt`.
- Pruebas nuevas de funcionalidad. H01 se comprueba con comandos de verificación (sección 4).

---

## 2. Componentes afectados, responsabilidades y límites

| Componente | Ruta | Responsabilidad en H01 | Límite |
|---|---|---|---|
| Configuración local | `.env` (raíz de `wallet-app-g6`) | Contiene `GITHUB_OWNER`, `PR_REPO`, `CREWAI_INCLUDE_DATA`. | Solo esas tres variables. **[Supuesto]** No se versiona; debe estar en `.gitignore`. |
| Script de verificación | `tools/verify.py` | Se ejecuta y se registra su resultado. | **No se modifica.** Su contenido y salida esperada son desconocidos. |
| Registro de línea base | **[Supuesto]** `openspec/changes/registro-activacion-wallet/baseline.md` | Guarda fecha, comando, resultado (pasa/falla) y salida resumida. | Solo documentación. Si el equipo prefiere otra ubicación (por ejemplo, la descripción del PR), se ajusta. |
| Spec y tareas | `openspec/changes/registro-activacion-wallet/specs/wallet-onboarding/spec.md`, `tasks.md` | Se documentan las decisiones de 1.3 y se marcan las tareas. | No se añaden requisitos nuevos. Las decisiones solo cierran las preguntas ya existentes. |
| Mock W1 | URL local o del grupo (desconocida) | Debe responder a `GET /health`. | Se verifica; no se modifica en H01. Su stack no está indicado en el Issue. |
| Frontend Angular | **[Supuesto]** `src/environments/environment.ts` | Almacena la URL base del mock W1 (el nombre de la propiedad debe seguir la convención ya existente en el archivo). | Solo cambia ese valor. No hay cambios de lógica ni de componentes. |
| API FastAPI | `api/app/` (`main.py`, `routers/`, `services.py`, `schemas.py`, `config.py`) y `api/tests/` | **Sin cambios en H01.** | Las convenciones de esta ubicación se aplican a las historias siguientes. |

---

## 3. Contrato de API relevante

### 3.1 Único endpoint involucrado: `GET /health` del mock W1

| Elemento | Detalle |
|---|---|
| Método y ruta | `GET /health` (explícito en 1.4) |
| Entradas | Ninguna. **[Supuesto]** Sin autenticación ni cuerpo. |
| Respuesta exitosa | **[Supuesto]** HTTP `200`. **El cuerpo no está especificado**: no se inventa. El criterio verificable es el código `200`. |
| Errores | Si el mock no está levantado, hay un error de conexión del cliente y no hay cuerpo de API. H01 no define errores propios. |

Ejemplo de comprobación (el puerto o host reales están pendientes):
```bash
curl -i <URL_MOCK_W1>/health
```

### 3.2 Convenciones a aplicar en historias posteriores (decisiones conservadoras, no contrato de H01)
Estas decisiones aplican si el API FastAPI incorpora endpoints; no se implementan en H01.
- **Formato único de error:** `{"code": "...", "message": "..."}`, con código HTTP y `code` definidos por cada error (por ejemplo, `401` sin identidad, `413` tamaño excedido).
- **Identidad:** viene de una dependencia de FastAPI en el servidor, nunca de un valor enviado por el cliente. Es un identificador opaco. Si se persiste por propietario, el directorio se deriva con SHA-256 del identificador. Ningún valor derivado del propietario se expone en las respuestas.

### 3.3 Información que falta
- URL y puerto del mock W1, y su stack.
- Cuerpo de respuesta de `GET /health`.
- Contrato de los endpoints de registro y activación (viven en la spec, que no se proporcionó).

---

## 4. Trazabilidad de criterios de aceptación

El Issue no enumera criterios de aceptación separados; se toma cada tarea como criterio.

| Criterio | Componente responsable | Forma verificable |
|---|---|---|
| **1.1** `.env` con las tres variables y valores exactos | `.env` | `grep -E '^(GITHUB_OWNER=user-bcp-student04\|PR_REPO=wallet-app-g6\|CREWAI_INCLUDE_DATA=true)$' .env` devuelve 3 líneas. `git check-ignore .env` confirma que no se versiona **[Supuesto]**. |
| **1.2** Línea base ejecutada y registrada | `tools/verify.py`, `baseline.md` | Ejecutar `python tools/verify.py` desde `wallet-app-g6`. El registro contiene fecha, comando, código de salida y resultado. Si hay fallos previos, quedan documentados como línea base y no se corrigen en H01. |
| **1.3** Seis preguntas cerradas | `spec.md` y `tasks.md` | Cada una de las seis preguntas tiene una decisión escrita, con responsable y fecha de aprobación en la spec. Ver la tabla siguiente. |
| **1.4** Mock responde y URL fijada | Mock W1, `environment.ts` | `curl -i <URL>/health` devuelve `200`. `grep` de la URL en `environment.ts` coincide con la usada en el `curl`. El frontend no tiene otros cambios (`git diff` limitado a ese archivo). |

### Decisiones propuestas para 1.3 (todas son **[Supuesto]** conservador, a confirmar por una persona)

| Pregunta | Decisión conservadora propuesta |
|---|---|
| Frontera de eventos | Los eventos se registran en el servidor (API/mock), no los declara el cliente. El frontend solo dispara las acciones. |
| Pasos adicionales al KYC simulado | Ninguno: el KYC simulado es un único paso. Cualquier paso adicional requiere un cambio explícito de spec. |
| Persistencia de eventos | No persistir en H01: se mantienen en memoria del proceso, sin migración (no hay datos previos conocidos). Si luego se persisten en archivos, se deberán cubrir la concurrencia del mismo usuario (escritura atómica o bloqueo por usuario), los archivos preexistentes (no sobrescribir sin comprobar) y la migración si hubiera datos. |
| CORS del mock | Permitir solo el origen de desarrollo del frontend (**[Supuesto]** `http://localhost:4200`, puerto por defecto de Angular), métodos `GET` y `POST`, sin comodín `*`. |
| Usuario activo | Se determina en el servidor con la identidad de la dependencia. "Activo" significa que completó la activación de la wallet según la spec. La definición exacta del estado está pendiente. |
| Fuente de gasto de adquisición | Dato de configuración o semilla del mock, no calculado por el cliente. El origen real está pendiente. |

---

## 5. Supuestos y preguntas pendientes

**Supuestos**
1. `.env` está en `.gitignore` y no se versiona.
2. `GET /health` no requiere autenticación y devuelve `200` cuando el mock está operativo.
3. `environment.ts` está en `src/environments/environment.ts`.
4. La línea base se registra en `openspec/changes/registro-activacion-wallet/baseline.md`.
5. Las decisiones de 1.3 de la sección 4 son propuestas conservadoras, pendientes de aprobación.
6. No hay actualización de dependencias en este Issue; no se tocan `requirements*.txt`. Si se pidiera, aplicaría pin exacto `paquete==versión` (incluido `starlette==`) y las versiones se confirmarían con PyPI y OSV, porque no hay datos consultados en el contexto.
7. No se añaden pruebas en `api/tests/` en H01, porque no cambia código del API.

**Preguntas pendientes**
1. ¿Cuál es la URL y el puerto del mock W1 (local o del grupo)? ¿Cuál es su stack?
2. ¿Qué devuelve `GET /health` (cuerpo)?
3. ¿Dónde debe registrarse la línea base: archivo en el repositorio o descripción del PR?
4. ¿Cuál es el nombre de la propiedad existente en `environment.ts` para la URL del mock?
5. ¿Qué resultado se considera aceptable para `python tools/verify.py` en la línea base (pasa limpio, o se admiten fallos preexistentes documentados)?
6. ¿Quién aprueba las seis decisiones de 1.3?
7. ¿El origen real del frontend para CORS es `http://localhost:4200` u otro?
8. ¿Cuál es la definición exacta de "usuario activo" y cuál es la fuente concreta del gasto de adquisición?