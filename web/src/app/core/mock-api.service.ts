// src/app/core/mock-api.service.ts
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Injectable, InjectionToken, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, throwError } from 'rxjs';

import {
  ApiErrorView,
  CreateVerificationRequest,
  DecideVerificationRequest,
  GetVerificationRequest,
  HealthResponse,
  OnboardingStateResponse,
  ResetResponse,
  ScenariosResponse,
  SubmitStepRequest,
  SupportCasesResponse,
  VerificationResponse,
} from './api.models';
import { SessionService } from './session.service';

/** Base del API. Vacío = mismo origen (proxy de desarrollo). */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  providedIn: 'root',
  factory: () => '',
});

const OWNER_HEADER = 'X-Owner-Id';

const DEFAULT_MESSAGES: Record<number, { code: string; message: string }> = {
  0: {
    code: 'NETWORK_ERROR',
    message: 'No se pudo conectar con el servicio. Revisa tu conexión e inténtalo de nuevo.',
  },
  401: { code: 'UNAUTHENTICATED', message: 'No se pudo identificar al usuario. Vuelve a identificarte.' },
  404: { code: 'NOT_FOUND', message: 'El recurso solicitado no existe.' },
  409: { code: 'CONFLICT', message: 'La acción no es posible en el estado actual. Actualiza e inténtalo de nuevo.' },
  413: { code: 'PAYLOAD_TOO_LARGE', message: 'Los datos enviados son demasiado grandes. Envía menos datos.' },
  422: { code: 'VALIDATION_ERROR', message: 'Los datos enviados no son válidos. Revísalos e inténtalo de nuevo.' },
  500: { code: 'INTERNAL_ERROR', message: 'Ocurrió un error interno. Inténtalo de nuevo más tarde.' },
};

/** Convierte cualquier error HTTP en {status, code, message}; prefiere el cuerpo del API. */
export function toApiErrorView(error: unknown): ApiErrorView {
  if (error instanceof HttpErrorResponse) {
    const body: unknown = error.error;
    if (
      typeof body === 'object' &&
      body !== null &&
      typeof (body as { code?: unknown }).code === 'string' &&
      typeof (body as { message?: unknown }).message === 'string'
    ) {
      const { code, message } = body as { code: string; message: string };
      return { status: error.status, code, message };
    }
    const fallback = DEFAULT_MESSAGES[error.status];
    if (fallback) {
      return { status: error.status, ...fallback };
    }
    return {
      status: error.status,
      code: 'HTTP_ERROR',
      message: 'No se pudo completar la solicitud. Inténtalo de nuevo.',
    };
  }
  return {
    status: -1,
    code: 'UNKNOWN_ERROR',
    message: 'Ocurrió un error inesperado. Inténtalo de nuevo.',
  };
}

/** Único punto de acceso al API. No contiene reglas de negocio. */
@Injectable()
export class MockApiService {
  private readonly http = inject(HttpClient);
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);
  private readonly base = inject(API_BASE_URL);

  health(): Observable<HealthResponse> {
    return this.get<HealthResponse>('/health');
  }

  scenarios(): Observable<ScenariosResponse> {
    return this.get<ScenariosResponse>('/scenarios');
  }

  supportCases(): Observable<SupportCasesResponse> {
    return this.get<SupportCasesResponse>('/support/cases');
  }

  createVerification(request: CreateVerificationRequest): Observable<VerificationResponse> {
    return this.post<VerificationResponse>('/kyc/verifications', {
      document_number: request.document_number,
      scenario: request.scenario,
    });
  }

  getVerification(request: GetVerificationRequest): Observable<VerificationResponse> {
    return this.get<VerificationResponse>(
      `/kyc/verifications/${encodeURIComponent(request.verification_id)}`,
    );
  }

  decideVerification(request: DecideVerificationRequest): Observable<VerificationResponse> {
    return this.post<VerificationResponse>(
      `/kyc/verifications/${encodeURIComponent(request.verification_id)}/decision`,
      { decision: request.decision },
    );
  }

  getOnboarding(): Observable<OnboardingStateResponse> {
    return this.get<OnboardingStateResponse>('/onboarding');
  }

  submitStep(request: SubmitStepRequest): Observable<OnboardingStateResponse> {
    const body: { document_number?: string } = {};
    if (request.document_number !== undefined) {
      body.document_number = request.document_number;
    }
    return this.post<OnboardingStateResponse>(
      `/onboarding/steps/${encodeURIComponent(request.step_id)}`,
      body,
    );
  }

  reset(): Observable<ResetResponse> {
    return this.post<ResetResponse>('/control/reset', null);
  }

  private get<T>(path: string): Observable<T> {
    return this.http
      .get<T>(`${this.base}${path}`, this.options())
      .pipe(catchError((error: unknown) => this.fail(error)));
  }

  private post<T>(path: string, body: unknown): Observable<T> {
    return this.http
      .post<T>(`${this.base}${path}`, body, this.options())
      .pipe(catchError((error: unknown) => this.fail(error)));
  }

  private options(): { headers?: HttpHeaders } {
    const owner = this.session.ownerId();
    return owner ? { headers: new HttpHeaders({ [OWNER_HEADER]: owner }) } : {};
  }

  private fail(error: unknown): Observable<never> {
    const view = toApiErrorView(error);
    if (view.code === 'UNAUTHENTICATED') {
      this.session.clear();
      void this.router.navigate(['/identificar']);
    }
    return throwError(() => view);
  }
}
