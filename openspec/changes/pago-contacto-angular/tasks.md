# Tasks

Issue: [#15](https://github.com/user-bcp-student04/wallet-app-g6/issues/15)

## 1. Preparación y contratos

- [ ] 1.1 Identificar el repositorio producto y el frontend Angular existente; registrar su configuración de URL base y el comando de pruebas ya configurado, verificando que no se crea un segundo frontend ni se agrega un runner nuevo.
- [ ] 1.2 Verificar que la instancia W2 de pruebas está aislada y que `wallet-demo` está disponible para los escenarios; comprobarlo con `GET /wallets/{id}` sin ejecutar `POST /control/reset` en un grupo compartido.
- [ ] 1.3 Localizar la configuración del límite por proveedor/canal y confirmar que el flujo la consulta sin hardcodear un umbral; si no existe, registrar el bloqueo para Producto en lugar de inventar un valor.
- [ ] 1.4 Obtener de Producto el contrato de eventos de checkout y activación (nombres, identidad, marca temporal y frontera mensual) antes de implementar analítica; verificar que queda aprobado y documentado.

## 2. Cliente Angular y cobertura básica por endpoint

- [ ] 2.1 Extender las instrucciones del agente de Testing para generar pruebas del cliente Angular bajo `frontend-angular/`, además de las pruebas API existentes; verificar que se conserva `testing_report.md` y pasan las pruebas del generador.
- [ ] 2.2 Añadir el consumo tipado de `GET /wallets/{id}` y su prueba: `200` con saldos y `404`; verificar ruta, respuesta y manejo del error en el servicio Angular.
- [ ] 2.3 Añadir el consumo tipado de `POST /payments` y sus pruebas: creación `202`, repetición idempotente `200`, errores `409` (`WALLET_NOT_ACTIVE`, `INSUFFICIENT_FUNDS`, `IDEMPOTENCY_CONFLICT`), `503` y `504` con `paymentId`; verificar cada resultado y que no se duplica el envío.
- [ ] 2.4 Añadir el consumo de `GET /payments?walletId=...` y sus pruebas para historial con pagos y lista vacía; verificar que ambos casos devuelven `200` y se representan correctamente.
- [ ] 2.5 Añadir el consumo de `GET /payments/{id}` y sus pruebas `200`/`404`; verificar que el estado consultado no se confunde con el estado del proveedor.
- [ ] 2.6 Añadir el consumo de `GET /payments/{id}/receipt` y sus pruebas `200`, `409 RECEIPT_NOT_READY` y `404`; verificar que no se muestra comprobante antes de tiempo.
- [ ] 2.7 Añadir el consumo de `GET /provider/payments/{id}` y sus pruebas `200`/`404`; verificar que consultar proveedor no cambia por sí solo el estado local de la wallet.
- [ ] 2.8 Añadir el consumo de `POST /payments/{id}/resolve` y sus pruebas `200` terminal, `202` pendiente y un error `404` o `409`; verificar la recuperación de una operación identificada sin crear otra.
- [ ] 2.9 Añadir el consumo de `POST /callbacks/payments` y sus pruebas `200` aplicado y error `404` o `409`; verificar que la confirmación actualiza el estado local una sola vez.
- [ ] 2.10 Añadir `GET /control/events` solo al modo de pruebas y verificar `200` con eventos y `200` con lista vacía, sin mostrarlo como API de negocio.
- [ ] 2.11 Añadir `POST /control/provider/{id}/complete` solo al modo de pruebas y verificar `200` y un error relevante (`400`, `404` o `409`), sin exponerlo como acción del pagador.

## 3. Flujo desde el frontend existente

- [ ] 3.1 Implementar en el frontend Angular existente la revisión de destinatario e importe, validaciones y envío idempotente; verificar con pruebas de componente que el importe mostrado coincide con los céntimos enviados y que un doble clic no crea otra solicitud.
- [ ] 3.2 Implementar estados `PENDING`, `SUCCEEDED` y `REJECTED`, errores y acciones de recuperación; verificar con pruebas de interfaz que no se anuncia un resultado terminal antes de confirmarlo y que un timeout con `paymentId` se consulta antes de reintentar.
- [ ] 3.3 Integrar historial y comprobante en el mismo frontend; verificar que se muestran tras `SUCCEEDED` y que `RECEIPT_NOT_READY` no se representa como éxito.
- [ ] 3.4 Ejecutar desde el frontend existente los escenarios aprobado, rechazado, pendiente/demorado y timeout contra el mock aislado; verificar las transiciones y guardar resultados reales en `testing_report.md`.

## 4. Métricas y validación integrada

- [ ] 4.1 Implementar los eventos de inicio/finalización de checkout y activación del pagador exitoso conforme al contrato aprobado por Producto; verificar que los eventos permiten calcular la caída y el MAU mensual sin atribuirlos al mock.
- [ ] 4.2 Ejecutar el comando de pruebas Angular identificado en 1.1 y completar la matriz endpoint por endpoint con resultado real o `NO EJECUTADO`; verificar que cada endpoint usado tenga el caso exitoso y el error relevante descritos en `design.md`.
- [ ] 4.3 Ejecutar `python tools/verify.py` en el generador y registrar su resultado; verificar que la suite del generador se reporte separada de las pruebas del producto Angular.
- [ ] 4.4 Revisar el resultado del Chapter y adjuntar al issue/PR el reporte y la salida real de las pruebas; verificar que no se declare como ejecutado ningún caso sin evidencia.
