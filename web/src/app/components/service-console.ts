import { Component, computed, inject, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiResult } from '../models/mock.models';
import { MockApiService } from '../services/mock-api.service';
import { OnboardingEventsService } from '../services/onboarding-events.service';
import { ReadableError, describeError } from '../services/error-messages';
import { SessionService } from '../services/session.service';

type ServiceKey = 'health' | 'scenarios' | 'createKyc' | 'getKyc' | 'decision' | 'getWallet' | 'supportCases' | 'reset';

interface ServiceDefinition {
  key: ServiceKey;
  label: string;
}

export const SERVICES: readonly ServiceDefinition[] = [
  { key: 'health', label: 'GET /health' },
  { key: 'scenarios', label: 'GET /scenarios' },
  { key: 'createKyc', label: 'POST /kyc/verifications' },
  { key: 'getKyc', label: 'GET /kyc/verifications/{id}' },
  { key: 'decision', label: 'POST /kyc/verifications/{id}/decision' },
  { key: 'getWallet', label: 'GET /wallets/{id}' },
  { key: 'supportCases', label: 'GET /support/cases' },
  { key: 'reset', label: 'POST /control/reset' },
];

@Component({
  selector: 'app-service-console',
  template: `
    <section class="panel" aria-labelledby="console-title">
      <h2 id="console-title">Consola de servicios</h2>
      <div class="services">
        @for (service of services; track service.key) {
          <button type="button" [class.current]="selected() === service.key" (click)="selected.set(service.key)">
            {{ service.label }}
          </button>
        }
      </div>

      @switch (selected()) {
        @case ('createKyc') {
          <label>
            document
            <input type="text" [value]="document()" (input)="document.set(valueOf($event))" />
          </label>
          <label>
            scenario
            <select [value]="scenario()" (change)="scenario.set(valueOf($event))">
              @for (option of scenarioOptions(); track option) {
                <option [value]="option" [selected]="option === scenario()">{{ option }}</option>
              }
            </select>
          </label>
        }
        @case ('getKyc') {
          <label>
            id (verificación)
            <input type="text" [value]="kycId()" (input)="kycIdOverride.set(valueOf($event))" />
          </label>
        }
        @case ('decision') {
          <label>
            id (verificación)
            <input type="text" [value]="kycId()" (input)="kycIdOverride.set(valueOf($event))" />
          </label>
          <label>
            decision
            <select [value]="decision()" (change)="decision.set(valueOf($event))">
              <option value="ACTIVE" [selected]="decision() === 'ACTIVE'">ACTIVE</option>
              <option value="REJECTED" [selected]="decision() === 'REJECTED'">REJECTED</option>
            </select>
          </label>
        }
        @case ('getWallet') {
          <label>
            id (wallet)
            <input type="text" [value]="walletId()" (input)="walletIdOverride.set(valueOf($event))" />
          </label>
        }
      }

      <button type="button" [disabled]="running()" (click)="run()">Ejecutar</button>

      @if (result(); as r) {
        <div class="result" aria-live="polite">
          <p><strong>{{ r.method }} {{ r.path }}</strong></p>
          <p>Cuerpo enviado: <code>{{ pretty(r.requestBody) }}</code></p>
          <p>Código HTTP: {{ r.blockedByClient ? 'no enviado' : r.status }} · Tiempo: {{ r.elapsedMs }} ms</p>
          <pre>{{ pretty(r.body ?? r.error) }}</pre>
        </div>
      }
      @if (readable(); as e) {
        <p class="error" role="alert">{{ e.message }} {{ e.action }}</p>
      }
    </section>
  `,
})
export class ServiceConsole {
  private readonly api = inject(MockApiService);
  private readonly events = inject(OnboardingEventsService);
  protected readonly session = inject(SessionService);

  protected readonly services = SERVICES;
  protected readonly selected = signal<ServiceKey>('health');
  protected readonly document = signal('TEST-001');
  protected readonly scenario = signal('APPROVED');
  protected readonly decision = signal('ACTIVE');
  protected readonly kycIdOverride = signal<string | null>(null);
  protected readonly walletIdOverride = signal<string | null>(null);
  protected readonly result = signal<ApiResult<unknown> | null>(null);
  protected readonly readable = signal<ReadableError | null>(null);
  protected readonly running = signal(false);

  protected readonly kycId = computed(() => this.kycIdOverride() ?? this.session.verificationId() ?? '');
  protected readonly walletId = computed(() => this.walletIdOverride() ?? this.session.walletId() ?? '');
  protected readonly scenarioOptions = computed(() =>
    this.session.scenarios().length > 0 ? this.session.scenarios() : ['APPROVED', 'REJECTED', 'MANUAL_REVIEW', 'UNAVAILABLE'],
  );

  protected valueOf(event: Event): string {
    return (event.target as HTMLInputElement | HTMLSelectElement).value;
  }

  protected pretty(value: unknown): string {
    return value === null || value === undefined ? '—' : JSON.stringify(value, null, 2);
  }

  protected run(): void {
    const call = this.buildCall();
    if (call === null) return;
    this.running.set(true);
    this.readable.set(null);
    call.subscribe((result) => {
      this.running.set(false);
      this.result.set(result);
      this.readable.set(result.ok ? null : describeError(result));
      if (result.ok && result.path === '/control/reset') {
        this.session.clearIdentifiers();
        this.events.clear();
        this.kycIdOverride.set(null);
        this.walletIdOverride.set(null);
      }
    });
  }

  private buildCall(): Observable<ApiResult<unknown>> | null {
    switch (this.selected()) {
      case 'health':
        return this.api.health();
      case 'scenarios':
        return this.api.scenarios();
      case 'createKyc':
        return this.api.createVerification({
          documentType: 'TEST',
          document: this.document(),
          scenario: this.scenario(),
        });
      case 'getKyc':
        return this.api.getVerification(this.kycId());
      case 'decision':
        return this.api.decide(this.kycId(), { decision: this.decision() === 'REJECTED' ? 'REJECTED' : 'ACTIVE' });
      case 'getWallet':
        return this.api.getWallet(this.walletId());
      case 'supportCases':
        return this.api.supportCases();
      case 'reset':
        return window.confirm('Esto borra TODOS los datos del grupo y repone wallet-demo. ¿Continuar?')
          ? this.api.reset()
          : null;
    }
  }
}
