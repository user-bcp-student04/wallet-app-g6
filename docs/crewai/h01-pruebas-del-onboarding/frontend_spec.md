# frontend_spec.md

## Sin cambios en el frontend

### 1. Decisión

El Issue H01 «Pruebas del onboarding» no pide ningún componente, servicio, ruta, plantilla ni cambio de contrato de API. Por eso no entrego código Angular. Tampoco regenero `app.routes.ts` ni `app.component.ts`, porque no cambian.

### 2. Justificación con los criterios del Issue

- **El cambio es de pruebas.** La historia de Arquitectura dice: «El cambio consiste en añadir pruebas, no funcionalidad». Las tareas 3.1 a 3.12 de `tasks.md` (grupo 3) piden cobertura por endpoint (camino feliz y un camino de error), no un recorrido de usuario nuevo.
- **Fuera de alcance.** Arquitectura excluye nuevos endpoints, cambios de contrato y cambios de lógica de negocio. Si una prueba revela una discrepancia con la spec, se reporta como hallazgo y no se corrige en este cambio, salvo decisión explícita de una persona (S-7).
- **Lo único que Arquitectura prevé en el frontend** son archivos `*.spec.ts` nuevos, con API simulada y sin red real (S-6). Son pruebas del rol de Pruebas, no implementación de interfaz. El Backend aplica el mismo criterio y no entrega pruebas.
- **Las reglas del cliente que menciona el Issue** son: latencia inválida bloqueada (3.1), documento sin `TEST-` bloqueado (3.3), cancelar la confirmación de reset sin llamar a la API (3.8), pasos y bloqueo del onboarding (3.10), y eventos y mediana (3.11). El Issue las trata como comportamiento que se prueba, no como comportamiento que se construye. Si el frontend ya las implementa, las pruebas las verifican. Si alguna no existe, es un hallazgo para que una persona decida, no un entregable de este rol.
- **Contrato de API.** No añado endpoints ni campos. Los nombres de campo que no fija el Issue siguen pendientes de confirmar contra `design.md` y `schemas.py` (P-3, P-10).

### 3. Pendientes que no generan entregables del frontend

| # | Tema | Quién lo resuelve |
|---|---|---|
| 1 | Ruta de los `*.spec.ts` y ejecutor de pruebas (Karma o Jest) (P-2) | Arquitectura y Pruebas |
| 2 | Ubicación del cálculo de mediana y de los eventos (P-6) | Arquitectura |
| 3 | Si falta alguna regla del cliente (3.1, 3.3, 3.8, 3.10, 3.11), tratarla como hallazgo (S-7) | Una persona del equipo |
| 4 | Ejecución de las pruebas y adjunto al PR de la salida real, sin redactarla ni resumirla (3.12) | Persona responsable del PR |

### 4. Verificación

No hay recorrido nuevo que comprobar manualmente. Cuando existan los `*.spec.ts` del rol de Pruebas, una persona ejecutará `ng test --watch=false` (comando propuesto, sujeto a P-2) y adjuntará la salida real al PR. No se declara ninguna cobertura ni resultado, y nada se ha ejecutado en este paso.