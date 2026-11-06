export type KycScenario = 'APPROVED' | 'REJECTED' | 'MANUAL_REVIEW' | 'UNAVAILABLE';
export type WalletStatus = 'ACTIVE' | 'PENDING' | 'REJECTED';

export interface Health {
  status: 'ok';
  storage: 'memory';
  environment?: string;
}

export interface Scenarios {
  kyc: string[];
  payments: string[];
  settlements: string[];
}

export interface KycRequest {
  documentType: 'TEST';
  document: string;
  scenario?: string;
}

export interface Kyc {
  id: string;
  wallet_id: string;
  scenario: Exclude<KycScenario, 'UNAVAILABLE'>;
  status: WalletStatus;
}

export interface DecisionRequest {
  decision: 'ACTIVE' | 'REJECTED';
}

export interface Wallet {
  id: string;
  status: WalletStatus;
  balance: number;
  reserved: number;
  available: number;
  currency: 'PEN';
}

export interface SupportCase {
  id: string;
  resource: string;
  reason: 'KYC_REVIEW' | 'UNKNOWN_PAYMENT_RESULT' | 'PROVIDER_PENDING';
  status: 'OPEN' | 'RESOLVED';
}

export interface Reset {
  reset: boolean;
}

export interface MockError {
  error: string;
}

export interface ApiResult<T> {
  method: 'GET' | 'POST';
  path: string;
  requestBody: unknown;
  status: number;
  ok: boolean;
  body: T | null;
  error: MockError | null;
  elapsedMs: number;
  blockedByClient: boolean;
}

export type OnboardingEventType = 'STARTED' | 'STEP_COMPLETED' | 'CLOSED';

export interface OnboardingEvent {
  type: OnboardingEventType;
  userId: string;
  step?: string;
  outcome?: WalletStatus;
  verificationId?: string;
  timestamp: string;
}
