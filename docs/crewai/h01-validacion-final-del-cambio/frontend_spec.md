# frontend_spec.md

## Sin cambios en el frontend

El Issue **[H01] Validación final del cambio** (tarea 4.1, grupo 4 de `openspec/changes/registro-activacion-wallet/tasks.md`) no requiere ningún cambio en el frontend Angular.

## Justificación según el Issue

- **La tarea es de verificación, no de funcionalidad.** El único criterio del Issue es ejecutar `python tools/verify.py` y registrar el resultado (fecha y hora, comando, código de salida y resumen de la salida). Eso no produce ninguna pantalla ni ningún recorrido de usuario.
- **No hay contrato de API que consumir.** El Arquitecto indica que el Issue no define endpoints ni esquemas. El desarrollador backend confirma que la tabla de endpoints está vacía y que no se modifica la lógica del API. Sin endpoints ni campos aprobados, el frontend no puede consumir nada sin inventarlo.
- **No hay campos, validaciones, acciones ni mensajes que definir.** Tampoco hay estados de carga, vacío, éxito o error que implementar. El único "error" del Issue es un fallo de `verify.py`. Se registra en `tasks.md` y lo gestiona el responsable de la entrega, no la interfaz.
- **El plan de Arquitectura lista el frontend Angular como "Sin cambios".** El resto del trabajo es documental: la línea 4.1 de `tasks.md` y su nota de resultado.
- **No se entrega ningún archivo Angular.** Entregar componentes, servicios, rutas o un `app.component.ts` nuevos quedaría fuera del alcance del Issue. Los archivos existentes (`main.ts`, `app.routes.ts`, `app.component.ts`, `index.html`, `package.json`, `angular.json`) no se tocan ni se regeneran.

## Cómo comprobar que el frontend no cambia

Este paso se hace en la revisión del cambio y **no se ha ejecutado**.

1. Revisar el diff del cambio y comprobar que no hay modificaciones bajo `src/app/` ni en `package.json` o `angular.json`.
2. Comprobar que los únicos archivos tocados por esta historia son la línea 4.1 de `tasks.md` y su nota de resultado. El resto de archivos de la base opcional del backend (`config.py`, `errors.py`, `middleware.py`, `main.py`) pertenece al backend y no afecta al frontend.
3. Verificar que la tarea 4.1 de `tasks.md` queda registrada con la plantilla definida por Arquitectura y Backend. Si `python tools/verify.py` devuelve un código de salida distinto de 0, se registra como fallido y se abre trabajo aparte.

## Supuestos y pendientes

- **Supuesto.** El contenido de `spec.md` (`wallet-onboarding`) no se recibió. Si define un recorrido de usuario con endpoints aprobados, el frontend deberá abordarse en un Issue distinto, con su contrato de API.
- **Pendiente (P1).** Contenido de `spec.md`.
- **Pendiente (P8).** Qué hacer si `verify.py` falla: bloquear el cierre del cambio o abrir un Issue nuevo.