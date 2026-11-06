## 1. Preparación

- [x] 1.1 Configurar `.env` con `GITHUB_OWNER=user-bcp-student04`, `PR_REPO=wallet-app-g6` y `CREWAI_INCLUDE_DATA=true`
  - Verificado el 2026-11-06: las tres variables están definidas en `.env`, que está ignorado por git y no se versiona.
- [x] 1.2 Ejecutar `python tools/verify.py` en `wallet-app-g6` y registrar la línea base
  - Línea base (2026-11-06, Python 3.13.15, crewai 1.15.36): `Ran 21 tests ... OK` y `All pipeline checks passed. No model or external service was called.`
- [ ] 1.3 Cerrar las preguntas bloqueantes de la spec (frontera de eventos, pasos adicionales al KYC simulado, persistencia de eventos, CORS del mock, usuario activo, fuente de gasto de adquisición)
  - Cerrada: persistencia de eventos = almacenamiento local del navegador, provisional (según `design.md`); no sirve para MAU y CAC reales.
  - Siguen abiertas: frontera de eventos de duración, pasos adicionales al KYC simulado, CORS del mock, usuario activo, fuente de gasto de adquisición (y espera de `PENDING`, muestra de la mediana).
- [ ] 1.4 Verificar que el mock W1 responde (`GET /health`) en la URL local o del grupo y fijarla en `environment.ts`
  - Pendiente: `GET http://127.0.0.1:8787/health` expiró (2026-11-06) porque el mock no está en ejecución, y `environment.ts` no existe hasta que se genere `web/` (issue #8).

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
  - Evidencia (2026-11-06): `npx ng test --watch=false` en `web/`: 4 archivos, 44 pruebas pasadas.
- [ ] 3.12 Adjuntar al PR la salida real de las pruebas ejecutadas por una persona

## 4. Validación

- [ ] 4.1 Ejecutar `python tools/verify.py` y registrar el resultado
  - Resultado (2026-11-06) sobre `main` + `web/`: falla (`Ran 20 tests`, `errors=1`) por marcadores de conflicto de merge en `tests/test_publish.py` (líneas 54-58 y 73-77), ya presentes en `main` desde `e311d2e`. Hallazgo secundario fuera del alcance; las otras 20 pruebas pasan.
