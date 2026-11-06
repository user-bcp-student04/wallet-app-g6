# user_story.md

## Historia de usuario

**Como** responsable de la entrega del cambio `registro-activacion-wallet`,
**quiero** ejecutar `python tools/verify.py` y registrar su resultado (H01, tarea 4.1),
**para** tener evidencia verificable de que el cambio cumple la validación final antes de darlo por cerrado.

**Información explícita recibida:** el Feature es "[H01] Validación final del cambio". La spec está en `openspec/changes/registro-activacion-wallet/specs/wallet-onboarding/spec.md`. La tarea es `4.1 Ejecutar python tools/verify.py y registrar el resultado` (grupo 4 de `tasks.md`).

**Información no recibida:** el contenido de la spec, el de `tasks.md` (grupos 1–3), el código de `tools/verify.py` y los contratos de API existentes. Nada de eso se infiere a continuación. Lo que no está en el Issue se marca como **[Supuesto]** o como pregunta en la sección 5.

---

## 1. Resumen del cambio y alcance

**Resumen.** Esta historia es una tarea de verificación, no de desarrollo de funcionalidad. Consiste en ejecutar el script `tools/verify.py` sobre el estado final del cambio `registro-activacion-wallet` y dejar constancia del resultado.

**Dentro del alcance**
- Ejecutar `python tools/verify.py` desde la raíz del repositorio.
- Registrar el resultado: fecha/hora, comando, código de salida y resumen de la salida.

**Fuera del alcance**
- Modificar la lógica del API, el frontend o `tools/verify.py`.
- Añadir endpoints o cambiar contratos de API. El Issue no los pide.
- Actualizar dependencias. El Issue no lo pide, así que no aplican pins de `requirements*.txt` ni de `starlette`. Si la spec lo exigiera, habría que fijar cada paquete con `==`, incluido `starlette`, y confirmar versiones con PyPI y OSV (ver sección 5).
- Corregir fallos que `verify.py` reporte. Si falla, se registra el fallo y se abre trabajo aparte **[Supuesto]**.

**Resultado de la ejecución.** No se ha ejecutado nada al redactar este documento. No se declara ningún resultado, y el campo se rellena solo tras la ejecución real (plantilla en la sección 4).

---

## 2. Componentes afectados, sus responsabilidades y límites

| Componente | Ruta | Responsabilidad en esta historia | Límite |
|---|---|---|---|
| Script de verificación | `tools/verify.py` | Realizar las comprobaciones finales del cambio y devolver un código de salida. | Solo se ejecuta; no se edita. Qué comprueba exactamente es **desconocido** (pregunta P2). |
| Plan de tareas | `openspec/changes/registro-activacion-wallet/tasks.md` | Marcar 4.1 como hecha y alojar la nota con el resultado **[Supuesto]**. | Solo cambia la línea 4.1 y su nota; el resto no se toca. |
| Spec | `openspec/changes/registro-activacion-wallet/specs/wallet-onboarding/spec.md` | Fuente de los criterios que `verify.py` debería respaldar. | Solo lectura. Su contenido no está disponible. |
| API (FastAPI/Starlette) | `api/app/` (`main.py`, `routers/`, `services.py`, `schemas.py`, `config.py`) | Sin cambios en esta historia. Es el sistema bajo verificación. | No se modifica. |
| Pruebas del API | `api/tests/` | Sin cambios. Solo se modificaría si la spec exigiera pruebas nuevas, lo que sería otra historia. | No se modifica. |
| Frontend Angular | (no indicado) | Sin cambios. | No se modifica. |

**Aclaración de ubicaciones.** Las rutas `api/app/...` y `api/tests/` son las convenciones cerradas del stack. Aquí solo delimitan lo que **no** cambia.

---

## 3. Contrato de API relevante

**No puede determinarse a partir de la información recibida.** El Issue no lista endpoints, esquemas de entrada ni de respuesta. La spec `wallet-onboarding` podría definirlos, pero su contenido no se aportó. Por eso no se inventan rutas, métodos ni campos.

**Información que falta para completar esta sección**
1. Endpoints, métodos HTTP, rutas y esquemas de petición/respuesta de `wallet-onboarding` (registro y activación de wallet).
2. Escenarios de error de la spec, con su código HTTP y su `code`.
3. Si hay límites de tamaño o de formato de entrada.
4. Cómo se identifica al propietario (ver supuestos).

**Decisiones conservadoras por defecto.** Solo se aplican si la spec define endpoints que las necesiten. Cada una es un **[Supuesto]** y debe contrastarse con la spec:

- **Formato único de error.** Todo error responde `{"code": "<CODIGO>", "message": "<texto>"}`, con un `code` y un código HTTP definidos por cada error del contrato. Catálogo base:

| Situación | HTTP | `code` |
|---|---|---|
| Sin identidad | 401 | `UNAUTHENTICATED` |
| Cuerpo excede el tamaño permitido | 413 | `PAYLOAD_TOO_LARGE` |
| Cuerpo inválido | 422 | `INVALID_REQUEST` |
| Recurso ya existente o conflicto de concurrencia | 409 | `CONFLICT` |

  Los nombres de `code` son propuestos y deben alinearse con los de las interfaces existentes, si los hay.

- **Identidad.** Se obtiene mediante una dependencia de FastAPI (`Depends`) en el servidor, nunca de un valor enviado por el cliente en el cuerpo o en parámetros. Formato propuesto: identificador de propietario como cadena opaca no vacía. El directorio de persistencia del propietario se deriva con `hashlib.sha256(owner_id.encode("utf-8")).hexdigest()`. Ni el identificador ni el hash ni la ruta aparecen en ninguna respuesta.

- **Riesgos de persistencia** (si la spec implica almacenamiento en archivos):
  - *Concurrencia del mismo usuario:* serializar escrituras por propietario con un lock por `owner_hash` y escribir de forma atómica (archivo temporal más `os.replace`).
  - *Archivos preexistentes:* no sobrescribir en silencio. Responder 409 `CONFLICT`, salvo que la spec indique idempotencia.
  - *Migración:* no se asume ninguna. Si ya existen datos con otro esquema, hay que decidirlo (pregunta P5).

**Ejemplo de error (solo ilustrativo del formato, sin endpoint real):**
```json
{"code": "UNAUTHENTICATED", "message": "Identidad no proporcionada."}
```

---

## 4. Trazabilidad de criterios de aceptación

**Criterio explícito del Issue**

| ID | Criterio | Componente responsable | Forma verificable de comprobarlo |
|---|---|---|---|
| CA-1 | Se ejecuta `python tools/verify.py` y se registra el resultado (tarea 4.1). | `tools/verify.py` (ejecución) y `tasks.md` (registro) | Ejecutar `python tools/verify.py; echo "exit=$?"` desde la raíz del repo. Comprobar que existe en `tasks.md` la tarea 4.1 marcada `[x]` con fecha/hora, comando, código de salida y resumen de la salida. Código de salida 0 = verificación superada **[Supuesto: convención estándar]**. |

**Plantilla de registro** (a rellenar tras la ejecución real; no contiene resultados):
```markdown
- [x] 4.1 Ejecutar `python tools/verify.py` y registrar el resultado
  - Fecha/hora: <AAAA-MM-DDThh:mm:ss±hh:mm>
  - Comando: `python tools/verify.py`
  - Versión de Python: <salida de `python --version`>
  - Código de salida: <n>
  - Resultado: <APROBADO | FALLIDO>
  - Resumen de la salida: <líneas relevantes o referencia al log>
```

**Criterios de la spec `wallet-onboarding`:** no pueden trazarse porque su contenido no se recibió. Cuando se aporten, cada escenario debe tener un componente responsable (`routers/`, `services.py`, `schemas.py`, `config.py`) y una prueba en `api/tests/` o una comprobación de `verify.py`. Si algún escenario no tiene cobertura, se declarará como brecha para que una persona la acepte.

**Pruebas existentes y brecha.** No se sabe qué pruebas de `api/tests/` cubren los POST con cuerpo válido. Hasta confirmarlo se declara como **brecha pendiente de aceptación humana** (pregunta P3).

---

## 5. Supuestos y preguntas pendientes

**Supuestos (decisiones conservadoras)**
- **S1.** Esta historia no modifica código ni dependencias; solo ejecuta el script y registra el resultado.
- **S2.** El código de salida 0 de `verify.py` significa éxito y cualquier otro significa fallo.
- **S3.** El resultado se registra en `tasks.md`, bajo la tarea 4.1, con la plantilla de la sección 4.
- **S4.** Si `verify.py` falla, la tarea 4.1 no se marca como completada con éxito. Se registra el fallo y se abre trabajo correctivo aparte.
- **S5.** Si la spec define endpoints, se aplican el formato de error `{"code","message"}`, el catálogo base de la sección 3, la identidad por dependencia de FastAPI con hash SHA-256 y las medidas de persistencia descritas.
- **S6.** La ubicación del código sigue `api/app/` (`main.py`, `routers/`, `services.py`, `schemas.py`, `config.py`) y `api/tests/`.
- **S7.** Sin actualización de dependencias en esta historia. Si la hubiera, se fijaría cada paquete con `==`, incluido `starlette`, y se citarían fecha y fuente de PyPI/OSV.

**Preguntas pendientes**
- **P1.** ¿Cuál es el contenido de `spec.md` (endpoints, escenarios, errores)?
- **P2.** ¿Qué comprueba `tools/verify.py` y qué argumentos, variables de entorno o servicios previos necesita? ¿Se ejecuta desde la raíz del repo?
- **P3.** ¿Qué pruebas existentes en `api/tests/` cubren los POST con cuerpo válido? Si ninguna, ¿una persona acepta la brecha?
- **P4.** ¿Dónde debe registrarse el resultado además de `tasks.md` (PR, CI, archivo de evidencia)?
- **P5.** ¿Hay datos preexistentes que exijan migración, o archivos ya existentes por propietario?
- **P6.** ¿Cuál es el mecanismo de identidad real del producto (cabecera, token, sesión) y su formato?
- **P7.** ¿El Issue incluye algún límite de tamaño de cuerpo que justifique el 413?
- **P8.** ¿Qué debe hacerse si `verify.py` falla: bloquear el cierre del cambio o abrir un Issue nuevo?