## GitHub Issue

- Issue: #2
- Repositorio: user-bcp-student04/wallet-app-g6

## Why

El onboarding de la wallet del MVP en Perú toma una mediana de 8 minutos y no hay instrumentación para medirlo ni para seguir MAU y CAC. El Issue pide un flujo guiado con señales claras de siguiente paso para que el usuario empiece a pagar sin abandonar el proceso. El equipo cuenta con un mock W1 (`docs/bcp-wallet-mock-openapi.yaml`, `docs/H1_registro`) que simula KYC y wallet, pero no hay una interfaz para probar esos servicios ni medir el flujo.

## What Changes

- Flujo de onboarding con pasos visibles y paso actual.
- Bloqueo de avance con mensajes accionables ante datos faltantes o inválidos, incluido el formato de documento ficticio `TEST-`.
- Verificación de identidad simulada (KYC) con los escenarios `APPROVED`, `REJECTED`, `MANUAL_REVIEW` (con decisión posterior) y `UNAVAILABLE`.
- Activación de la wallet (`ACTIVE`) al finalizar y acceso al punto de entrada de pagos de bajo monto; `PENDING` y `REJECTED` no habilitan pagos.
- Consola Angular básica en `web/` para ejecutar y observar los servicios W1 del mock: `GET /health`, `GET /scenarios`, `POST /kyc/verifications`, `GET /kyc/verifications/{id}`, `POST /kyc/verifications/{id}/decision`, `GET /wallets/{id}`, `GET /support/cases` y `POST /control/reset`. Es la "Consola de pruebas", solo para el usuario `admin`.
- Registro de cliente previo al login (tipo `DNI`, número de hasta 8 dígitos, OTP dummy `0000`) e inicio de sesión con DNI y contraseña (dummy `admin`/`admin`; cliente inexistente: "Ups, registrate como nuevo usuario").
- Panel de saldo, últimos movimientos y transferencias por contacto y con QR sobre el mock (`/payments`, `/qrs`).
- Cobertura básica de pruebas por endpoint (camino feliz y un camino de error por servicio).
- Registro de eventos de inicio, de cada paso y de cierre, y cálculo de la duración del onboarding (el mock no lo provee).
- Salida analítica mensual de nuevos usuarios activos y gasto de adquisición atribuido.
- La implementación se genera en el repo destino mediante el pipeline existente (ver `design.md`).

## Preserved Behavior

- Orden de etapas y semántica de `CREWAI_INCLUDE_DATA` del pipeline.
- Nombres de entregables de cada agente y formato `VEREDICTO: APROBADO` / `VEREDICTO: RECHAZADO`.
- Mapeo de rutas y resolución del repo destino de `crew/publish_pr.py`.
- Formato de extracción de código y `python tools/verify.py` con los tests existentes.
- Contrato del mock W1 (solo lectura): no se modifican `docs/bcp-wallet-mock-openapi.yaml` ni `docs/H1_registro`.

## Out of Scope

- Recarga, validación de acceso en transporte, conciliación y reversos.
- Reglas de KYC reales (se usa solo el KYC simulado con documentos `TEST-`).
- Despliegue multipaís, lealtad y APIs abiertas para terceros.
- Autenticación real de usuarios: el registro, el login, el OTP y el código de validación son dummy en el cliente.
- Cambios en el motor del generador, salvo ajustes de instrucciones de agentes aprobados.

## Capabilities

### New Capabilities

- `wallet-onboarding`: flujo de onboarding, KYC simulado, activación de wallet, consola Angular de pruebas, eventos y salida analítica.

### Modified Capabilities

- Ninguna.

## Impact

- Repo destino `user-bcp-student04/wallet-app-g6`: `api/`, `web/` (consola Angular), `db/` y `docs/crewai/<slug>/` en la raíz.
- `wallet-app-g6`: sin cambios previstos en el motor; posibles ajustes en `agents/*.py` si la salida no cubre la spec.
- Dependencias: mock W1 disponible (local `http://127.0.0.1:8787` o URL del grupo en cloud), compatibilidad CORS con el navegador y, para métricas, la definición de «usuario activo» y la fuente del gasto de adquisición.
