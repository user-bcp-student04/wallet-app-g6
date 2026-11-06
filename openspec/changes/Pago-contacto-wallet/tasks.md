## 1. Preparación

- [ ] 1.1 Configurar `.env` con `GITHUB_OWNER=user-bcp-student04`, `PR_REPO=wallet-app-g6` y `CREWAI_INCLUDE_DATA=true`
- [ ] 1.2 Ejecutar `python tools/verify.py` en `wallet-app-g6` y registrar la línea base
- [ ] 1.3 Cerrar las preguntas bloqueantes de la spec (frontera de eventos, pasos adicionales al KYC simulado, persistencia de eventos, CORS del mock, usuario activo, fuente de gasto de adquisición)
- [ ] 1.4 Verificar que el mock W1 responde (`GET /health`) en la URL local o del grupo y fijarla en `environment.ts`

## 2. Generación en el repo destino

- [ ] 2.1 Ejecutar el pipeline con H01 como feature y revisar `user_story.md` contra la spec
- [ ] 2.2 Servicio tipado del mock (`MockApiService`) con interfaces de request y response por endpoint, y `SessionService` único
- [ ] 2.3 Estado de wallet y validación de pasos con bloqueo, documento `TEST-` y mensajes accionables
- [ ] 2.4 KYC: `POST /kyc/verifications` con los cuatro escenarios, consulta y decisión sobre `PENDING`
- [ ] 2.5 Registro de eventos de inicio, paso y cierre, y cálculo de duración
- [ ] 2.6 Interfaz: flujo guiado con pasos visibles y paso actual, y acceso a pagos de bajo monto según estado de wallet
- [ ] 2.7 Consola de servicios: `GET /health`, `GET /scenarios`, `GET /support/cases`, ejecución individual, errores legibles y `POST /control/reset` con confirmación
- [ ] 2.8 Salida analítica mensual de nuevos usuarios activos y gasto atribuido

## 3. Pruebas

Cobertura básica por endpoint (camino feliz y un camino de error), según la tabla de `design.md`.

- [ ] 3.1 `GET /health`: `200` y latencia inválida bloqueada en cliente
- [ ] 3.2 `GET /scenarios`: llena el selector; error de red con mensaje legible
- [ ] 3.3 `POST /kyc/verifications`: `201` en `APPROVED`, `REJECTED` y `MANUAL_REVIEW`; `503 KYC_UNAVAILABLE`; documento sin `TEST-` bloqueado
- [ ] 3.4 `GET /kyc/verifications/{id}`: `200` y `404`
- [ ] 3.5 `POST /kyc/verifications/{id}/decision`: `200` sobre `PENDING` y `409 DECISION_CONFLICT`
- [ ] 3.6 `GET /wallets/{id}`: `200` con saldos 0 y `404`
- [ ] 3.7 `GET /support/cases`: caso `KYC_REVIEW` `OPEN` y lista vacía
- [ ] 3.8 `POST /control/reset`: `200` limpia estado local; cancelar la confirmación no llama a la API
- [ ] 3.9 Manejador de errores común: `400`, `404`, `409`, `413`, `429` y `503` con mensaje accionable
- [ ] 3.10 Pasos visibles, bloqueo con dato faltante e inválido, y estado activo tras onboarding exitoso frente a incompleto, `PENDING` o `REJECTED`
- [ ] 3.11 Eventos (completo y abandonado) y cálculo de mediana
- [ ] 3.12 Adjuntar al PR la salida real de las pruebas ejecutadas por una persona

## 4. Validación

- [ ] 4.1 Ejecutar `python tools/verify.py` y registrar el resultado
