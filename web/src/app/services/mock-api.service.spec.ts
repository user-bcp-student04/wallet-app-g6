import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { ApiResult } from '../models/mock.models';
import { describeError } from './error-messages';
import { MockApiService } from './mock-api.service';
import { SessionService } from './session.service';

const BASE = environment.mockBaseUrl;

function collect<T>(source: Observable<ApiResult<T>>): { result: ApiResult<T> | null } {
  const box: { result: ApiResult<T> | null } = { result: null };
  source.subscribe((value) => (box.result = value));
  return box;
}

describe('MockApiService', () => {
  let api: MockApiService;
  let http: HttpTestingController;
  let session: SessionService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    api = TestBed.inject(MockApiService);
    http = TestBed.inject(HttpTestingController);
    session = TestBed.inject(SessionService);
  });

  afterEach(() => http.verify());

  describe('GET /health', () => {
    it('devuelve 200 y envía X-Mock-Latency-Ms', () => {
      session.setLatencyInput('250');
      const box = collect(api.health());
      const req = http.expectOne(`${BASE}/health`);
      expect(req.request.headers.get('X-Mock-Latency-Ms')).toBe('250');
      req.flush({ status: 'ok', storage: 'memory' });
      expect(box.result?.status).toBe(200);
      expect(box.result?.body?.status).toBe('ok');
    });

    it('no envía X-Mock-Latency-Ms cuando la latencia es 0 (evita el preflight CORS)', () => {
      collect(api.health());
      const req = http.expectOne(`${BASE}/health`);
      expect(req.request.headers.has('X-Mock-Latency-Ms')).toBe(false);
      req.flush({ status: 'ok', storage: 'memory' });
    });

    it('bloquea una latencia fuera de rango sin llamar a la API', () => {
      session.setLatencyInput('9999');
      const box = collect(api.health());
      http.expectNone(`${BASE}/health`);
      expect(box.result?.blockedByClient).toBe(true);
      expect(session.latencyError()).toContain('0 y 5000');
    });
  });

  describe('GET /scenarios', () => {
    it('devuelve 200 y llena la lista de escenarios KYC', () => {
      collect(api.scenarios());
      http.expectOne(`${BASE}/scenarios`).flush({
        kyc: ['APPROVED', 'REJECTED', 'MANUAL_REVIEW', 'UNAVAILABLE'],
        payments: [],
        settlements: [],
      });
      expect(session.scenarios()).toContain('MANUAL_REVIEW');
    });

    it('con error de red devuelve un mensaje legible', () => {
      const box = collect(api.scenarios());
      http.expectOne(`${BASE}/scenarios`).error(new ProgressEvent('error'));
      expect(box.result?.status).toBe(0);
      expect(describeError(box.result as ApiResult<unknown>).message).toContain('No se pudo contactar');
    });
  });

  describe('POST /kyc/verifications', () => {
    it.each([
      ['APPROVED', 'ACTIVE'],
      ['REJECTED', 'REJECTED'],
      ['MANUAL_REVIEW', 'PENDING'],
    ] as const)('201 en %s deja la wallet %s y recuerda los identificadores', (scenario, status) => {
      const box = collect(api.createVerification({ documentType: 'TEST', document: 'TEST-001', scenario }));
      const req = http.expectOne(`${BASE}/kyc/verifications`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ documentType: 'TEST', document: 'TEST-001', scenario });
      req.flush({ id: 'kyc-1', wallet_id: 'w-1', scenario, status }, { status: 201, statusText: 'Created' });
      expect(box.result?.status).toBe(201);
      expect(session.verificationId()).toBe('kyc-1');
      expect(session.walletId()).toBe('w-1');
      expect(session.walletStatus()).toBe(status);
    });

    it('503 KYC_UNAVAILABLE no crea wallet y permite reintentar', () => {
      const box = collect(api.createVerification({ documentType: 'TEST', document: 'TEST-001', scenario: 'UNAVAILABLE' }));
      http.expectOne(`${BASE}/kyc/verifications`).flush({ error: 'KYC_UNAVAILABLE' }, { status: 503, statusText: 'Unavailable' });
      expect(box.result?.error?.error).toBe('KYC_UNAVAILABLE');
      expect(session.walletId()).toBeNull();
      expect(describeError(box.result as ApiResult<unknown>).action).toContain('Reintenta');
    });

    it('400 por documento sin prefijo TEST- se muestra con acción sugerida', () => {
      const box = collect(api.createVerification({ documentType: 'TEST', document: '12345678' }));
      http.expectOne(`${BASE}/kyc/verifications`).flush({ error: 'INVALID_DOCUMENT' }, { status: 400, statusText: 'Bad Request' });
      expect(box.result?.status).toBe(400);
      expect(describeError(box.result as ApiResult<unknown>).action).toContain('Corrige');
    });
  });

  describe('GET /kyc/verifications/{id}', () => {
    it('200 devuelve la verificación', () => {
      const box = collect(api.getVerification('kyc-1'));
      http.expectOne(`${BASE}/kyc/verifications/kyc-1`).flush({ id: 'kyc-1', wallet_id: 'w-1', scenario: 'APPROVED', status: 'ACTIVE' });
      expect(box.result?.body?.wallet_id).toBe('w-1');
    });

    it('404 NOT_FOUND', () => {
      const box = collect(api.getVerification('nope'));
      http.expectOne(`${BASE}/kyc/verifications/nope`).flush({ error: 'NOT_FOUND' }, { status: 404, statusText: 'Not Found' });
      expect(box.result?.error?.error).toBe('NOT_FOUND');
    });
  });

  describe('POST /kyc/verifications/{id}/decision', () => {
    it('200 sobre PENDING actualiza el estado de la wallet', () => {
      session.rememberVerification('kyc-1', 'w-1', 'PENDING');
      collect(api.decide('kyc-1', { decision: 'ACTIVE' }));
      const req = http.expectOne(`${BASE}/kyc/verifications/kyc-1/decision`);
      expect(req.request.body).toEqual({ decision: 'ACTIVE' });
      req.flush({ id: 'kyc-1', wallet_id: 'w-1', scenario: 'MANUAL_REVIEW', status: 'ACTIVE' });
      expect(session.walletStatus()).toBe('ACTIVE');
    });

    it('409 DECISION_CONFLICT al cambiar una decisión final', () => {
      const box = collect(api.decide('kyc-1', { decision: 'REJECTED' }));
      http.expectOne(`${BASE}/kyc/verifications/kyc-1/decision`).flush({ error: 'DECISION_CONFLICT' }, { status: 409, statusText: 'Conflict' });
      expect(describeError(box.result as ApiResult<unknown>).message).toContain('DECISION_CONFLICT');
    });
  });

  describe('GET /wallets/{id}', () => {
    it('200 con saldos en 0 y moneda PEN', () => {
      const box = collect(api.getWallet('w-1'));
      http.expectOne(`${BASE}/wallets/w-1`).flush({ id: 'w-1', status: 'ACTIVE', balance: 0, reserved: 0, available: 0, currency: 'PEN' });
      expect(box.result?.body).toMatchObject({ balance: 0, reserved: 0, available: 0, currency: 'PEN' });
    });

    it('404 NOT_FOUND', () => {
      const box = collect(api.getWallet('nope'));
      http.expectOne(`${BASE}/wallets/nope`).flush({ error: 'NOT_FOUND' }, { status: 404, statusText: 'Not Found' });
      expect(box.result?.status).toBe(404);
    });
  });

  describe('GET /support/cases', () => {
    it('200 con un caso KYC_REVIEW OPEN', () => {
      const box = collect(api.supportCases());
      http.expectOne(`${BASE}/support/cases`).flush([{ id: 'c-1', resource: 'kyc-1', reason: 'KYC_REVIEW', status: 'OPEN' }]);
      expect(box.result?.body?.[0]).toMatchObject({ reason: 'KYC_REVIEW', status: 'OPEN' });
    });

    it('200 con lista vacía', () => {
      const box = collect(api.supportCases());
      http.expectOne(`${BASE}/support/cases`).flush([]);
      expect(box.result?.body).toEqual([]);
    });
  });

  describe('POST /control/reset', () => {
    it('200 devuelve reset true', () => {
      const box = collect(api.reset());
      http.expectOne(`${BASE}/control/reset`).flush({ reset: true });
      expect(box.result?.body?.reset).toBe(true);
    });
  });

  describe('pagos y QR', () => {
    const PAYMENT = { id: 'pay_1', wallet_id: 'wallet-demo', recipient: 'contact-demo', amount: 1500, status: 'PENDING', scenario: 'APPROVED', idem: 'k' };

    it('POST /payments envía Idempotency-Key y devuelve 202', () => {
      const box = collect(api.createPayment({ walletId: 'wallet-demo', recipient: 'contact-demo', amountCents: 1500, currency: 'PEN' }, 'key-1'));
      const req = http.expectOne(`${BASE}/payments`);
      expect(req.request.headers.get('Idempotency-Key')).toBe('key-1');
      req.flush(PAYMENT, { status: 202, statusText: 'Accepted' });
      expect(box.result?.status).toBe(202);
    });

    it('POST /payments con 409 INSUFFICIENT_FUNDS', () => {
      const box = collect(api.createPayment({ walletId: 'wallet-demo', recipient: 'contact-demo', amountCents: 999999999, currency: 'PEN' }, 'key-2'));
      http.expectOne(`${BASE}/payments`).flush({ error: 'INSUFFICIENT_FUNDS' }, { status: 409, statusText: 'Conflict' });
      expect(describeError(box.result as ApiResult<unknown>).message).toContain('Saldo insuficiente');
    });

    it('POST /payments/{id}/resolve devuelve el pago resuelto', () => {
      const box = collect(api.resolvePayment('pay_1'));
      http.expectOne(`${BASE}/payments/pay_1/resolve`).flush({ ...PAYMENT, status: 'SUCCEEDED' });
      expect(box.result?.body).toMatchObject({ status: 'SUCCEEDED' });
    });

    it('GET /payments filtra por walletId', () => {
      const box = collect(api.listPayments('wallet-demo'));
      http.expectOne(`${BASE}/payments?walletId=wallet-demo`).flush([PAYMENT]);
      expect(box.result?.body).toHaveLength(1);
    });

    it('POST /qrs y POST /qrs/resolve', () => {
      collect(api.createQr({ merchantId: 'merchant-demo' }));
      http.expectOne(`${BASE}/qrs`).flush({ id: 'qr_1', payload: 'qrmock:qr_1', amountCents: null, currency: 'PEN' }, { status: 201, statusText: 'Created' });
      const resolved = collect(api.resolveQr('qrmock:qr_1'));
      const req = http.expectOne(`${BASE}/qrs/resolve`);
      expect(req.request.body).toEqual({ payload: 'qrmock:qr_1' });
      req.flush({ merchantId: 'merchant-demo', merchantName: 'Comercio de prueba', amountCents: null, currency: 'PEN' });
      expect(resolved.result?.body?.merchantName).toBe('Comercio de prueba');
    });
  });

  describe('manejador de errores común', () => {
    it.each([
      [400, undefined, 'datos inválidos'],
      [404, 'NOT_FOUND', 'No se encontró'],
      [409, 'DECISION_CONFLICT', 'decisión final'],
      [413, undefined, 'demasiado grande'],
      [429, 'GROUP_LIMIT_RESET_REQUIRED', 'límite'],
      [503, 'KYC_UNAVAILABLE', 'no está disponible'],
    ])('HTTP %s produce un mensaje accionable', (status, code, text) => {
      const readable = describeError({
        method: 'GET',
        path: '/x',
        requestBody: null,
        status,
        ok: false,
        body: null,
        error: code ? { error: code } : null,
        elapsedMs: 1,
        blockedByClient: false,
      });
      expect(readable.message).toContain(text);
      expect(readable.action.length).toBeGreaterThan(0);
    });

    it('429 GROUP_LIMIT_RESET_REQUIRED indica reiniciar el grupo', () => {
      const readable = describeError({
        method: 'POST',
        path: '/kyc/verifications',
        requestBody: null,
        status: 429,
        ok: false,
        body: null,
        error: { error: 'GROUP_LIMIT_RESET_REQUIRED' },
        elapsedMs: 1,
        blockedByClient: false,
      });
      expect(readable.action).toContain('Reinicia el grupo');
    });
  });
});
