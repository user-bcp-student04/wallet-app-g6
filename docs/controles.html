# Controles del mock

Estas operaciones preparan escenarios para W1–W6. Todos los integrantes comparten el estado de su grupo.

### `GET /control/events`

Lista eventos de todos los pagos del grupo, incluidos los entregados. Filtra en tu cliente por payment_id y target, y usa id como eventId. No hay envío automático de webhooks.

Respuestas HTTP: `200`.

Respuesta: lista de objetos con `id`, `payment_id`, `target`, `delivered`. Una lista vacía se representa como `[]`.

### `POST /control/events/{id}/deliver`

Entrega el evento por ID evt de la ruta. Equivale a POST /callbacks/payments con eventId. No requiere cuerpo. Repetir es seguro; 404 si no existe; 409 si la transición es incompatible.

Respuestas HTTP: `200`, `404`, `409`, `400`, `413`, `429`.

Campos de respuesta: `duplicate`, `payment`.

### `POST /control/provider/{id}/complete`

Finaliza un proveedor PENDING usando el ID pay del pago. status puede ser SUCCEEDED, valor predeterminado, o REJECTED. Devuelve eventId para entregar después. No confirma la wallet automáticamente. Si ya terminó: 409 PROVIDER_ALREADY_FINAL; estado inválido: 400 INVALID_STATUS; ID inexistente: 404.

Campos del cuerpo JSON:

- `status`: string, opcional. Resultado del proveedor. Predeterminado SUCCEEDED. Valores: SUCCEEDED, REJECTED.

Respuestas HTTP: `200`, `400`, `404`, `409`, `413`, `429`.

Campos de respuesta: `eventId`.

### `POST /control/settlements`

Configura una sola alteración por paymentId, reemplazando la anterior. AMOUNT exige amountCents; MISSING omite fila; DUPLICATE duplica fila; los tres exigen pago existente. ORPHAN exige ID nuevo y amountCents, o 409 PROVIDER_ALREADY_EXISTS. CLEAR elimina la alteración aunque no exista. Modo inválido: 400 INVALID_MODE. No modifica proveedor, wallet ni ledger; solo el reporte.

Campos del cuerpo JSON:

- `paymentId`: string, obligatorio. ID pay del pago; para ORPHAN usa un ID nuevo.
- `mode`: string, obligatorio. Alteración del reporte. CLEAR restaura la fila original. Valores: MISSING, AMOUNT, DUPLICATE, ORPHAN, CLEAR.
- `amountCents`: integer, opcional. Importe en céntimos de PEN. 1500 = S/ 15.00. Obligatorio para AMOUNT y ORPHAN.

Respuestas HTTP: `200`, `400`, `404`, `409`, `413`, `429`.

Campos de respuesta: `configured`.

### `POST /control/reset`

Borra TODOS los datos del grupo y repone wallet-demo con 100000 y dos asientos de apertura. Elimina KYC, pagos, QRs, claves, eventos, reversos, soporte e incidencias. Afecta a todos los integrantes del grupo. No afecta otros grupos ni cambia su URL. Sin cuerpo. Funciona incluso al alcanzar el límite cloud.

Respuestas HTTP: `200`, `400`, `413`.

Campos de respuesta: `reset`.
