# frontend_spec.md

**Feature:** [H01] Preparación del entorno y línea base
**Rol:** Desarrollador frontend Angular 17 (componentes standalone)
**Fecha:** 2026-11-06

## 1. Decisión de alcance

**Sin cambios en el frontend.**

No se entregan componentes, servicios, rutas, plantillas, `app.routes.ts` ni `app.component.ts`. Este documento no incluye ningún bloque de código.

## 2. Justificación con los criterios del Issue

| Criterio del Issue | Efecto en el frontend |
|---|---|
| 1.1 Configurar `.env` con `GITHUB_OWNER`, `PR_REPO` y `CREWAI_INCLUDE_DATA` | Es configuración local del repositorio. No interviene el código Angular. |
| 1.2 Ejecutar `python tools/verify.py` y registrar la línea base | Es un script de Python y un registro documental. No hay pantalla ni flujo de usuario. |
| 1.3 Cerrar las preguntas bloqueantes de la spec | Son decisiones documentales. Ninguna se implementa en H01 (ver sección 4). |
| 1.4 Verificar `GET /health` del mock W1 y fijar la URL en `environment.ts` | Es una verificación operativa. Fijar la URL es solo un valor de configuración, no un componente ni un servicio. |

- El Issue no describe ningún recorrido de usuario. No hay formularios, campos, validaciones, acciones ni mensajes que definir.
- El plan de Arquitectura indica que en el frontend solo cambia el valor de la URL del mock en `environment.ts`, sin cambios de lógica ni de componentes.
- El backend confirma que no hay endpoints nuevos. El único endpoint implicado es `GET /health` del mock W1, que es una comprobación de disponibilidad y no un contrato de pantalla.
- Por tanto, los estados de carga, vacío, éxito y error de una pantalla no aplican. No hay pantalla en H01.
- La accesibilidad (etiquetas, teclado, foco visible) y la prevención de envíos duplicados tampoco aplican, porque no se añade ningún elemento de interfaz. Quedan como requisitos de las historias que sí introduzcan pantallas.
- Se mantienen `main.ts`, `index.html`, `package.json` y `angular.json` sin tocar.

## 3. Único ajuste relacionado con el frontend (tarea 1.4)

- **Archivo:** `src/environments/environment.ts` (ruta supuesta por Arquitectura).
- **Cambio:** solo el valor de la URL base del mock W1, con el nombre de propiedad que ya use el archivo.
- **Por qué no se entrega código:**
  - La URL y el puerto del mock son desconocidos.
  - El nombre de la propiedad existente es desconocido.
  - El contenido actual de `environment.ts` no está en el contexto. Reescribirlo sería inventar o sobrescribir líneas existentes.
- **Quién lo hace:** la persona responsable, después de que `GET /health` responda `200`. El valor fijado debe coincidir con la URL usada en la verificación.
- **Límite:** no se añaden claves nuevas ni servicios que consuman esa URL. Ningún componente la usa todavía.

## 4. Decisiones de 1.3 que afectan al frontend en historias futuras

Son propuestas conservadoras del Arquitecto, pendientes de aprobación humana. No se implementan en H01.

- **Eventos:** los registra el servidor. El cliente solo dispara acciones.
- **KYC simulado:** un único paso. Cualquier paso adicional exige un cambio explícito de la spec.
- **CORS del mock:** origen de desarrollo `http://localhost:4200` (supuesto), métodos `GET` y `POST`, sin comodín. Es relevante para el frontend, porque un origen distinto provocará errores de CORS en el navegador.
- **Usuario activo y gasto de adquisición:** los determina el servidor. El cliente no los calcula ni los envía.
- **Errores de API:** en historias posteriores se mostrarán al usuario con el formato `{"code": "...", "message": "..."}` acordado, sin inventar campos.

## 5. Pasos para comprobar que no hay cambios en el frontend

Nada de lo siguiente se ha ejecutado. Los resultados indicados son esperados, no observados.

1. **Diff limitado.** Ejecutar `git status --short` y `git diff --stat`. Esperado: dentro de `src/` solo puede aparecer `src/environments/environment.ts`. No debe aparecer nada bajo `src/app/`.
2. **Valor de la URL.** Buscar con `grep` la URL en `src/environments/environment.ts`. Esperado: coincide exactamente con la URL con la que `curl -i <URL_MOCK_W1>/health` devolvió `200`.
3. **Caso válido.** Con el mock levantado, `curl -i <URL_MOCK_W1>/health` debe devolver `HTTP 200`. El cuerpo es desconocido y no se verifica.
4. **Caso de error.** Con el mock apagado o un puerto incorrecto (por ejemplo `curl -i http://localhost:59999/health`), curl no recibe respuesta HTTP y termina con código distinto de 0, típicamente 7. La tarea 1.4 no se marca y no se modifica `environment.ts`.
5. **Compilación.** Ejecutar `ng build` o `npm run build` para confirmar que el cambio de URL no rompe la compilación. El resultado es desconocido hasta ejecutarlo.

## 6. Supuestos y pendientes

**Supuestos**
- `environment.ts` está en `src/environments/environment.ts`.
- `GET /health` no requiere autenticación y devuelve `200` con el mock operativo.
- La app Angular ya existente (`main.ts`, `app.component.ts`, `app.routes.ts`) no se modifica.

**Pendientes (decisión humana)**
1. URL y puerto del mock W1, y su stack.
2. Nombre de la propiedad existente en `environment.ts`.
3. Origen real del frontend para CORS (`http://localhost:4200` u otro).
4. Responsable de aprobar las seis decisiones de 1.3.