## ADDED Requirements

### Requirement: Secuencia de pasos y paso actual visibles

El sistema DEBE mostrar, en todo momento del onboarding de wallet, la secuencia completa de pasos requeridos y cuál es el paso actual.

#### Scenario: Usuario en cualquier paso del onboarding

- **GIVEN** un usuario con onboarding iniciado y no finalizado
- **WHEN** visualiza cualquier paso del flujo
- **THEN** se muestran todos los pasos requeridos y se identifica el paso actual

### Requirement: Bloqueo de avance ante datos faltantes o inválidos

El sistema DEBE bloquear el avance al siguiente paso cuando falte información obligatoria o haya datos inválidos, y DEBE mostrar un mensaje que indique qué corregir.

#### Scenario: Dato obligatorio faltante

- **GIVEN** un usuario en un paso con un campo obligatorio vacío
- **WHEN** intenta avanzar
- **THEN** el avance se bloquea
- **AND** se muestra un mensaje que identifica el campo y la acción para corregirlo

#### Scenario: Dato inválido

- **GIVEN** un usuario en un paso con un dato que no cumple la validación
- **WHEN** intenta avanzar
- **THEN** el avance se bloquea
- **AND** se muestra un mensaje que indica por qué el dato es inválido y cómo corregirlo

### Requirement: Activación de la wallet al finalizar el onboarding

El sistema DEBE cambiar el estado de la wallet a activo solo cuando el onboarding finaliza correctamente, y DEBE permitir entonces el acceso al punto de entrada de pagos de bajo monto.

#### Scenario: Onboarding finalizado correctamente

- **GIVEN** un usuario que completó todos los pasos requeridos sin errores
- **WHEN** se cierra el flujo de onboarding
- **THEN** el estado de la wallet es activo
- **AND** el usuario puede acceder al punto de entrada de pagos de bajo monto

#### Scenario: Onboarding incompleto

- **GIVEN** un usuario que no completó todos los pasos requeridos
- **WHEN** consulta el estado de su wallet
- **THEN** el estado de la wallet no es activo
- **AND** no puede acceder al punto de entrada de pagos de bajo monto

### Requirement: Registro de eventos de onboarding

El sistema DEBE registrar un evento al iniciar el onboarding, un evento por cada paso finalizado y un evento al cerrar el flujo, cada uno con identificador de usuario y marca de tiempo.

#### Scenario: Onboarding completo

- **GIVEN** un usuario que inicia y completa el onboarding con N pasos requeridos
- **WHEN** se cierra el flujo
- **THEN** existen un evento de inicio, N eventos de paso finalizado y un evento de cierre
- **AND** cada evento contiene identificador de usuario y marca de tiempo

#### Scenario: Onboarding abandonado

- **GIVEN** un usuario que inicia el onboarding y finaliza K pasos, con K menor que N
- **WHEN** consulta el registro de eventos de ese usuario
- **THEN** existen un evento de inicio y K eventos de paso finalizado
- **AND** no existe evento de cierre exitoso

### Requirement: Tiempo mediano de onboarding de la cohorte MVP

El sistema DEBE permitir calcular la duración de cada onboarding a partir de los eventos registrados, de modo que la mediana de la cohorte MVP en Perú baje de 8 minutos a 3 minutos dentro del trimestre posterior al lanzamiento.

#### Scenario: Cálculo de la mediana

- **GIVEN** los eventos de inicio y cierre de los onboardings finalizados de la cohorte MVP en Perú
- **WHEN** se calcula la duración entre inicio y cierre según la frontera de eventos aprobada
- **THEN** se obtiene la mediana de duración de la cohorte
- **AND** la mediana es de 3 minutos o menos al cierre del trimestre posterior al lanzamiento

### Requirement: Salida analítica para MAU y CAC

El sistema DEBE producir una salida analítica de onboarding con el conteo mensual de nuevos usuarios activos y el gasto de adquisición atribuido, suficiente para verificar un MAU entre 1,000 y 2,000 y un CAC de PEN 10 por usuario nuevo en los primeros 3 meses.

#### Scenario: Salida mensual de los meses 1 a 3

- **GIVEN** el período de los meses 1 a 3 posteriores al lanzamiento
- **WHEN** se genera la salida analítica de onboarding
- **THEN** incluye, por mes, el conteo de nuevos usuarios activos y el gasto de adquisición atribuido
- **AND** permite calcular el CAC como gasto de adquisición atribuido dividido entre nuevos usuarios

## Constraints

- No cambiar el orden de etapas del pipeline ni la semántica de `CREWAI_INCLUDE_DATA` en `crew/workflow.py`.
- No cambiar los nombres de los entregables de cada agente (`user_story.md`, `data_spec.md`, `backend_spec.md`, `frontend_spec.md`, `testing_report.md`, `security_report.md`, `chapter_review.md`).
- No cambiar el formato `VEREDICTO: APROBADO` / `VEREDICTO: RECHAZADO` ni su lectura en `publish_pr.verdict()`.
- No cambiar el mapeo de rutas `output/<origen>` → repo del producto de `crew/publish_pr.py`.
- No cambiar el formato de extracción de código (ruta completa del archivo en el bloque) que exigen Backend y Frontend.
- Los contratos nuevos (API de onboarding y estado de wallet, esquema de eventos, salida analítica) se definen en diseño y no modifican los protegidos.
- El alcance excluye pago por contacto o QR, recarga, validación de acceso en transporte, conciliación, definición de KYC y despliegue multipaís.

## Acceptance Evidence

- Prueba o evidencia de UI/API que muestre la secuencia de pasos y el paso actual.
- Prueba con datos faltantes e inválidos que demuestre el bloqueo y el mensaje accionable.
- Prueba que verifique el estado de wallet activo tras un onboarding exitoso y no activo tras uno incompleto.
- Registro de eventos de un onboarding completo y de uno abandonado.
- Consulta o reporte de la mediana de duración de la cohorte MVP en Perú.
- Salida analítica mensual con nuevos usuarios activos y gasto de adquisición atribuido.
- Resultado de `python tools/verify.py` y de los tests existentes sin regresiones.

## Open Questions (pendientes de revisión humana)

- ¿Qué eventos y marcas de tiempo definen oficialmente el inicio y el fin de la duración de onboarding?
- ¿Cuáles son los pasos y datos obligatorios, dado que el KYC está pendiente con cumplimiento y producto?
- ¿Qué significa "usuario activo" para el MAU y de qué fuente proviene el gasto de adquisición para el CAC?
- ¿Se mide la mediana sobre el 100% de la cohorte MVP o sobre una muestra?
- ¿Se confirma el listado de contratos protegidos derivado del repositorio?
