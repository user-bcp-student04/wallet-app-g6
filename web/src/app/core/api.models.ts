// src/app/core/api.models.ts
// Espejo en TypeScript de api/app/schemas.py. Una interfaz de request y una de response por endpoint.

export type KycScenario = 'APPROVED' | 'REJECTED' | 'PENDING' | 'EXPIRED';
export type VerificationStatus = 'APPROVED' | 'REJECTED' | 'PENDING' | 'EXPIRED';
export type KycDecision = 'APPROVED' | 'REJECTED';
export type WalletStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'KYC_PENDING' | 'KYC_FAILED' | 'ACTIVE';
export type StepId = 'registro' | 'kyc' | 'activacion';
export type StepStatus = 'COMPLETED' | 'CURRENT' | 'LOCKED';

/** Cuerpo de error único del API. */
export interface ApiErrorBody {
  code: string;
  message: string;
}

/** Error ya normalizado para la interfaz (status 0 = sin conexión). */
export interface ApiErrorView extends ApiErrorBody {
  status: number;
}

// GET /health (sin entrada)
export type HealthRequest = void;
export interface HealthResponse {
  status: string;
}

// GET /scenarios (sin entrada)
export type ScenariosRequest = void;
export interface ScenarioItem {
  name: KycScenario;
  description: string;
}
export interface ScenariosResponse {
  scenarios: ScenarioItem[];
}

// GET /support/cases (sin entrada)
export type SupportCasesRequest = void;
export interface SupportCase {
  verification_id: string;
  status: VerificationStatus;
  message: string;
}
export interface SupportCasesResponse {
  cases: SupportCase[];
}

// Respuesta común de KYC
export interface VerificationResponse {
  verification_id: string;
  document_number: string;
  scenario: KycScenario;
  status: VerificationStatus;
  created_at: string;
  decided_at: string | null;
}

// POST /kyc/verifications
export interface CreateVerificationRequest {
  document_number: string;
  scenario: KycScenario;
}

// GET /kyc/verifications/{verification_id}
export interface GetVerificationRequest {
  verification_id: string;
}

// POST /kyc/verifications/{verification_id}/decision
export interface DecideVerificationRequest {
  verification_id: string;
  decision: KycDecision;
}

// Respuesta común de onboarding
export interface StepInfo {
  id: StepId;
  order: number;
  status: StepStatus;
}
export interface OnboardingStateResponse {
  wallet_status: WalletStatus;
  current_step: StepId | null;
  steps: StepInfo[];
  low_amount_payments_enabled: boolean;
  duration_seconds: number | null;
}

// GET /onboarding (sin entrada)
export type GetOnboardingRequest = void;

// POST /onboarding/steps/{step_id}  (document_number solo en 'registro')
export interface SubmitStepRequest {
  step_id: StepId;
  document_number?: string;
}

// POST /control/reset (sin cuerpo)
export type ResetRequest = void;
export interface ResetResponse {
  status: string;
}
