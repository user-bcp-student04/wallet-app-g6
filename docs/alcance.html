# Cobertura y límites

## Datos y límites del paquete

La semilla incluye `wallet-demo` con S/ 1 000.00, destinatario `contact-demo` y comercio `merchant-demo`. Los importes son enteros en céntimos de PEN.

Esta versión mantiene los datos en memoria, sin SQLite ni base externa. Los datos pueden perderse por inactividad del servicio o por un despliegue; la idempotencia se comprueba mientras se mantienen los datos del grupo. Si ocurre un reinicio, usa la misma URL fija y repite el escenario. `POST /control/reset` borra los datos y repone la semilla. La separación por grupo organiza los datos de prueba; no hay autenticación y cualquiera que conozca la URL puede operar los mocks de ese grupo. Hay un límite de 2 000 recursos por grupo; usa el reinicio para empezar de nuevo. No hay webhooks salientes ni movimientos de dinero real. El ZIP es opcional para pruebas locales.

## Cobertura frente a los criterios del reto

Los ocho grupos tienen las mismas APIs y escenarios W1–W6. La API simula dependencias para construir el MVP; pasar sus pruebas no demuestra por sí solo que una aplicación cumpla todos los criterios de las historias.

- W1 permite probar validación de entradas, activación, rechazo y revisión. La aplicación del equipo implementa la secuencia de pantallas y la instrumentación de inicio, pasos y fin. El mock no calcula duración, MAU, CAC ni atribución de adquisición. Las nuevas wallets tienen saldo cero y no existe una API de recarga; usa wallet-demo para los pagos con fondos.
- W2 permite probar aprobación, rechazo, saldo insuficiente, demora, timeout y comprobante. No hay estado EXPIRED de pago ni vencimiento automático: PENDING solo cambia mediante control del proveedor y confirmación. El QR sí puede vencer. La identidad visible del destinatario y los eventos de activación los implementa la aplicación; no hay catálogo de contactos ni analítica de checkout en el mock.
- W3 permite crear y resolver QR, vincularlo al pago y consultar el resultado por referencia. No hay timestamps, filtro por fecha ni consulta de historial por comercio. GET /payments lista una wallet, no todos los pagos recibidos por un comercio. Si el equipo necesita la vista comercial diaria, debe conservar referencias, fechas y estados en su aplicación y actualizarse consultando el pago.
- W4 evita operaciones y asientos duplicados. Repetir devuelve el estado actual de la operación original, que puede haber avanzado desde PENDING. No hay ventana de retención, registro de cada solicitud duplicada ni IDs de correlación por solicitud. La conciliación compara operaciones financieras; no enumera reintentos HTTP. La auditoría de solicitudes corresponde a la aplicación.
- W5 permite distinguir rechazo, proveedor caído y timeout ya procesado; consultar soporte y ejecutar un reverso completo simulado. No hay clasificación persistida de todos los rechazos, matriz de elegibilidad, expediente de disputa, SLA ni bitácora de acciones del operador. Los códigos de error HTTP y motivos de casos ayudan a implementar esos flujos en la aplicación. El reverso simulado no representa una regla de cancelación bancaria real.
- W6 compara wallet, proveedor y ledger, conserva incidencias y permite resolverlas al corregir su causa. No hay fecha de negocio, canal de proveedor, cierre diario, filtros de fechas ni resumen diario con totales. Para esos criterios, la aplicación necesita registrar fechas y canales y construir su reporte. Las APIs del mock solo devuelven la base completa del grupo.

Los controles `/control/*` permiten preparar escenarios. No son APIs de negocio para usuarios finales. Los casos de soporte se cierran mediante la decisión KYC o la confirmación del pago; no existe un endpoint para editar su estado manualmente.
