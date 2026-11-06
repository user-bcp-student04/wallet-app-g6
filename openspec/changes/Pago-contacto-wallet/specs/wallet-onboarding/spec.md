# Pago de bajo monto a contacto

## Fuente y alcance

Esta especificación se basa en `docs/epic.md`, `docs/H2_pago_contacto`,
`docs/endpoint_h2`, `docs/alcance.html`, `docs/controles.html` y
`docs/bcp-wallet-mock-openapi.yaml`. También incorpora el requerimiento de
probar los pagos desde el mismo frontend Angular existente. Se excluyó
`docs/H1_registro`.

Define el flujo de pago de bajo monto a un contacto y los resultados que ve el
pagador, incluyendo su prueba desde el frontend Angular existente. No especifica
el onboarding, la recarga, el pago de acceso al transporte ni la integración con
validadores.

## ADDED Requirements

### Requirement: Mostrar el destino y el monto antes de enviar el pago

El sistema DEBE mostrar al pagador la identidad del destinatario y el monto en
PEN antes de confirmar el envío. Los importes enviados al servicio se expresan
como enteros en céntimos.

#### Scenario: Confirmación de un pago

- **GIVEN** un pagador que prepara una transferencia
- **WHEN** revisa el pago antes de confirmarlo
- **THEN** ve el destinatario y el monto que se enviarán
- **AND** el monto se presenta en PEN y corresponde al importe en céntimos de la solicitud

### Requirement: Crear pagos sin duplicar operaciones

El sistema DEBE asociar una clave de idempotencia a cada intento lógico de
pago. Repetir una solicitud con la misma clave y el mismo contenido DEBE
devolver la operación original y su estado actual; reutilizar la clave con
contenido distinto DEBE producir un conflicto, no una operación nueva.

#### Scenario: Repetición de una solicitud idéntica

- **GIVEN** que ya existe un pago creado con una clave de idempotencia
- **WHEN** se repite la solicitud con la misma clave y el mismo contenido
- **THEN** se devuelve el pago original con su estado actual
- **AND** no se reserva ni se descuenta saldo por segunda vez

#### Scenario: Reutilización de clave con contenido diferente

- **GIVEN** que ya existe un pago asociado a una clave de idempotencia
- **WHEN** se envía contenido diferente con esa misma clave
- **THEN** el sistema devuelve `409 IDEMPOTENCY_CONFLICT`
- **AND** no crea un segundo pago

### Requirement: Validar el saldo y los límites antes del envío

El sistema DEBE impedir el envío cuando el saldo disponible sea insuficiente o
el monto supere el límite aplicable al proveedor o canal. El saldo disponible
DEBE considerar los montos reservados por pagos pendientes. La operación
rechazada por estas validaciones NO DEBE enviarse al proveedor.

#### Scenario: Saldo disponible insuficiente

- **GIVEN** que el saldo disponible no cubre el monto solicitado
- **WHEN** el pagador confirma el pago
- **THEN** el sistema informa el rechazo con `409 INSUFFICIENT_FUNDS`
- **AND** no se crea una operación con el proveedor

#### Scenario: Monto por encima del límite aplicable

- **GIVEN** que el monto supera el límite configurado para el proveedor o canal
- **WHEN** el pagador intenta confirmar el pago
- **THEN** el sistema impide el envío e informa que el monto no está permitido

### Requirement: Comunicar el estado real de la confirmación

El sistema DEBE distinguir una operación pendiente de un resultado terminal y
NO DEBE presentar un pago como exitoso o fallido hasta conocer su resultado.
Cuando el pago sea exitoso, fallido o expirado, el pagador DEBE recibir un
único resultado terminal para ese intento. La confirmación de estados
asíncronos DEBE reflejar el resultado final del proveedor.

#### Scenario: Pago aprobado y confirmado

- **GIVEN** que el proveedor aprueba el pago
- **AND** la aplicación recibe el evento de confirmación correspondiente
- **WHEN** se consulta el estado del pago
- **THEN** el estado local pasa a `SUCCEEDED`
- **AND** el pagador recibe una confirmación de éxito

#### Scenario: Pago rechazado y confirmado

- **GIVEN** que el proveedor rechaza el pago
- **AND** la aplicación recibe el evento de confirmación correspondiente
- **WHEN** se consulta el estado del pago
- **THEN** el estado local pasa a `REJECTED`
- **AND** el pagador recibe una confirmación de fallo
- **AND** se libera la reserva sin cobrar el monto

#### Scenario: Aprobación demorada

- **GIVEN** que el pago permanece `PENDING`
- **WHEN** todavía no se ha completado el proveedor o entregado su evento
- **THEN** la interfaz informa que la confirmación sigue en proceso
- **AND** no presenta un resultado terminal

#### Scenario: Pago expirado

- **GIVEN** que el servicio o proveedor comunica un resultado terminal de expiración
- **WHEN** la aplicación recibe ese resultado
- **THEN** el pagador recibe el resultado de expiración como estado terminal del intento
- **AND** no se crea un cobro duplicado

### Requirement: Recuperar el resultado ante errores o demoras

El sistema DEBE proporcionar una siguiente acción clara ante un error. Si una
respuesta de timeout incluye un identificador de pago, el pagador DEBE poder
consultar el estado de esa operación antes de iniciar otro intento. Un error de
proveedor que no creó una operación DEBE poder reintentarse sin presentar un
cobro como realizado.

#### Scenario: Timeout después de procesar el pago

- **GIVEN** que la solicitud termina en `504` e incluye `paymentId`
- **WHEN** el pagador solicita conocer el resultado
- **THEN** la aplicación consulta la operación identificada antes de iniciar otro pago
- **AND** comunica el estado real sin crear un segundo cobro

#### Scenario: Proveedor no disponible antes de crear la operación

- **GIVEN** que el proveedor no está disponible y no se creó operación ni reserva
- **WHEN** la aplicación recibe `503 PROVIDER_ERROR`
- **THEN** informa que el pago no se procesó
- **AND** ofrece una acción clara para reintentar o volver

### Requirement: Consultar el historial y el comprobante del pago

El sistema DEBE permitir consultar el estado de un pago y el historial de la
wallet. Cuando un pago termine en `SUCCEEDED`, DEBE estar disponible su
comprobante y el pago DEBE figurar en el historial.

#### Scenario: Consulta de pago exitoso

- **GIVEN** un pago en estado `SUCCEEDED`
- **WHEN** el pagador consulta el pago, su historial y su comprobante
- **THEN** puede identificar el pago en el historial de la wallet
- **AND** obtiene el comprobante con el importe, la moneda, el destinatario y el estado

#### Scenario: Comprobante aún no disponible

- **GIVEN** un pago en estado `PENDING` o `REJECTED`
- **WHEN** el pagador solicita el comprobante
- **THEN** el servicio responde `409 RECEIPT_NOT_READY`
- **AND** la interfaz no muestra un comprobante como si el pago hubiera sido exitoso

### Requirement: Probar el flujo de pago desde el frontend Angular existente

El frontend Angular existente DEBE permitir ejecutar y observar los escenarios
de pago a contacto de esta especificación, sin requerir un frontend separado.
Debe usar la configuración de servicio ya disponible en ese frontend y mostrar
el resultado devuelto por el mock para cada operación de prueba.

#### Scenario: Probar un pago exitoso desde el frontend existente

- **GIVEN** el usuario está en el frontend Angular existente y tiene configurado el mock
- **WHEN** ejecuta el flujo de pago a contacto
- **THEN** puede enviar el pago y consultar su estado desde ese mismo frontend
- **AND** puede consultar el historial y el comprobante cuando el pago termina en `SUCCEEDED`

#### Scenario: Observar estados y errores del mock

- **GIVEN** el usuario ejecuta desde el frontend un escenario pendiente, rechazado o con error
- **WHEN** el mock responde a las operaciones del pago
- **THEN** el frontend muestra el estado o error recibido y una siguiente acción coherente
- **AND** no representa un pago pendiente o fallido como exitoso

#### Scenario: Preparar escenarios de prueba

- **GIVEN** el usuario necesita probar una transición asíncrona documentada
- **WHEN** prepara y confirma el escenario en el frontend de prueba
- **THEN** las operaciones de control se usan únicamente para preparar pruebas
- **AND** no se presentan al usuario final como operaciones de negocio

### Requirement: Medir el resultado del flujo de pago

La aplicación DEBE instrumentar el funnel de checkout y registrar el evento de
activación del pagador para los pagos exitosos, de modo que se pueda evaluar la
caída en checkout y calcular el MAU de la cohorte MVP en Perú durante los meses
1 a 3 posteriores al lanzamiento.

#### Scenario: Seguimiento del objetivo de checkout

- **GIVEN** la cohorte MVP en Perú durante el trimestre posterior al lanzamiento
- **WHEN** se genera el reporte del funnel de checkout
- **THEN** el reporte permite calcular la caída entre el inicio y la finalización del flujo
- **AND** permite verificar el objetivo de reducir la caída del 30% al 8%

#### Scenario: Activación de un pagador

- **GIVEN** un pago exitoso de un usuario de la cohorte MVP
- **WHEN** se registra la activación del pagador
- **THEN** el evento puede utilizarse para el cálculo mensual de MAU de los meses 1 a 3
- **AND** el reporte permite contrastar el objetivo de 1,000 a 2,000 MAU

## Contratos y restricciones protegidos

- El contrato de pago del mock comprende `POST /payments`,
  `GET /payments?walletId=...`, `GET /payments/{id}`,
  `GET /payments/{id}/receipt` y `GET /provider/payments/{id}`.
- Los pagos se expresan en céntimos de PEN; el mock admite únicamente PEN.
  Los escenarios de proveedor documentados son `APPROVED`, `REJECTED`,
  `PENDING`, `DELAYED_APPROVAL`, `TIMEOUT_AFTER_PROCESSING` y `PROVIDER_ERROR`.
- La confirmación asíncrona se realiza mediante `POST /callbacks/payments`.
  Los endpoints `/control/*` preparan escenarios de prueba y no son APIs de
  negocio para usuarios finales.
- Las llamadas HTTP del frontend Angular deben seguir las prácticas de
  `docs/GOOD_PRACTICES.md`: tipado estricto, interfaces para requests y
  responses, y llamadas HTTP desde servicios en lugar de componentes.
- El mock mantiene datos en memoria, no mueve dinero real y no garantiza que
  los datos sobrevivan un reinicio o despliegue. Su historial no tiene filtros
  por fecha ni paginación.
- El mock no implementa una recarga. La recarga sin paso adicional de
  activación pertenece al alcance de la épica, pero no a esta especificación.
- La interfaz debe mostrar mensajes de error comprensibles sin exponer detalles
  internos del backend, conforme a `docs/GOOD_PRACTICES.md`.

## Supuestos y preguntas abiertas

- El mock no define un estado `EXPIRED` para pagos ni vencimiento automático.
  Debe confirmarse qué servicio comunica la expiración y cómo se representa en
  el contrato antes de verificar ese escenario de extremo a extremo.
- La regla inicial de monto bajo y los límites por proveedor o canal están por
  definir. No hay un umbral numérico en la documentación fuente.
- Las etiquetas de los estados terminales que verá el usuario y el tiempo
  máximo aceptable de confirmación deben acordarse con producto y cada operador.
- El mock no registra eventos de checkout ni calcula MAU, CAC o atribución; el
  esquema y la salida analítica de la aplicación quedan por definir.
