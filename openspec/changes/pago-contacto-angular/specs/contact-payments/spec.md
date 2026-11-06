# Spec Delta

## Purpose

Permite iniciar y consultar pagos de bajo monto a contactos con confirmación confiable, y probar el flujo desde el frontend Angular existente.

## ADDED Requirements

### Requirement: Mostrar el destino y el monto antes del envío

El frontend MUST mostrar la identidad del destinatario y el importe en PEN antes de confirmar el pago, usando céntimos enteros en la solicitud.

#### Scenario: Revisión antes de confirmar

- **GIVEN** el pagador prepara una transferencia a un contacto
- **WHEN** revisa la operación antes de enviarla
- **THEN** ve la identidad del destinatario y el importe en PEN
- **AND** el importe enviado corresponde a los céntimos mostrados

### Requirement: Crear pagos con idempotencia

El frontend MUST enviar una clave de idempotencia por intento lógico y conservarla al repetir la misma solicitud.

#### Scenario: Repetición idéntica

- **GIVEN** ya existe un pago con una clave y un contenido determinados
- **WHEN** se repite la solicitud con la misma clave y el mismo contenido
- **THEN** el servicio devuelve la operación original y su estado actual
- **AND** no se crea un cobro duplicado

#### Scenario: Contenido distinto para la misma clave

- **GIVEN** una clave de idempotencia ya asociada a un pago
- **WHEN** se reutiliza con contenido distinto
- **THEN** el servicio devuelve `409 IDEMPOTENCY_CONFLICT`
- **AND** no crea otra operación

### Requirement: Permitir pagos solo desde una wallet activa

El sistema MUST impedir la creación de pagos desde una wallet que no esté activa y comunicar el error estable del contrato.

#### Scenario: Wallet no activa

- **GIVEN** la wallet está `PENDING` o `REJECTED`
- **WHEN** se intenta crear un pago con esa wallet
- **THEN** el servicio devuelve `409 WALLET_NOT_ACTIVE`
- **AND** el frontend informa que no se puede continuar

### Requirement: Validar el saldo y los límites antes del envío

El sistema MUST validar el saldo disponible, incluidas las reservas de pagos pendientes, y el límite configurado para el proveedor o canal antes de enviar el pago.

#### Scenario: Saldo insuficiente

- **GIVEN** el saldo disponible no cubre el importe
- **WHEN** el pagador intenta confirmar
- **THEN** la operación se rechaza con `409 INSUFFICIENT_FUNDS`
- **AND** no se crea una operación con el proveedor

#### Scenario: Importe superior al límite

- **GIVEN** el importe supera el límite configurado para el proveedor o canal
- **WHEN** el pagador intenta confirmar
- **THEN** el sistema impide el envío e informa que el importe no está permitido

### Requirement: Mostrar estados de pago según la confirmación

El frontend MUST distinguir `PENDING` de los resultados terminales y mostrar el resultado confirmado por el proveedor sin inferir éxito o fallo a partir de una demora.

#### Scenario: Pago pendiente

- **GIVEN** el pago se encuentra en `PENDING`
- **WHEN** aún no se ha recibido su confirmación
- **THEN** el pagador ve que el resultado sigue en proceso
- **AND** la interfaz no lo presenta como terminal

#### Scenario: Pago aprobado y confirmado

- **GIVEN** el proveedor aprueba el pago
- **WHEN** la aplicación procesa la confirmación correspondiente
- **THEN** el estado local queda en `SUCCEEDED`
- **AND** el pagador recibe una confirmación de éxito

#### Scenario: Pago rechazado y confirmado

- **GIVEN** el proveedor rechaza el pago
- **WHEN** la aplicación procesa la confirmación correspondiente
- **THEN** el estado local queda en `REJECTED`
- **AND** el pagador recibe una confirmación de fallo y se libera la reserva

#### Scenario: Resultado terminal de expiración comunicado

- **GIVEN** un servicio o proveedor comunica explícitamente un resultado terminal de expiración
- **WHEN** la aplicación recibe ese resultado
- **THEN** el pagador ve la expiración como resultado del intento
- **AND** la aplicación no crea un cobro duplicado

### Requirement: Recuperar el resultado ante timeout o indisponibilidad

El sistema MUST ofrecer una acción coherente ante un error y consultar una operación identificada antes de iniciar otro intento cuando el timeout indique que pudo procesarse.

#### Scenario: Timeout con identificador de pago

- **GIVEN** una respuesta `504` contiene `paymentId`
- **WHEN** el pagador solicita el resultado
- **THEN** la aplicación consulta o resuelve esa operación antes de permitir otro intento
- **AND** comunica el estado real sin duplicar el cobro

#### Scenario: Error del proveedor antes de crear la operación

- **GIVEN** el proveedor no está disponible y no se creó operación ni reserva
- **WHEN** la aplicación recibe `503 PROVIDER_ERROR`
- **THEN** informa que el pago no se procesó
- **AND** ofrece una acción clara para reintentar o volver

### Requirement: Consultar el historial y el comprobante

El sistema MUST permitir consultar el estado y el historial de la wallet y solo mostrar el comprobante cuando el contrato indique que está disponible.

#### Scenario: Pago exitoso en historial

- **GIVEN** un pago termina en `SUCCEEDED`
- **WHEN** el pagador consulta el historial y el comprobante
- **THEN** el pago aparece en el historial de la wallet
- **AND** el comprobante muestra importe, moneda, destinatario y estado

#### Scenario: Comprobante no disponible

- **GIVEN** un pago está `PENDING` o `REJECTED`
- **WHEN** se solicita el comprobante
- **THEN** el servicio devuelve `409 RECEIPT_NOT_READY`
- **AND** la interfaz no presenta un comprobante exitoso

### Requirement: Probar el flujo desde el frontend Angular existente

El frontend Angular existente MUST permitir ejecutar y observar el flujo de pago a contacto usando su configuración actual, sin requerir una aplicación frontend separada.

#### Scenario: Prueba de pago exitoso desde el frontend

- **GIVEN** el mock está configurado en el frontend Angular existente
- **WHEN** se ejecuta un pago aprobado a contacto
- **THEN** desde el mismo frontend se puede consultar el estado, el historial y el comprobante disponible

#### Scenario: Prueba de estados y errores

- **GIVEN** se ejecuta desde el frontend un escenario pendiente, rechazado o con error
- **WHEN** el mock responde
- **THEN** el frontend muestra el estado o error recibido y una siguiente acción coherente
- **AND** los endpoints `/control/*` solo se usan para preparar escenarios de prueba

### Requirement: Cubrir los endpoints utilizados por el flujo

La entrega MUST incluir una verificación reproducible por cada endpoint de negocio utilizado por el flujo, con un caso exitoso y un error relevante cuando el contrato lo defina.

#### Scenario: Reporte de cobertura por endpoint

- **GIVEN** se ejecuta la suite de pruebas del cambio
- **WHEN** se revisa el reporte de pruebas
- **THEN** cada endpoint de negocio utilizado tiene al menos un caso exitoso
- **AND** cada endpoint con respuestas de error definidas tiene al menos un caso de error relevante
- **AND** los resultados no ejecutados están identificados como `NO EJECUTADO`

### Requirement: Medir el funnel y la activación del pagador

La aplicación MUST registrar el funnel de checkout y la activación asociada a pagos exitosos para permitir evaluar la cohorte MVP en Perú.

#### Scenario: Medición del checkout

- **GIVEN** el período del trimestre posterior al lanzamiento
- **WHEN** se genera el reporte del funnel de checkout
- **THEN** permite calcular la caída entre inicio y finalización y contrastarla con el objetivo de 30% a 8%

#### Scenario: Activación mensual

- **GIVEN** un pago exitoso de un usuario de la cohorte MVP
- **WHEN** se registra la activación del pagador
- **THEN** el evento puede utilizarse para el cálculo mensual de MAU de los meses 1 a 3
- **AND** el reporte permite contrastar el objetivo de 1,000 a 2,000 MAU
