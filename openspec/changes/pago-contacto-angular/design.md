# Design

## Context

Ver `proposal.md` para el motivo y `specs/contact-payments/spec.md` para el
contrato observable. Este repositorio contiene el generador CrewAI, no la
aplicación Angular destino. `agents/frontend.py` genera Angular 17 standalone
y `crew/publish_pr.py` mapea `frontend-angular/` a `web/` en el repo producto.
El contrato W2 vive en el mock; sus datos son en memoria y los controles
`/control/*` no son APIs de negocio.

El agente de Testing actual está orientado a pruebas Python/FastAPI. Para cubrir
el consumo del mock desde Angular sin reemplazar su entregable
`testing_report.md`, debe admitir también pruebas del cliente frontend.

## Goals / Non-Goals

**Goals:**

- Extender el frontend Angular existente, sin crear una aplicación separada.
- Mantener intactos los contratos W2 y hacer visibles sus estados y errores.
- Obtener cobertura básica por endpoint y distinguir pruebas locales del mock
  de la validación del generador.

**Non-Goals:**

- Implementar o modificar el mock W2, agregar endpoints o cambiar sus estados.
- Cubrir onboarding/KYC, QR, recarga, acceso al transporte o conciliación.
- Presentar `/control/*` o callbacks de prueba como operaciones para usuarios
  finales.

## Decisions

### Integración desde el frontend existente

Las llamadas W2 se encapsulan en los servicios Angular existentes, con
interfaces tipadas para requests y responses. Los componentes presentan el
flujo y no llaman HTTP directamente. Se reutilizan la URL base y configuración
existentes; no se agrega otro frontend ni una nueva capa backend.

**Alternativas consideradas:** crear una consola frontend separada o cambiar el
contrato del mock. Se descartan porque el requisito indica usar el mismo
frontend y el mock es el contrato protegido.

### Confirmación y recuperación

El cliente distingue `PENDING`, `SUCCEEDED` y `REJECTED`. Para el flujo de
prueba, entrega el evento mediante `POST /callbacks/payments`; para recuperar
un timeout con `paymentId`, consulta o resuelve el pago con las rutas
documentadas. No inicia una nueva operación mientras el resultado de la
anterior sea desconocido. No impone un SLA ni cuenta regresiva: mantiene
`PENDING` hasta recibir un resultado. Solo muestra expiración si un proveedor
la comunica explícitamente; el mock no se amplía para simularla.

Los endpoints de control solo preparan escenarios de prueba. La interfaz los
mantiene separados de las acciones del pagador y no los presenta como API de
negocio.

### Cobertura básica por endpoint

Las pruebas nuevas viven junto al cliente Angular generado y reutilizan el
runner ya configurado en el repositorio producto. Se cubre un resultado exitoso
y al menos un error relevante por endpoint consumido, salvo endpoints que solo
definan éxito; en esos se cubren sus respuestas válidas y el caso vacío cuando
aplique. Una prueba unitaria de servicio verifica método, ruta, parámetros,
cuerpo y mapeo de errores; una prueba integrada contra el mock valida la
transición asíncrona.

| Endpoint | Cobertura básica |
|---|---|
| `GET /wallets/{id}` | `200` con saldos; `404` |
| `POST /payments` | `202` para nueva operación; repetición idempotente `200`; errores `409`, `503` y `504` con sus semánticas |
| `GET /payments?walletId=...` | `200` con resultados y `200` con lista vacía |
| `GET /payments/{id}` | `200`; `404` |
| `GET /payments/{id}/receipt` | `200` cuando está disponible; `409 RECEIPT_NOT_READY`; `404` |
| `GET /provider/payments/{id}` | `200`; `404` |
| `POST /payments/{id}/resolve` | `200` resuelto; `202` pendiente; error `404` o `409` |
| `POST /callbacks/payments` | `200` aplicado; error `404` o `409` |
| `GET /control/events` (solo pruebas) | `200` con eventos y `200` sin eventos |
| `POST /control/provider/{id}/complete` (solo pruebas) | `200`; error `404` o `409` |

`GET /control/events` y `POST /control/provider/{id}/complete` se usan solo
para preparar la prueba integrada de estados asíncronos. No se cubren otros
controles que el flujo no consume.

### Datos y aislamiento

Las pruebas integradas usan una instancia local o un grupo cloud dedicado. El
mock comparte los datos entre integrantes del grupo y `POST /control/reset`
borra todo el estado del grupo; no se ejecuta el reset contra un grupo
compartido sin autorización. No se asume persistencia después de reinicios.
No se fija un umbral numérico de pago bajo: se usa el límite configurado para
el proveedor o canal y no se hardcodea un valor.

## Risks / Trade-offs

- **El timeout puede ocurrir después de procesar el pago** → consultar el
  `paymentId` antes de habilitar un nuevo intento.
- **El mock no define `EXPIRED` ni vencimiento automático** → no inferir
  expiración; la prueba extremo a extremo queda pendiente hasta que exista un
  contrato que emita ese resultado.
- **Las APIs de control no tienen autenticación y afectan el grupo compartido**
  → usarlas solo en una instancia o grupo de pruebas aislado.
- **El mock no implementa métricas ni eventos analíticos** → registrar estos
  datos en la aplicación, pero no atribuir métricas al mock ni declarar
  resultados no ejecutados.
- **El repositorio actual no contiene el Angular destino ni su runner** →
  reutilizar la configuración existente del repo producto y verificarla antes
  de agregar dependencias.

## Migration Plan

No hay migración de base de datos ni cambio de API. Incorporar el flujo y las
pruebas en la generación Angular existente, generar el PR mediante el pipeline
actual y ejecutar las pruebas contra una instancia aislada del mock. Para
revertir, retirar el punto de entrada y los archivos generados de esta
capacidad; el mock y los datos de otros grupos no cambian.

## Open Questions

- Producto debe definir el esquema de eventos, la identidad del usuario y la
  frontera temporal usados para medir funnel y MAU; no se inventan campos en
  este cambio.
- El repositorio de la aplicación Angular destino no está en este workspace;
  al aplicar, se debe identificar su runner de pruebas y confirmar que expone
  la configuración del mock mencionada en la spec antes de añadir dependencias.
