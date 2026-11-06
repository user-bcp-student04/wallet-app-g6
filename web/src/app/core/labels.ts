// src/app/core/labels.ts
import { StepId, StepStatus, VerificationStatus, WalletStatus } from './api.models';

export const WALLET_STATUS_LABELS: Record<WalletStatus, string> = {
  NOT_STARTED: 'No iniciada',
  IN_PROGRESS: 'En progreso',
  KYC_PENDING: 'Verificación pendiente',
  KYC_FAILED: 'Verificación fallida',
  ACTIVE: 'Activa',
};

export const STEP_LABELS: Record<StepId, string> = {
  registro: 'Registro',
  kyc: 'Verificación KYC',
  activacion: 'Activación',
};

export const STEP_STATUS_LABELS: Record<StepStatus, string> = {
  COMPLETED: 'Completado',
  CURRENT: 'Paso actual',
  LOCKED: 'Bloqueado',
};

export const VERIFICATION_STATUS_LABELS: Record<VerificationStatus, string> = {
  APPROVED: 'Aprobada',
  REJECTED: 'Rechazada',
  PENDING: 'Pendiente',
  EXPIRED: 'Expirada',
};
