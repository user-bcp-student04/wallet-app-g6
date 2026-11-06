# chapter_review.md

**Feature:** [H01] Validación final del cambio, tarea 4.1 (`python tools/verify.py`)
**Cambio:** `registro-activacion-wallet`
**Fecha de la revisión:** 2026-11-06 (America/Bogota, UTC-05:00)
**Rol:** Chapter, revisor transversal

**Estado de la evidencia: NO EJECUTADO.** Esta revisión es estática, sobre el material de Arquitecto, Backend, Frontend, Pruebas y Seguridad. Ningún agente ejecutó `verify.py`, pytest, `pip-audit` ni consultas a PyPI/OSV. No afirmo ningún resultado de ejecución. **Este informe no sustituye ninguna aprobación humana.**

**Material recibido.** Llegó completo, sin truncamiento visible. No se recibieron `spec.md`, `tasks.md` (grupos 1–3) ni `tools/verify.py` (P1 y P2). Esto se trata como brecha, no como motivo único de rechazo.

---

## 1. Veredicto resumido

**RECHAZADO**, por un bloqueante de diseño: **B1, cambios fuera del alcance del Issue y contradicción de alcance entre entregables** (sección 4).

El diseño y las pruebas del criterio explícito CA-1 sí están cubiertos. El rechazo no viene de CA-1 sino de que el equipo entregó, además, una base de código y pruebas que el propio Arquitecto declaró fuera de alcance. Esa base trae hallazgos de seguridad abiertos y sin corregir.

---

## 2. Supuestos confirmados y stack

| Tema | Resultado |
|---|---|
| Stack | Todos los entregables usan Python/FastAPI en `api/` (`pytest`, `python tools/lab.py test api`, `uvicorn`, `hashlib`). **No hay mezcla de stacks ni otro stack distinto.** No hay rastro de Java, Maven ni Quarkus en lo entregado. Backend (S8) ignora explícitamente cualquier referencia legada. Se registra como **supuesto confirmado**, no como contradicción. |
| S2 (código de salida 0 = éxito) | Coherente en Arquitecto, Backend, Pruebas y Seguridad. Sigue siendo un **supuesto**: no se conoce el contrato de salida de `verify.py` (P2). |
| S4 (un fallo no se marca como éxito) | Coherente en las prosas de Arquitecto, Backend, Frontend y Pruebas. La plantilla textual lo contradice (O-1). |
| Persistencia | No hay base de datos ni archivos de negocio en el Issue. Lo único persistente es el registro en markdown de `tasks.md`. No aplica SQL ni `PreparedStatement`. |

---

## 3. Cobertura por criterio de aceptación

Leyenda: ✔ cubierto en diseño, ◐ cubierto parcialmente o con brecha, ✖ no cubierto, n/a no aplica. Ningún "Pruebas" implica resultado: todo está **NO EJECUTADO**.

| Criterio | Arquitectura | Persistencia | Implementación | Pruebas | Seguridad |
|---|---|---|---|---|---|
| **CA-1a.** Se ejecuta `python tools/verify.py` | ✔ Arquitecto §4 (CA-1), comando y supuesto S2 | n/a | ✔ Backend §8 y §C: es solo ejecutar, no hay código que escribir | ✔ T-V01 (comando con `tee` y `PIPESTATUS`). `test_h01_baseline_contract.py` valida que los artefactos existen. | ◐ SEC-06: ejecutar un script de contenido desconocido con credenciales reales y guardar su salida en `/tmp` |
| **CA-1b.** Se registra fecha/hora, comando, versión de Python, código de salida, resultado y resumen | ✔ Plantilla de Arquitecto §4 | ✔ El registro es markdown en `tasks.md`, bajo 4.1 | ✔ Plantilla en Backend §9 | ✔ `test_registro_4_1.py` (campos, placeholders, ISO, comando, versión, código, resumen) | ◐ SEC-03: nada vincula el registro a una ejecución real |
| **CA-1c.** Coherencia del registro: `exit==0` ⇔ APROBADO ⇔ `[x]` | ◐ S4 dice "un fallo no se marca como éxito", pero la plantilla marca siempre `[x]` (O-1) | n/a | ◐ Igual que la plantilla | ✔ `test_resultado_coherente_con_codigo_salida`, `test_estado_marca_coherente_con_resultado` (ST9) | n/a |
| **Criterios de `wallet-onboarding/spec.md`** | ✖ Sin contenido de la spec; Arquitecto declara que no puede trazarlos | ✖ | ✖ | ✖ No hay pruebas de endpoints (brecha declarada) | ✖ Autenticación, autorización, IDOR y activación son "no evaluables" (Seguridad §5) |
| **Alcance** (solo ejecutar y registrar; sin cambios de API, dependencias ni frontend) | ✔ Arquitecto §1 y §2 lo fijan | n/a | ✖ **Backend entrega 5 archivos de código y un manifiesto de dependencias** (B1) | ✖ **Pruebas entrega 5 archivos de prueba sobre ese código** (B1) | ◐ Seguridad revisa y encuentra hallazgos sobre ese código fuera de alcance |
| **Frontend sin cambios** | ✔ | n/a | ✔ Frontend entrega "sin cambios" y una forma de comprobarlo | ✔ ALC-1 (`git diff`) | n/a |

**Brechas sin cobertura que requieren aceptación humana** (no son bloqueantes por sí solas, porque no están en un criterio visible del Issue):
- Se desconoce el contenido de la spec y, por tanto, qué debería respaldar `verify.py` (P1, P2).
- Se desconoce qué pruebas existentes cubren los POST con cuerpo válido (P3).
- `verify.py` solo prueba lo que verifica internamente, y su código de salida es la única evidencia.

---

## 4. Bloqueantes de diseño (motivo del RECHAZADO)

### B1 · Cambios fuera del alcance y contradicción de alcance entre entregables

**Evidencia:**
1. Arquitecto §1 declara **fuera del alcance**: modificar la lógica del API, añadir endpoints y actualizar dependencias. S1 y S7 dicen que no se modifica código ni dependencias. Arquitecto §2 marca `api/app/` y `api/tests/` como "sin cambios".
2. Backend S1 afirma que "no modifica código ni dependencias", pero entrega en la sección B cinco archivos: `api/app/config.py`, `errors.py`, `middleware.py`, `main.py` y `api/requirements.txt`. Los llama "base opcional" sin ningún requisito del Issue que la justifique.
3. `main.py` y `config.py` ya figuran como existentes en Arquitecto §2. Backend dice "prevalecen los existentes", pero no confirma si existen ni cuál es su contenido. Un `main.py` que "se registraría aquí" no puede aplicarse sin riesgo de sobrescribir los routers reales.
4. `requirements.txt` fija `fastapi==0.115.0`, `starlette==0.38.6`, `uvicorn==0.30.6` y `pydantic==2.9.2`. Backend S7 reconoce que **no se verificaron** contra PyPI/OSV. Es una actualización de dependencias que el Issue no pide.
5. Pruebas añade `test_h01_errors.py`, `test_h01_body_limit.py`, `test_h01_config.py`, `test_h01_integration_main.py` y `test_h01_requirements.py` en `api/tests/`. Dependen de esa base (ST2). Si la base no se aplica, "se descartan por escrito", lo que deja la suite de línea base en estado indefinido. Además, `lab.py test api` las recogería y fallarían por falta de módulos.
6. Los criterios de alcance de Pruebas (ALC-1) y de Frontend aceptan "solo `tasks.md` (y la base B si se adoptó)". El conjunto de archivos del cambio queda condicional y sin decisión humana. Eso es un supuesto contradictorio entre entregables.
7. Seguridad evaluó esa base y abrió hallazgos sobre ella (SEC-01, SEC-02, SEC-04, SEC-05, SEC-07), **ninguno corregido**. SEC-02 recomienda tratar las dependencias como un Issue aparte, y SEC-01 es una hipótesis aún sin confirmar. Entregar código con hallazgos abiertos para una tarea de "validación final" agrava el problema.

**Cambio requerido (ruta preferida):**
- **Backend:** retirar de este cambio `config.py`, `errors.py`, `middleware.py`, `main.py` y `requirements.txt`. Moverlos a un Issue propio, con spec y contrato aprobados, donde se atiendan SEC-01, 02, 04, 05 y 07.
- **Ingeniero de pruebas:** retirar `api/tests/test_h01_errors.py`, `test_h01_body_limit.py`, `test_h01_config.py`, `test_h01_integration_main.py` y `test_h01_requirements.py` de este cambio. Reemplazar en ALC-1 la condición "y la base B si se adoptó" por "solo `tasks.md` (más el archivo de pruebas de registro, si una persona lo acepta)".
- **Arquitecto:** reafirmar por escrito el conjunto cerrado de archivos tocados.
- **Frontend:** actualizar el punto 2 de su comprobación en consecuencia.

**Ruta alternativa (solo si una persona decide ampliar el alcance):**
- Enmendar el Issue por escrito (decisión humana).
- Backend aplica el middleware corregido de SEC-01/SEC-04 (aún sin probar) y confirma por inspección que no sobrescribe `main.py` ni `config.py` existentes.
- Resolver SEC-02: pins verificados en PyPI/OSV con fecha y fuente, y dependencias de prueba declaradas en el manifiesto de desarrollo.
- Pruebas ejecuta V-01, V-02 y `pip-audit` con salida real.

**Verificación (NO EJECUTADO, tras la ruta preferida):**
```bash
git diff --name-only -- api | tee /tmp/h01_alcance_api.txt     # esperado: vacío
git diff --name-only | tee /tmp/h01_alcance_total.txt          # esperado: solo tasks.md (+ test_registro_4_1.py si se acepta)
git diff --name-only -- src package.json angular.json tools/verify.py   # esperado: vacío
```

---

## 5. Contratos incompatibles detectados

| # | Contradicción | Entregables | Gravedad | Estado |
|---|---|---|---|---|
| C1 | "No se toca código ni dependencias" frente a una base de código y pins entregados | Arquitecto §1/S1/S7, Backend S1 frente a Backend §B | Bloqueante | **B1** |
| C2 | La plantilla marca siempre `[x]`, mientras S4 dice que un fallo no se marca como éxito | Arquitecto §4, Backend §9 frente a S4 | Menor. Pruebas ya lo resolvió: `[x]` ⇔ APROBADO (ST9). | **O-1** |
| C3 | ALC-1 y Frontend aceptan un conjunto de archivos condicional ("si se adoptó") | Pruebas §3 y Frontend, punto 2 | Bloqueante por derivación | **B1** |
| C4 | Pruebas fuera del alcance en `api/tests/` dependen de módulos que quizá no existan (ST2) | Pruebas | Bloqueante por derivación | **B1** |

No se detectan contratos de API incompatibles: el Issue no define endpoints y la tabla de Backend §3 está vacía.

---

## 6. Observaciones no bloqueantes

| ID | Sev. | Observación | Responsable | Cambio requerido | Cómo verificarlo (NO EJECUTADO) |
|---|---|---|---|---|---|
| O-1 | Media | La plantilla de 4.1 marca `[x]` siempre, y S4 dice que un fallo no se marca como éxito. | Arquitecto y Backend | Corregir la plantilla: `[x]` solo si Resultado = APROBADO; con FALLIDO queda `- [ ] 4.1 …` y se abre trabajo aparte (alineado con ST9). | `python -m pytest openspec/changes/registro-activacion-wallet/tests/test_registro_4_1.py -v -rsxX` tras registrar el resultado real. |
| O-2 | Media | SEC-03: el registro puede escribirse a mano y pasar todas las pruebas. | Ingeniero de pruebas, con la plantilla de Arquitecto | Añadir `Commit` y `SHA-256 del log` (y, si hay CI, `Enlace CI`) a la plantilla y a `test_registro_4_1.py`. Archivar el log según P4. Idealmente que lo revise una persona distinta de quien ejecutó. | `git rev-parse HEAD` y `sha256sum <log archivado>` deben coincidir con la nota. Pytest de registro. |
| O-3 | Baja | SEC-06: la evidencia se guarda en `/tmp/h01_evidencia` con permisos por defecto, y `verify.py` es de contenido desconocido. Además, el resumen irá a un archivo versionado. | Ingeniero de pruebas y persona que ejecuta | Usar `umask 077; EV=$(mktemp -d)`. Ejecutar sin credenciales reales. Revisar y redactar la salida antes de pegarla en `tasks.md`. Si aparece un secreto, rotarlo. | `stat -c '%a %U' "$EV"` → `700`. `grep -nEi "(token\|secret\|password\|api[_-]?key\|authorization\|bearer\|BEGIN [A-Z ]*PRIVATE KEY)" "$EV/21_verify.log"` (heurístico). |
| O-4 | Baja | `test_registro_4_1.py` es un archivo nuevo en `openspec/changes/registro-activacion-wallet/tests/`. El alcance se declaró como "solo `tasks.md`". | Arquitecto, con aprobación humana | Decidir por escrito si se mantiene este archivo como artefacto de verificación o se sustituye por una revisión manual del registro. | Revisión del diff. |
| O-5 | Baja | `python tools/lab.py test api` es un supuesto sin confirmar (ST3); `verify.py` puede ya invocarlo (P2). | Ingeniero de pruebas | Confirmar qué comandos existen realmente. Si no existe, usar `cd api && python -m pytest tests`. | `python tools/lab.py --help` y revisión de `tools/verify.py`. |
| O-6 | Info | SEC-08: el 403 "Acceso denegado" puede permitir enumerar recursos ajenos cuando haya endpoints. Es una regla de diseño para el Issue futuro. | Arquitecto (Issue de `wallet-onboarding`) | Documentar: se filtra siempre por propietario autenticado y se responde 404 idéntico al caso "no existe". | Prueba con dos identidades sobre un recurso ajeno y uno inexistente (cuando existan endpoints). |
| O-7 | Info | Si se ejecuta la ruta alternativa de B1, aplican SEC-01, 02, 04, 05, 07 y 09 y V-01 a V-09 de Seguridad. | Backend, Pruebas y Seguridad | Ver `security_report.md`. | Ver §6 de Seguridad. |

---

## 7. Pruebas y comprobaciones pendientes

Todas **NO EJECUTADO**. Deben ejecutarse por una persona, con salida real adjunta, **después** de resolver B1.

| Orden | Responsable | Comando exacto | Criterio |
|---|---|---|---|
| 1 | Persona responsable de la entrega | `git status --short; git rev-parse HEAD; python --version` | Registrar el estado y la versión. |
| 2 | Persona responsable de la entrega (**ejecución real, no la hace un agente**) | `date --iso-8601=seconds; python tools/verify.py 2>&1 \| tee "$EV/21_verify.log"; echo "exit=${PIPESTATUS[0]}"` (en bash, con `EV` creado según O-3) | Código de salida registrado. Con 0 = APROBADO (S2). |
| 3 | Persona responsable de la entrega | Editar `tasks.md` con la plantilla corregida (O-1 y O-2), con valores reales del paso 2. | Sin placeholders `<…>`. |
| 4 | Ingeniero de pruebas | `python -m pytest openspec/changes/registro-activacion-wallet/tests/test_registro_4_1.py -v -rsxX` | 0 failed, 0 skipped. |
| 5 | Ingeniero de pruebas | `python tools/lab.py test api` y `cd api && python -m pytest tests -v -rsxX` | 0 failed, 0 errors, 0 skipped. Suite de regresión sin las pruebas fuera de alcance. |
| 6 | Revisor | `git diff --name-only` y `git diff --name-only -- api src package.json angular.json tools/verify.py` | Solo los archivos aceptados; las demás rutas, vacías. |
| 7 | Persona responsable de la entrega y Seguridad | Revisar el registro frente a O-3 y archivarlo en el destino de P4. | Sin secretos en `tasks.md`. |

**Solo si se elige la ruta alternativa de B1:**
```bash
cd api && python -m pytest tests/test_h01_body_limit.py -v -rsxX       # V-01 / V-02 (SEC-01)
pip-audit -r api/requirements.txt                                      # V-03 (SEC-02), en venv aparte, con red
```

---

## 8. Condiciones previas al merge (no son motivo de rechazo por sí solas)

1. Resolver B1 y obtener la re-entrega de Backend y Pruebas con el alcance corregido.
2. Ejecutar `python tools/verify.py` y registrar el resultado real (pasos 1 a 4 de la sección 7).
3. Adjuntar las salidas reales: `verify.py`, pytest de registro y regresión.
4. **Aprobaciones humanas** (no sustituidas por este informe):
   - la persona responsable de la entrega, que aprueba la ejecución y el registro;
   - una persona que decida la ruta de B1 (retirar la base o ampliar el alcance);
   - una persona que acepte las brechas P1, P2 y P3;
   - una persona que responda P4 (dónde se archiva la evidencia) y P8 (qué hacer si `verify.py` falla).

---

## 9. Hallazgos de seguridad: estado de traspaso

| ID | Estado a efectos de este Issue |
|---|---|
| SEC-01, 04, 05, 07, 09 | Se refieren a código fuera de alcance (B1). Quedan en el Issue donde se entregue la base. Aquí no se resuelven. |
| SEC-02 | Se refiere a dependencias fuera de alcance (B1). Se trata como Issue de actualización aparte, tal como recomienda Seguridad (P9). |
| SEC-03, SEC-06 | Aplican a este Issue: O-2 y O-3. |
| SEC-08 | Preventivo para `wallet-onboarding` (O-6). |
| Autenticación, autorización, IDOR y activación | **No evaluables** por falta de spec y código. No equivale a "sin hallazgos". Requiere aceptación humana. |

---

## 10. Veredicto

**VEREDICTO: RECHAZADO**

**Motivos y bloqueante de diseño:**
- **B1 · Cambios fuera del alcance del Issue.**
  - Backend entrega `config.py`, `errors.py`, `middleware.py`, `main.py` y `requirements.txt`, y Pruebas entrega cinco archivos de pruebas sobre ellos.
  - Arquitecto (§1, S1 y S7) y el propio Backend (S1) declaran que este Issue no modifica código ni dependencias.
  - Los archivos pueden colisionar con `main.py` y `config.py` existentes.
  - Los pins de `requirements.txt` no están verificados (Backend S7, SEC-02).
  - Hay hallazgos abiertos sobre ese código (SEC-01 y SEC-04, entre otros), y las correcciones propuestas por Seguridad no están aplicadas.
  - El conjunto de archivos del cambio quedó condicional ("si se adoptó") en Pruebas y Frontend.

**Qué sí cumple:**
- CA-1 tiene diseño, plantilla de registro y pruebas asociadas, y el stack Python/FastAPI es coherente sin mezclas.
- Frontend declara correctamente "sin cambios".
- Nadie afirma haber ejecutado nada ni inventa evidencia.

**Qué hay que hacer para pasar a APROBADO:** resolver B1 por la ruta preferida (retirar base y pruebas fuera de alcance, fijar el conjunto de archivos) y alinear la plantilla (O-1). Con eso el cambio no tendría bloqueantes de diseño. Aun así, **la aprobación final depende de la evidencia ejecutada y de las aprobaciones humanas** de la sección 8: `python tools/verify.py` aún no se ha ejecutado ni registrado.

**Condiciones previas al merge:** sección 8.
**Pruebas pendientes con responsable y comando:** sección 7.