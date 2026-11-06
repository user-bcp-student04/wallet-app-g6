## 1. Preparación

- [ ] 1.1 Configurar `.env` con `GITHUB_OWNER=user-bcp-student04`, `PR_REPO=wallet-app-g6` y `CREWAI_INCLUDE_DATA=true`
- [ ] 1.2 Ejecutar `python tools/verify.py` en `wallet-app-g6` y registrar la línea base
- [ ] 1.3 Cerrar las preguntas bloqueantes de la spec (frontera de eventos, pasos y KYC, usuario activo, fuente de gasto de adquisición)

## 2. Generación en el repo destino

- [ ] 2.1 Ejecutar el pipeline con H01 como feature y revisar `user_story.md` contra la spec
- [ ] 2.2 Estado de wallet y validación de pasos con bloqueo y mensajes accionables
- [ ] 2.3 Registro de eventos de inicio, paso y cierre
- [ ] 2.4 Salida analítica mensual de nuevos usuarios activos y gasto atribuido
- [ ] 2.5 Interfaz con pasos visibles, paso actual y acceso a pagos de bajo monto

## 3. Pruebas

- [ ] 3.1 Pruebas de pasos visibles, bloqueo con dato faltante e inválido
- [ ] 3.2 Pruebas de estado activo tras onboarding exitoso y no activo tras uno incompleto
- [ ] 3.3 Pruebas de eventos (completo y abandonado) y del cálculo de mediana
- [ ] 3.4 Adjuntar al PR la salida real de las pruebas ejecutadas por una persona

## 4. Validación

- [ ] 4.1 Ejecutar `python tools/verify.py` y registrar el resultado
