import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, map, of, tap } from 'rxjs';
import {
  ApiResult,
  DecisionRequest,
  Health,
  Kyc,
  KycRequest,
  MockError,
  Reset,
  Scenarios,
  SupportCase,
  Wallet,
} from '../models/mock.models';
import { SessionService } from './session.service';

@Injectable({ providedIn: 'root' })
export class MockApiService {
  private readonly http = inject(HttpClient);
  private readonly session = inject(SessionService);

  health(): Observable<ApiResult<Health>> {
    return this.execute<Health>('GET', '/health');
  }

  scenarios(): Observable<ApiResult<Scenarios>> {
    return this.execute<Scenarios>('GET', '/scenarios').pipe(
      tap((result) => {
        if (result.body) this.session.scenarios.set(result.body.kyc);
      }),
    );
  }

  createVerification(request: KycRequest): Observable<ApiResult<Kyc>> {
    return this.execute<Kyc>('POST', '/kyc/verifications', request).pipe(
      tap((result) => {
        if (result.body) this.session.rememberVerification(result.body.id, result.body.wallet_id, result.body.status);
      }),
    );
  }

  getVerification(id: string): Observable<ApiResult<Kyc>> {
    return this.execute<Kyc>('GET', `/kyc/verifications/${encodeURIComponent(id)}`);
  }

  decide(id: string, request: DecisionRequest): Observable<ApiResult<Kyc>> {
    return this.execute<Kyc>('POST', `/kyc/verifications/${encodeURIComponent(id)}/decision`, request).pipe(
      tap((result) => {
        if (result.body) this.session.rememberVerification(result.body.id, result.body.wallet_id, result.body.status);
      }),
    );
  }

  getWallet(id: string): Observable<ApiResult<Wallet>> {
    return this.execute<Wallet>('GET', `/wallets/${encodeURIComponent(id)}`).pipe(
      tap((result) => {
        if (result.body && result.body.id === this.session.walletId()) this.session.walletStatus.set(result.body.status);
      }),
    );
  }

  supportCases(): Observable<ApiResult<SupportCase[]>> {
    return this.execute<SupportCase[]>('GET', '/support/cases');
  }

  reset(): Observable<ApiResult<Reset>> {
    return this.execute<Reset>('POST', '/control/reset');
  }

  private execute<T>(method: 'GET' | 'POST', path: string, requestBody?: unknown): Observable<ApiResult<T>> {
    const base = { method, path, requestBody: requestBody ?? null };
    const latency = this.session.latencyMs();
    if (latency === null) {
      return of({
        ...base,
        status: 400,
        ok: false,
        body: null,
        error: { error: 'INVALID_MOCK_LATENCY' },
        elapsedMs: 0,
        blockedByClient: true,
      });
    }
    const started = performance.now();
    const headers = new HttpHeaders({ 'X-Mock-Latency-Ms': String(latency) });
    return this.http
      .request<T>(method, this.session.baseUrl() + path, { body: requestBody, headers, observe: 'response' })
      .pipe(
        map((response) => ({
          ...base,
          status: response.status,
          ok: true,
          body: response.body,
          error: null,
          elapsedMs: Math.round(performance.now() - started),
          blockedByClient: false,
        })),
        catchError((failure: HttpErrorResponse) =>
          of({
            ...base,
            status: failure.status,
            ok: false,
            body: null,
            error: this.toMockError(failure),
            elapsedMs: Math.round(performance.now() - started),
            blockedByClient: false,
          }),
        ),
      );
  }

  private toMockError(failure: HttpErrorResponse): MockError | null {
    const body: unknown = failure.error;
    if (typeof body === 'object' && body !== null && 'error' in body && typeof body.error === 'string') {
      return { error: body.error };
    }
    return failure.status === 0 ? { error: 'NETWORK_ERROR' } : null;
  }
}
