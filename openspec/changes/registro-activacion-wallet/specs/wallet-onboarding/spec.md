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

#### Scenario: Documento fuera del formato permitido

- **GIVEN** un usuario que ingresa un tipo de documento distinto de `TEST` o un documento sin el prefijo `TEST-`
- **WHEN** intenta avanzar
- **THEN** el avance se bloquea
- **AND** se muestra un mensaje que indica que solo se admiten documentos ficticios con prefijo `TEST-`

### Requirement: Verificación de identidad simulada (KYC)

El sistema DEBE crear la verificación y la wallet mediante `POST /kyc/verifications` con `documentType` `TEST`, `document` con prefijo `TEST-` y `scenario` opcional (predeterminado `APPROVED`), y DEBE conservar los identificadores de verificación (`id`) y de wallet (`wallet_id`) devueltos para consultas posteriores con `GET /kyc/verifications/{id}` y `GET /wallets/{id}`. La verificación es simulada: no valida documentos reales ni evita registros repetidos.

#### Scenario: Verificación aprobada

- **GIVEN** un usuario que envía un documento `TEST-` válido con escenario `APPROVED`
- **WHEN** la API responde `201`
- **THEN** la verificación y la wallet tienen estado `ACTIVE`
- **AND** la wallet tiene saldo cero

#### Scenario: Verificación rechazada

- **GIVEN** un usuario cuya verificación se resuelve con escenario `REJECTED`
- **WHEN** la API responde `201`
- **THEN** la wallet tiene estado `REJECTED`
- **AND** la interfaz informa que la cuenta fue rechazada

#### Scenario: Verificación en revisión manual

- **GIVEN** un usuario cuya verificación se resuelve con escenario `MANUAL_REVIEW`
- **WHEN** la API responde `201`
- **THEN** la wallet tiene estado `PENDING` y se abre un caso de soporte `KYC_REVIEW` consultable en `GET /support/cases`
- **AND** la interfaz explica que falta una decisión

#### Scenario: Decisión sobre una verificación pendiente

- **GIVEN** una verificación en estado `PENDING`
- **WHEN** se envía `POST /kyc/verifications/{id}/decision` con `ACTIVE` o `REJECTED`
- **THEN** la wallet adopta el estado decidido y el caso de soporte se resuelve
- **AND** repetir la misma decisión conserva el resultado, y cambiar una decisión final devuelve `409 DECISION_CONFLICT`

#### Scenario: Proveedor KYC no disponible

- **GIVEN** un usuario cuya verificación se resuelve con escenario `UNAVAILABLE`
- **WHEN** la API responde `503 KYC_UNAVAILABLE`
- **THEN** no se crea ninguna wallet
- **AND** se muestra un mensaje de indisponibilidad del servicio que permite reintentar

#### Scenario: Wallet nueva sin fondos

- **GIVEN** una wallet creada por el onboarding con estado `ACTIVE`
- **WHEN** se consulta `GET /wallets/{id}`
- **THEN** `balance`, `reserved` y `available` valen 0 y `currency` es `PEN`
- **AND** la interfaz no ofrece recarga, porque el mock no la provee; las pruebas de pago con fondos usan `wallet-demo`

### Requirement: Activación de la wallet al finalizar el onboarding

El sistema DEBE cambiar el estado de la wallet a activo (`ACTIVE`) solo cuando el onboarding finaliza correctamente, y DEBE permitir entonces el acceso al punto de entrada de pagos de bajo monto. Una wallet `PENDING` o `REJECTED` NO DEBE permitir pagos: el pago con ella devuelve `409 WALLET_NOT_ACTIVE`.

#### Scenario: Onboarding finalizado correctamente

- **GIVEN** un usuario que completó todos los pasos requeridos sin errores y cuya verificación quedó `ACTIVE`
- **WHEN** se cierra el flujo de onboarding
- **THEN** el estado de la wallet es `ACTIVE`
- **AND** el usuario puede acceder al punto de entrada de pagos de bajo monto

#### Scenario: Onboarding incompleto

- **GIVEN** un usuario que no completó todos los pasos requeridos, o cuya wallet está `PENDING` o `REJECTED`
- **WHEN** consulta el estado de su wallet con `GET /wallets/{id}`
- **THEN** el estado de la wallet no es `ACTIVE`
- **AND** no puede acceder al punto de entrada de pagos de bajo monto

#### Scenario: Wallet inexistente

- **GIVEN** un identificador de wallet que no existe en el grupo
- **WHEN** se consulta `GET /wallets/{id}`
- **THEN** la API responde `404 NOT_FOUND`
- **AND** la interfaz no muestra un estado de wallet

### Requirement: Registro de eventos de onboarding

La aplicación DEBE registrar un evento al iniciar el onboarding, un evento por cada paso finalizado y un evento al cerrar el flujo, cada uno con identificador de usuario y marca de tiempo. El mock no registra estos eventos ni calcula duración, MAU, CAC ni atribución de adquisición.

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

### Requirement: Registro de cliente con OTP previo al inicio de sesión

El sistema DEBE mostrar, antes del inicio de sesión, una vista de registro de cliente con el tipo de documento `DNI` y un número de documento de solo dígitos y como máximo 8. Al completar el registro DEBE indicar que se ha enviado un OTP de aprobación (dato dummy `0000`) y, al validarlo, DEBE dar acceso al panel de saldo, movimientos y transferencias.

#### Scenario: Validación del número de documento

- **GIVEN** un usuario en el formulario de registro con el tipo de documento `DNI`
- **WHEN** deja el número vacío, ingresa caracteres que no son dígitos o ingresa más de 8 dígitos
- **THEN** el registro se bloquea
- **AND** se muestra un mensaje que indica qué corregir

#### Scenario: Registro válido y OTP enviado

- **GIVEN** un usuario que ingresa un número de documento válido de hasta 8 dígitos
- **WHEN** completa el registro
- **THEN** se muestra que se ha enviado un OTP de aprobación y se pide ingresarlo
- **AND** el OTP dummy de la demo es `0000`

#### Scenario: OTP incorrecto

- **GIVEN** un usuario en la validación del OTP
- **WHEN** ingresa un valor distinto de `0000`
- **THEN** no se da acceso
- **AND** se muestra un mensaje que indica que el OTP no es correcto

#### Scenario: OTP correcto

- **GIVEN** un usuario en la validación del OTP
- **WHEN** ingresa `0000`
- **THEN** se abre la sesión del cliente
- **AND** se muestra el panel de saldo, movimientos y transferencias, sin acceso a la consola de pruebas

### Requirement: Inicio de sesión con DNI y contraseña

El sistema DEBE ofrecer un inicio de sesión responsive con DNI y contraseña. El cliente existente de la demo es el usuario dummy `admin` con contraseña `admin`. Si el DNI no corresponde a un cliente existente, DEBE mostrar el mensaje "Ups, registrate como nuevo usuario".

#### Scenario: Acceso del usuario dummy

- **GIVEN** un usuario en el inicio de sesión
- **WHEN** ingresa `admin` y `admin`
- **THEN** se muestra el panel de saldo, movimientos y transferencias
- **AND** se habilita la consola de pruebas, solo para este usuario

#### Scenario: Cliente inexistente

- **GIVEN** un usuario en el inicio de sesión
- **WHEN** ingresa un DNI distinto de `admin`
- **THEN** no se da acceso
- **AND** se muestra "Ups, registrate como nuevo usuario" con acceso al registro

#### Scenario: Datos faltantes o contraseña incorrecta

- **GIVEN** un usuario en el inicio de sesión
- **WHEN** deja un campo vacío o ingresa `admin` con una contraseña incorrecta
- **THEN** no se da acceso
- **AND** se muestra un mensaje que indica qué corregir

### Requirement: Panel de saldo, movimientos y transferencias

Después de acceder, el sistema DEBE mostrar el saldo de la cuenta (`GET /wallets/{id}` de `wallet-demo`), los últimos movimientos (`GET /payments?walletId=`) y las opciones de transferencia "Pago a contacto" y "Pago con QR".

#### Scenario: Saldo y movimientos

- **GIVEN** un cliente con sesión
- **WHEN** abre el panel
- **THEN** ve el saldo disponible, el contable y el reservado en soles
- **AND** ve hasta 5 movimientos, el más reciente primero, con destinatario, estado e importe

#### Scenario: Panel sin movimientos o con error de carga

- **GIVEN** un cliente con sesión
- **WHEN** no hay movimientos o falla la carga
- **THEN** se muestra un estado vacío o un mensaje accionable con la opción de reintentar

### Requirement: Transferencia a contacto y con QR

El sistema DEBE permitir transferir por contacto (`POST /payments` a `contact-demo`) y con QR (`POST /qrs/resolve` y `POST /payments` a `merchant-demo` con `qrId`) mediante un flujo de método, datos, confirmación, código de validación y resultado. Cada pago DEBE enviar `Idempotency-Key` y, si queda `PENDING`, confirmarse con `POST /payments/{id}/resolve`.

#### Scenario: Transferencia exitosa a contacto

- **GIVEN** un cliente que elige "Pago a contacto" e ingresa un monto válido menor o igual a su saldo disponible
- **WHEN** confirma, ingresa el código de validación mostrado y aprueba
- **THEN** se muestra el resultado exitoso con destinatario, monto y operación
- **AND** al cerrar se actualizan el saldo y los movimientos

#### Scenario: Transferencia con QR

- **GIVEN** un cliente que elige "Pago con QR" e ingresa o genera un texto `qrmock:ID`
- **WHEN** valida el QR, completa el monto si es abierto y aprueba con el código de validación
- **THEN** el pago incluye el `qrId` y se muestra el resultado
- **AND** exige validar el QR antes de continuar

#### Scenario: Bloqueos y errores de la transferencia

- **GIVEN** un cliente en el flujo de transferencia
- **WHEN** ingresa un monto inválido o mayor al saldo, un código de validación incorrecto, rechaza en la confirmación, o el mock responde `409 INSUFFICIENT_FUNDS`, `410 QR_EXPIRED` u otro error
- **THEN** no se crea el pago (o se informa el error con la acción sugerida) y puede reintentar o cancelar

### Requirement: Consola Angular básica para probar los servicios de onboarding

El sistema DEBE incluir un front básico en Angular (en `web/`) que permita ejecutar y observar cada servicio del mock usado por esta historia. Es la "Consola de pruebas", visible solo para el usuario `admin` tras iniciar sesión. Los servicios cubiertos son `GET /health`, `GET /scenarios`, `POST /kyc/verifications`, `GET /kyc/verifications/{id}`, `POST /kyc/verifications/{id}/decision`, `GET /wallets/{id}`, `GET /support/cases` y `POST /control/reset`. La consola DEBE tener tres zonas: configuración, flujo de onboarding guiado y consola de servicios.

#### Scenario: Configuración de la URL base y la latencia

- **GIVEN** un usuario que abre la consola
- **WHEN** define la URL base del grupo (predeterminada en `environment.ts`, la URL del grupo en cloud; p. ej. `http://127.0.0.1:8787` en local) y, opcionalmente, una latencia de 0 a 5000 ms
- **THEN** todas las llamadas usan esa URL base y envían la latencia en `X-Mock-Latency-Ms` cuando es mayor que 0 (el mock en nube no permite ese header en el preflight CORS)
- **AND** un valor de latencia fuera de rango se bloquea en el cliente con un mensaje, sin llamar a la API

#### Scenario: Comprobar disponibilidad y escenarios

- **GIVEN** la consola abierta
- **WHEN** el usuario ejecuta `GET /health` y `GET /scenarios`
- **THEN** se muestra el estado del servicio y las opciones exactas de `scenario` para KYC
- **AND** el selector de escenario del formulario KYC se alimenta de esa lista

#### Scenario: Flujo de onboarding guiado

- **GIVEN** un usuario con la consola configurada
- **WHEN** recorre el flujo: datos de documento, elección de escenario, envío de la verificación y resultado
- **THEN** el indicador de pasos muestra la secuencia completa y el paso actual
- **AND** el resultado muestra `id`, `wallet_id`, `scenario` y `status`, y la consulta posterior de `GET /wallets/{id}`

#### Scenario: Ejecutar cada servicio de forma individual

- **GIVEN** la consola de servicios
- **WHEN** el usuario completa los campos de un servicio (cuerpo o parámetro `id`) y lo ejecuta
- **THEN** se muestran el método, la ruta, el cuerpo enviado, el código HTTP, el cuerpo de respuesta y el tiempo de respuesta
- **AND** los identificadores `id` y `wallet_id` de la última verificación creada se reutilizan como valores sugeridos

#### Scenario: Resolver una revisión manual desde la consola

- **GIVEN** una verificación en `PENDING` con caso de soporte abierto
- **WHEN** el usuario lista `GET /support/cases` y envía la decisión `ACTIVE` o `REJECTED`
- **THEN** la consola muestra la wallet con el nuevo estado y el caso de soporte `RESOLVED`
- **AND** al intentar cambiar una decisión final se muestra el `409 DECISION_CONFLICT`

#### Scenario: Errores de la API

- **GIVEN** una llamada que devuelve `400`, `404`, `409`, `413`, `429` o `503`
- **WHEN** la consola recibe la respuesta
- **THEN** muestra un mensaje legible con el código de error estable (`error`) y la acción sugerida
- **AND** ante `429 GROUP_LIMIT_RESET_REQUIRED` indica que debe reiniciarse el grupo

#### Scenario: Reinicio de datos del grupo

- **GIVEN** la consola de servicios
- **WHEN** el usuario ejecuta `POST /control/reset` tras confirmar la acción
- **THEN** se informa que se borraron todos los datos del grupo y se repuso `wallet-demo`
- **AND** se limpian los identificadores y el registro de eventos locales de la consola

#### Scenario: Eventos de onboarding visibles en la consola

- **GIVEN** un onboarding ejecutado desde la consola
- **WHEN** el usuario abre el panel de eventos
- **THEN** ve los eventos de inicio, paso finalizado y cierre con identificador de usuario y marca de tiempo
- **AND** ve la duración del onboarding calculada desde esos eventos

#### Scenario: Acceso al punto de entrada de pagos

- **GIVEN** la consola con una wallet cargada
- **WHEN** el estado de la wallet es `ACTIVE`
- **THEN** el acceso al punto de entrada de pagos de bajo monto queda habilitado
- **AND** con estado `PENDING` o `REJECTED` queda deshabilitado con un mensaje que explica el motivo

## Constraints

- No cambiar el orden de etapas del pipeline ni la semántica de `CREWAI_INCLUDE_DATA` en `crew/workflow.py`.
- No cambiar los nombres de los entregables de cada agente (`user_story.md`, `data_spec.md`, `backend_spec.md`, `frontend_spec.md`, `testing_report.md`, `security_report.md`, `chapter_review.md`).
- No cambiar el formato `VEREDICTO: APROBADO` / `VEREDICTO: RECHAZADO` ni su lectura en `publish_pr.verdict()`.
- No cambiar el mapeo de rutas `output/<origen>` → repo del producto de `crew/publish_pr.py`.
- No cambiar el formato de extracción de código (ruta completa del archivo en el bloque) que exigen Backend y Frontend.
- Los contratos nuevos (API de onboarding y estado de wallet, esquema de eventos, salida analítica) se definen en diseño y no modifican los protegidos.
- El contrato W1 del mock (`docs/bcp-wallet-mock-openapi.yaml`, `docs/H1_registro`) es la fuente para KYC y wallet: `POST /kyc/verifications`, `GET /kyc/verifications/{id}`, `POST /kyc/verifications/{id}/decision` y `GET /wallets/{id}`; importes en céntimos PEN; cuerpos de hasta 65536 bytes (`413` si se excede); `429 GROUP_LIMIT_RESET_REQUIRED` solo en cloud.
- Solo se usan documentos ficticios (`documentType` `TEST`, `document` con prefijo `TEST-`); no se envían documentos reales.
- El mock no registra eventos de onboarding ni métricas, y no calcula duración, MAU, CAC ni atribución: la secuencia de pantallas y la instrumentación de inicio, pasos y fin las implementa la aplicación y sus contratos los define el diseño.
- Datos del mock: en memoria, sin autenticación, límite de 2000 recursos por grupo y posible pérdida por inactividad o despliegue; `POST /control/reset` borra el grupo y repone `wallet-demo` (S/ 1000.00 = 100000 céntimos), `contact-demo` y `merchant-demo`. Los `/control/*` son solo para preparar escenarios.
- Los casos de soporte se cierran únicamente mediante la decisión KYC; no hay endpoint para editarlos.
- Front Angular (`web/`) conforme a `docs/GOOD_PRACTICES.md`: tipado estricto sin `any`, interfaces para cada request y response, llamadas HTTP solo en servicios (no en componentes), URL base en `environment.ts`, sesión centralizada en un único servicio, sin `[innerHTML]` con datos dinámicos y mensajes de error que no exponen detalles internos.
- La consola es una herramienta de prueba y demostración: no valida documentos reales ni sustituye la analítica de producción.
- Credenciales, OTP y código de validación son dummy y se comprueban en el cliente (`admin`/`admin`, OTP `0000`): no constituyen autenticación real y no deben usarse fuera de la demo.
- Los pagos y QR usan el contrato W2/W3 del mock (`POST /payments` con `Idempotency-Key`, `POST /payments/{id}/resolve`, `GET /payments`, `POST /qrs`, `POST /qrs/resolve`) sobre `wallet-demo`, `contact-demo` y `merchant-demo`; los movimientos no traen fecha.
- El alcance excluye recarga, validación de acceso en transporte, conciliación, reversos, reglas de KYC reales (se usa solo el KYC simulado) y despliegue multipaís.

## Acceptance Evidence

- Prueba o evidencia de UI/API que muestre la secuencia de pasos y el paso actual.
- Prueba con datos faltantes e inválidos (incluido documento sin prefijo `TEST-`) que demuestre el bloqueo y el mensaje accionable.
- Prueba de los escenarios KYC `APPROVED`, `REJECTED`, `MANUAL_REVIEW` (con decisión `ACTIVE`/`REJECTED`) y `UNAVAILABLE` contra el mock.
- Prueba que verifique el estado de wallet `ACTIVE` tras un onboarding exitoso y no activo tras uno incompleto, `PENDING` o `REJECTED`.
- Registro de eventos de un onboarding completo y de uno abandonado.
- Consola Angular que ejecuta cada servicio cubierto contra el mock y muestra método, ruta, código HTTP, respuesta y tiempo; captura o prueba de componentes y servicios Angular (tests del front) con los mensajes de error `400`, `404`, `409`, `413`, `429` y `503`.
- Ejecución desde la consola de `POST /control/reset` y de un onboarding por cada escenario KYC.
- Consulta o reporte de la mediana de duración de la cohorte MVP en Perú.
- Salida analítica mensual con nuevos usuarios activos y gasto de adquisición atribuido.
- Resultado de `python tools/verify.py` y de los tests existentes sin regresiones.
- Pruebas del registro (DNI de hasta 8 dígitos, OTP `0000` correcto e incorrecto), del inicio de sesión (`admin`/`admin`, cliente inexistente con "Ups, registrate como nuevo usuario") y del panel de saldo, movimientos y transferencias (contacto y QR, caminos felices y de error).
- Validación manual en el navegador contra el mock del grupo: registro con OTP, acceso al panel, pago a contacto y pago con QR que actualizan saldo y movimientos.

## Open Questions (pendientes de revisión humana)

- ¿Qué eventos y marcas de tiempo definen oficialmente el inicio y el fin de la duración de onboarding?
- ¿Cuáles son los pasos y datos obligatorios adicionales al KYC simulado (`documentType`, `document`), dado que las reglas de KYC reales están pendientes con cumplimiento y producto?
- ¿Cómo gestiona la interfaz el tiempo de espera de una wallet `PENDING` hasta la decisión humana y cuenta ese tiempo en la duración del onboarding?
- ¿Dónde se persisten los eventos de onboarding (backend propio o almacenamiento local de la consola) y cuál es la URL base del grupo en cloud frente a la local?
- ¿El mock permite llamadas desde el navegador (CORS) o la consola necesita un proxy de desarrollo?
- ¿Qué significa "usuario activo" para el MAU y de qué fuente proviene el gasto de adquisición para el CAC?
- ¿Se mide la mediana sobre el 100% de la cohorte MVP o sobre una muestra?
- ¿Se confirma el listado de contratos protegidos derivado del repositorio?
- ¿Los clientes registrados con DNI y OTP deben poder iniciar sesión más adelante (el registro no pide contraseña) y tener su propia wallet en lugar de `wallet-demo`?
- ¿El DNI debe tener exactamente 8 dígitos o basta con "máximo 8"?
