# Épica: MVP de wallet en Perú para acceso al transporte público

Documentación de la épica definida en [peru-wallet-mvp.sp.md](peru-wallet-mvp.sp.md), enfocada en el acceso al transporte público.

## Descripción

Lanzar un MVP de wallet en Perú que permita pagar y acceder al transporte público con un solo medio de pago, ya sea por contacto o por QR. Busca reducir la fricción en checkout y acelerar el onboarding, manteniendo la confianza del usuario con confirmaciones claras, manejo confiable de estados y límites alineados a cumplimiento.

## Público objetivo

- **Empresas de transporte público**: tren, metropolitano y corredores auxiliares.
- **Usuarios del transporte público** que acceden y recargan con smartphone.

## Problema

- El acceso al transporte depende de una **tarjeta física recargable**.
- Recargar con otras billeteras digitales exige un **paso adicional de activación**.
- Se forman **colas** para activar la recarga o realizar recargas.
- Muchos pasajeros abandonan el pago a mitad de camino y crear la cuenta toma demasiado tiempo: terminan perdiendo minutos valiosos antes de poder viajar.

## Propuesta de valor

- **Un solo medio de pago** que agiliza el acceso al transporte, con contacto o por QR.
- **Sin reposición de tarjetas** por deterioro o pérdida.
- **Sin colas ni paso de activación** para recargar.

## Objetivos (1 trimestre)

| Métrica | Línea base | Objetivo |
|---|---|---|
| Caída en checkout | 30% | 8% |
| Tiempo de onboarding | 8 min | 3 min |
| MAU (meses 1-3 post-lanzamiento) | n/d | 1,000 - 2,000 |
| CAC por usuario nuevo (meses 1-3) | n/d | PEN 10 |

Los umbrales de MAU y CAC los define el Product Owner. Las métricas específicas de transporte (por ejemplo, tiempo de acceso o reducción de colas) están por definir.

## Alcance

**Incluye**

- Onboarding de wallet para el segmento MVP en Perú.
- Pago de acceso al transporte público por contacto o QR.
- Recarga desde la wallet sin paso adicional de activación.
- Visibilidad de confirmación y estado de pago para usuarios y empresas de transporte.
- Instrumentación base del funnel de checkout, finalización de onboarding y activación al mes 3.

**Fuera de alcance**

- Despliegue multipaís amplio.
- Programas avanzados de lealtad o mecánicas de crecimiento no esenciales.
- Paridad funcional completa entre todos los proveedores/bancos externos desde el día uno.
- APIs de pago abiertas y de autoservicio para terceros.

## Supuestos y restricciones

- Ecosistema multirriel: no asumir un único riel de procesamiento de extremo a extremo.
- Integraciones contractuales con habilitaciones operativas; el alta de proveedores no es inmediata.
- Los límites por proveedor pueden ser menores al máximo regulatorio; el producto y la UX deben reflejarlo.
- Se espera disponibilidad de pagos inmediatos con alias (24x7x365).
- La confirmación de pago en el acceso debe ser rápida; el tiempo máximo aceptable está por definir con cada operador.

## Dependencias y riesgos

| Tipo | Descripción |
|---|---|
| Dependencia | Acuerdos y habilitación técnica con las empresas de transporte (tren, metropolitano, corredores auxiliares). |
| Dependencia | Compatibilidad de los validadores con lectura por contacto y por QR. |
| Dependencia | Partners de adquirencia/gateway para QR y procesamiento wallet. |
| Riesgo | Reintentos sin idempotencia robusta: duplicidad financiera y desvíos de conciliación. |
| Riesgo | Transiciones asíncronas del estado de pago: pérdida de confianza si la confirmación no es clara o llega tarde en el acceso. |
| Riesgo | Reversos y disputas deben tener manejo operativo/legal explícito. |

## Historias de usuario candidatas

1. Como usuario del transporte público, completo el onboarding rápidamente y entiendo el siguiente paso en cada punto del flujo.
2. Como pasajero, accedo al transporte pagando por contacto o QR con la wallet, sin tarjeta física.
3. Como pasajero, recargo desde mi wallet sin paso adicional de activación ni colas.
4. Como pasajero, no necesito reponer una tarjeta por deterioro o pérdida.
5. Como empresa de transporte, valido el estado del pago de forma confiable en el acceso.
6. Como operaciones/compliance, monitoreo estados de pago y concilio las transacciones núcleo del MVP.
