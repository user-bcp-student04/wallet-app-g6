# Proposal

## Why

El issue [#15](https://github.com/user-bcp-student04/wallet-app-g6/issues/15) busca que el pagador pueda completar un pago de bajo monto a contacto y conocer su resultado sin riesgo de cobros duplicados. El flujo debe probarse desde el mismo frontend Angular existente y cubrir los contratos del mock endpoint por endpoint.

## What Changes

- Agregar al frontend Angular generado el flujo de pago a contacto, con destino e importe visibles, estados pendientes y terminales, recuperación ante timeout, historial y comprobante.
- Consumir los endpoints W2 documentados sin cambiar sus contratos ni presentar las APIs `/control/*` como operaciones de negocio.
- Incorporar pruebas básicas por endpoint: respuesta exitosa y un error relevante cuando el contrato lo defina.
- Extender el agente de Testing para que genere cobertura del cliente Angular además de pruebas de API, conservando el entregable `testing_report.md`.
- Registrar la cobertura y los resultados de las pruebas sin afirmar ejecuciones que no se hayan realizado.
- Instrumentar el funnel de checkout y el evento de activación del pagador exitoso conforme a la especificación.

## Alcance

Incluye pagos a contacto de bajo monto probados desde el frontend Angular existente. La cobertura se limita a los endpoints de pago usados por ese flujo y al mock documentado.

## Fuera de alcance

Onboarding/KYC, recargas, QR, acceso a validadores, conciliación, movimiento de dinero real y cambios al contrato del mock. No se inventará un estado de expiración que el mock no expone.

## Capabilities

### New Capabilities

- `contact-payments`: iniciar y consultar pagos de bajo monto a contacto, comunicar su resultado, obtener historial y comprobante, y probar el flujo desde el frontend Angular.

### Modified Capabilities

- Ninguna.

## Impact

- Repositorio producto generado: el agente Frontend entrega código Angular bajo `frontend-angular/`, que el publicador mapea a `web/` en el repositorio destino.
- Integración con el mock W2 de pagos; no se modifican sus endpoints.
- El agente de Testing debe poder generar pruebas del cliente Angular para estos endpoints y conservar `testing_report.md`.
- La especificación fuente es `openspec/changes/Pago-contacto-wallet/specs/wallet-onboarding/spec.md`; el detalle de API se contrasta con `docs/H2_pago_contacto` y `docs/endpoint_h2`.
