import { ApiResult } from '../models/mock.models';

export interface ReadableError {
  message: string;
  action: string;
}

const BY_CODE: Record<string, ReadableError> = {
  INVALID_MOCK_LATENCY: { message: 'La latencia enviada no es válida.', action: 'Usa un entero entre 0 y 5000 ms.' },
  KYC_UNAVAILABLE: {
    message: 'El servicio de verificación no está disponible.',
    action: 'Reintenta en unos minutos.',
  },
  NOT_FOUND: { message: 'No se encontró el recurso solicitado.', action: 'Comprueba el identificador.' },
  DECISION_CONFLICT: {
    message: 'Esa verificación ya tiene una decisión final distinta.',
    action: 'Una decisión final no se puede cambiar.',
  },
  INVALID_DECISION: { message: 'La decisión no es válida.', action: 'Elige ACTIVE o REJECTED.' },
  INSUFFICIENT_FUNDS: { message: 'Saldo insuficiente.', action: 'Ingresa un monto menor o igual a tu saldo disponible.' },
  WALLET_NOT_ACTIVE: { message: 'Tu wallet no está activa.', action: 'Completa la verificación de tu cuenta.' },
  QR_EXPIRED: { message: 'El QR venció.', action: 'Genera o solicita un QR nuevo.' },
  INVALID_QR: { message: 'El texto del QR no es válido.', action: 'Revisa que tenga el formato qrmock:ID.' },
  QR_PAYMENT_MISMATCH: { message: 'El monto no coincide con el del QR.', action: 'Usa el monto indicado por el QR.' },
  IDEMPOTENCY_CONFLICT: { message: 'Ya existe un pago con otros datos para esta operación.', action: 'Inicia una nueva transferencia.' },
  GROUP_LIMIT_RESET_REQUIRED: {
    message: 'El grupo alcanzó su límite de recursos.',
    action: 'Reinicia el grupo con POST /control/reset.',
  },
};

const BY_STATUS: Record<number, ReadableError> = {
  0: {
    message: 'No se pudo contactar con el mock.',
    action: 'Revisa la URL base, que el mock esté en ejecución y que permita los headers enviados (CORS).',
  },
  400: { message: 'La solicitud tiene datos inválidos.', action: 'Corrige los campos e inténtalo de nuevo.' },
  404: BY_CODE['NOT_FOUND'],
  409: { message: 'La operación entra en conflicto con el estado actual.', action: 'Consulta el estado y reintenta.' },
  413: { message: 'La solicitud es demasiado grande.', action: 'Reduce el tamaño del cuerpo.' },
  410: { message: 'El recurso ya no está vigente.', action: 'Solicita uno nuevo.' },
  504: {
    message: 'No se confirmó la respuesta del pago.',
    action: 'Revisa tus movimientos antes de reintentar, el pago pudo procesarse.',
  },
  429: { message: 'Se superó el límite del grupo.', action: 'Reinicia el grupo con POST /control/reset.' },
  503: { message: 'El servicio no está disponible.', action: 'Reintenta en unos minutos.' },
};

const UNKNOWN: ReadableError = { message: 'Ocurrió un error inesperado.', action: 'Inténtalo de nuevo.' };

export function describeError<T>(result: ApiResult<T>): ReadableError {
  const code = result.error?.error;
  const readable = (code && BY_CODE[code]) || BY_STATUS[result.status] || UNKNOWN;
  return code ? { ...readable, message: `${readable.message} (${code})` } : readable;
}
