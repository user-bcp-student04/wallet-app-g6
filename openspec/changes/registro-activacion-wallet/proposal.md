## GitHub Issue

- Issue: #2
- Repositorio: user-bcp-student04/wallet-app-g6

## Why

El onboarding de la wallet del MVP en Perú toma una mediana de 8 minutos y no hay instrumentación para medirlo ni para seguir MAU y CAC. El Issue pide un flujo guiado con señales claras de siguiente paso para que el usuario empiece a pagar sin abandonar el proceso.

## What Changes

- Flujo de onboarding con pasos visibles y paso actual.
- Bloqueo de avance con mensajes accionables ante datos faltantes o inválidos.
- Activación de la wallet al finalizar y acceso al punto de entrada de pagos de bajo monto.
- Registro de eventos de inicio, de cada paso y de cierre.
- Salida analítica mensual de nuevos usuarios activos y gasto de adquisición atribuido.
- La implementación se genera en el repo destino mediante el pipeline existente (ver `design.md`).

## Preserved Behavior

- Orden de etapas y semántica de `CREWAI_INCLUDE_DATA` del pipeline.
- Nombres de entregables de cada agente y formato `VEREDICTO: APROBADO` / `VEREDICTO: RECHAZADO`.
- Mapeo de rutas y resolución del repo destino de `crew/publish_pr.py`.
- Formato de extracción de código y `python tools/verify.py` con los tests existentes.

## Out of Scope

- Pago por contacto o QR, recarga, validación de acceso en transporte y conciliación.
- Definición de los requisitos de KYC.
- Despliegue multipaís, lealtad y APIs abiertas para terceros.
- Cambios en el motor del generador, salvo ajustes de instrucciones de agentes aprobados.

## Capabilities

### New Capabilities

- `wallet-onboarding`: flujo de onboarding, activación de wallet, eventos y salida analítica.

### Modified Capabilities

- Ninguna.

## Impact

- Repo destino `user-bcp-student04/wallet-app-g6`: `api/`, `web/`, `db/` y `docs/crewai/<slug>/` en la raíz.
- `wallet-app-g6`: sin cambios previstos en el motor; posibles ajustes en `agents/*.py` si la salida no cubre la spec.
- Dependencias: definición de KYC con cumplimiento y producto.
