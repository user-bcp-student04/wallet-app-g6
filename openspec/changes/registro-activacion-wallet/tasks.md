## 1. Preparación

- [x] 1.1 Configurar `.env` con `GITHUB_OWNER=user-bcp-student04`, `PR_REPO=wallet-app-g6` y `CREWAI_INCLUDE_DATA=true`
  - Verificado el 2026-11-06: las tres variables están definidas en `.env`, que está ignorado por git y no se versiona.
- [x] 1.2 Ejecutar `python tools/verify.py` en `wallet-app-g6` y registrar la línea base
  - Línea base (2026-11-06, Python 3.13.15, crewai 1.15.36): `Ran 21 tests ... OK` y `All pipeline checks passed. No model or external service was called.`
- [x] 1.3 Cerrar las preguntas bloqueantes de la spec (frontera de eventos, pasos adicionales al KYC simulado, persistencia de eventos, CORS del mock, usuario activo, fuente de gasto de adquisición)
  - Decisiones humanas (2026-11-06):
    - Persistencia de eventos: almacenamiento local del navegador, provisional; no sirve para MAU y CAC reales.
    - Frontera de duración: `STARTED` al abrir el flujo guiado hasta `CLOSED` en un estado final (`ACTIVE`, `REJECTED`) o abandono.
    - Datos adicionales al KYC simulado: ninguno; solo `documentType`, `document` (`TEST-`) y escenario.
    - Espera de `PENDING`: mensaje de revisión pendiente; ese tiempo no cuenta en la duración y el evento se cierra en `PENDING`.
    - CORS: sin proxy por ahora; usar proxy de desarrollo solo si falla.
    - Usuario activo (MAU): wallet en estado `ACTIVE` tras onboarding exitoso en el mes.
    - Gasto de adquisición (CAC): sin fuente definida; la salida analítica recibe el gasto como parámetro de entrada manual.
    - Muestra de la mediana: 100% de la cohorte MVP.
  - Pendiente: reflejar estas decisiones en la spec (`openspec-update-change`); la lista de preguntas abiertas de `spec.md` sigue sin actualizar.
- [x] 1.4 Verificar que el mock W1 responde (`GET /health`) en la URL local o del grupo y fijarla en `environment.ts`
  - URL del grupo: `https://bcp-wallet-mock.yefri.workers.dev/groups/6`. `GET /health` -> `200 {"status":"ok","environment":"cloud-mock","storage":"sqlite",...}` (2026-11-06). La URL local `http://127.0.0.1:8787` rechaza la conexión.
  - CORS del mock en nube: `Access-Control-Allow-Origin: *`, métodos `GET, POST, OPTIONS`, `OPTIONS` -> `204`.
  - Hallazgo: `Access-Control-Allow-Headers` solo permite `Content-Type, Idempotency-Key`; un navegador bloqueará `X-Mock-Latency-Ms` (exigido por la spec) en el preflight. Candidato a backlog: proxy de desarrollo solo para la latencia, o pedir al mock que la permita. No se resuelve aquí.
  - `environment.ts` ya existe en `web/` con esa URL del grupo como valor por defecto. Mitigación provisional del hallazgo CORS: `X-Mock-Latency-Ms` solo se envía si la latencia es mayor que 0, así el uso por defecto no dispara el preflight bloqueado; con latencia > 0 el navegador seguirá bloqueándolo hasta resolver el candidato a backlog.

## 2. Generación en el repo destino

- [ ] 2.1 Ejecutar el pipeline con H01 como feature y revisar `user_story.md` contra la spec
  - No ejecutado: el pipeline es interactivo (MCP, Copilot y aprobación humana por etapa); `web/` se implementó manualmente y queda pendiente decidir si se contrasta con `user_story.md`.
- [x] 2.2 Servicio tipado del mock (`MockApiService`) con interfaces de request y response por endpoint, y `SessionService` único
- [x] 2.3 Estado de wallet y validación de pasos con bloqueo, documento `TEST-` y mensajes accionables
- [x] 2.4 KYC: `POST /kyc/verifications` con los cuatro escenarios, consulta y decisión sobre `PENDING`
- [x] 2.5 Registro de eventos de inicio, paso y cierre, y cálculo de duración
- [x] 2.6 Interfaz: flujo guiado con pasos visibles y paso actual, y acceso a pagos de bajo monto según estado de wallet
- [x] 2.7 Consola de servicios: `GET /health`, `GET /scenarios`, `GET /support/cases`, ejecución individual, errores legibles y `POST /control/reset` con confirmación
- [x] 2.8 Salida analítica mensual de nuevos usuarios activos y gasto atribuido
  - Fuente del gasto provisional: campo manual en la consola; la fuente real sigue abierta.
  - Cambio de alcance (2026-11-06, pedido del usuario tras revisar la vista): `web/` ahora abre con login (DNI y contraseña; usuario dummy `admin`/`admin`) y un panel con saldo, últimos movimientos y transferencias (pago a contacto y pago con QR, con flujo de confirmación y código de validación). El flujo de onboarding y la consola de servicios pasaron a la sección "Consola de pruebas", visible solo para admin. `spec.md`, `design.md` y `proposal.md` se actualizaron el 2026-11-06 para reflejar este cambio.
  - Ampliación (2026-11-06): antes del login hay una vista de registro (tipo de documento `DNI`; número solo dígitos, máximo 8) con OTP de aprobación dummy `0000`; al validarlo se entra al panel como `customer` (sin Consola de pruebas). En el login, un DNI distinto de `admin` muestra "Ups, registrate como nuevo usuario".

## 3. Pruebas

Cobertura básica por endpoint (camino feliz y un camino de error), según la tabla de `design.md`.

- [x] 3.1 `GET /health`: `200` y latencia inválida bloqueada en cliente
- [x] 3.2 `GET /scenarios`: llena el selector; error de red con mensaje legible
- [x] 3.3 `POST /kyc/verifications`: `201` en `APPROVED`, `REJECTED` y `MANUAL_REVIEW`; `503 KYC_UNAVAILABLE`; documento sin `TEST-` bloqueado
- [x] 3.4 `GET /kyc/verifications/{id}`: `200` y `404`
- [x] 3.5 `POST /kyc/verifications/{id}/decision`: `200` sobre `PENDING` y `409 DECISION_CONFLICT`
- [x] 3.6 `GET /wallets/{id}`: `200` con saldos 0 y `404`
- [x] 3.7 `GET /support/cases`: caso `KYC_REVIEW` `OPEN` y lista vacía
- [x] 3.8 `POST /control/reset`: `200` limpia estado local; cancelar la confirmación no llama a la API
- [x] 3.9 Manejador de errores común: `400`, `404`, `409`, `413`, `429` y `503` con mensaje accionable
- [x] 3.10 Pasos visibles, bloqueo con dato faltante e inválido, y estado activo tras onboarding exitoso frente a incompleto, `PENDING` o `REJECTED`
- [x] 3.11 Eventos (completo y abandonado) y cálculo de mediana
  - Evidencia (2026-11-06): `npx ng test --watch=false` en `web/`: 4 archivos, 46 pruebas pasadas; `npx ng build` sin errores.
  - Validación manual (2026-11-06) con `ng serve` en `http://localhost:4200` contra el mock del grupo 6: `GET /scenarios`, `POST /kyc/verifications` (`APPROVED` y `MANUAL_REVIEW`), `GET /wallets/{id}`, `GET /support/cases` y decisión `ACTIVE` (repetida: `200`) funcionan desde el navegador. Con latencia 300 ms el navegador bloquea `GET /health` por CORS (`x-mock-latency-ms` no permitido), como anticipaba el hallazgo de 1.4. Corregido un defecto: el flujo mostraba el estado de la última verificación creada desde la consola en lugar del de su propia wallet.
- [ ] 3.12 Adjuntar al PR la salida real de las pruebas ejecutadas por una persona

## 4. Validación

- [x] 4.1 Ejecutar `python tools/verify.py` y registrar el resultado
  - Resultado (2026-11-06) tras integrar `origin/main` (que corrige el conflicto de `tests/test_publish.py`): `Ran 24 tests ... OK` y `All pipeline checks passed. No model or external service was called.`
