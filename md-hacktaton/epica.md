# Hackatón · Billetera digital en Perú

La quinta actividad del programa reúne lo trabajado en los laboratorios anteriores. El reto parte de una épica y seis historias de usuario para construir y demostrar un MVP de billetera digital.

## Épica e historias

- [Épica del MVP](packages/epic/peru-wallet-mvp.sp.md).
- [Registro y activación](packages/user-stories/user-onboarding-mvp-completion.sp.md).
- [Confirmación de pagos de bajo monto](packages/user-stories/payer-low-value-payment-confirmation.sp.md).
- [Estado de pagos QR para comercios](packages/user-stories/merchant-qr-payment-status-visibility.sp.md).
- [Idempotencia en pagos](packages/user-stories/payment-idempotency-protection.sp.md).
- [Pagos fallidos y reversos](packages/user-stories/payment-failure-reversal-handling.sp.md).
- [Conciliación operativa](packages/user-stories/operations-transaction-reconciliation.sp.md).

## Carpeta de trabajo

Conserva la carpeta con matrícula y nombre creada por `curso` el Día 1. El repositorio del producto elegido para la hackatón se clona dentro de su `reqflow-workspace/`; si ya existe, reutiliza ese clon y comprueba `git remote -v`. Ejecuta cada comando desde la raíz del repositorio al que pertenece.

Si reutilizas los agentes del Día 4, `crewai/` y `guardrails/` permanecen al lado de `reqflow-workspace/`, dentro de la misma carpeta del curso. Cada uno conserva su propio repositorio y entorno. Las guías, la épica y las historias se leen o descargan del portal en https://bcp-ai-labs.pages.dev. No necesitas clonar `bcp-ai-labs` ni ejecutar la solución dentro del repositorio del portal.

## Cómo abordar el reto

1. Lee la épica y revisa las seis historias con tu equipo.
2. Elige el alcance de la demo. Registra los supuestos y las preguntas que necesitas resolver antes de implementar.
3. Convierte los criterios de aceptación del alcance elegido en especificaciones y pruebas. Aplica los agentes, Skills y herramientas trabajados en los labs.
4. Implementa el recorrido elegido y comprueba sus resultados. Para la demo, utiliza datos ficticios e integraciones simuladas; documenta qué simulaste.
5. Presenta el recorrido y sus pruebas. Explica qué funciona, qué queda pendiente y qué decisiones tomó el equipo.

## Evidencia para la demo

- Repositorio del equipo con instrucciones para ejecutar la solución.
- Historias seleccionadas y criterios de aceptación cubiertos.
- Pruebas o ejemplos reproducibles del comportamiento implementado.
- Supuestos, limitaciones y decisiones pendientes.
