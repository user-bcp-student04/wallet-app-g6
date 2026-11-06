import { Component, OnInit, inject, signal } from '@angular/core';
import { ApiResult, Kyc, Wallet } from '../models/mock.models';
import { MockApiService } from '../services/mock-api.service';
import { OnboardingEventsService } from '../services/onboarding-events.service';
import { ReadableError, describeError } from '../services/error-messages';
import { SessionService } from '../services/session.service';

export const ONBOARDING_STEPS = ['documento', 'escenario', 'verificacion', 'resultado'] as const;
const DOCUMENT_PREFIX = 'TEST-';

@Component({
  selector: 'app-onboarding-flow',
  template: `
    <section class="panel" aria-labelledby="flow-title">
      <h2 id="flow-title">Onboarding guiado</h2>
      <ol class="steps" aria-label="Pasos del onboarding">
        @for (name of steps; track name; let i = $index) {
          <li [attr.aria-current]="i === stepIndex() ? 'step' : null" [class.current]="i === stepIndex()">
            {{ i + 1 }}. {{ name }}
          </li>
        }
      </ol>
      <p>Paso actual: {{ steps[stepIndex()] }}</p>

      @switch (steps[stepIndex()]) {
        @case ('documento') {
          <label>
            Documento ficticio (prefijo TEST-)
            <input type="text" [value]="document()" (input)="document.set(valueOf($event))" />
          </label>
          <button type="button" (click)="completeDocument()">Continuar</button>
        }
        @case ('escenario') {
          @if (session.scenarios().length === 0) {
            <p>Aún no se cargaron los escenarios KYC.</p>
            <button type="button" (click)="loadScenarios()">Cargar escenarios</button>
          } @else {
            <label>
              Escenario KYC
              <select [value]="scenario()" (change)="scenario.set(valueOf($event))">
                @for (option of session.scenarios(); track option) {
                  <option [value]="option" [selected]="option === scenario()">{{ option }}</option>
                }
              </select>
            </label>
            <button type="button" (click)="completeScenario()">Continuar</button>
          }
        }
        @case ('verificacion') {
          <p>Documento: {{ document() }} · Escenario: {{ scenario() }}</p>
          <button type="button" [disabled]="loading()" (click)="submit()">
            {{ loading() ? 'Enviando...' : 'Enviar verificación' }}
          </button>
        }
        @case ('resultado') {
          @if (verification(); as kyc) {
            <dl>
              <dt>id</dt><dd>{{ kyc.id }}</dd>
              <dt>wallet_id</dt><dd>{{ kyc.wallet_id }}</dd>
              <dt>scenario</dt><dd>{{ kyc.scenario }}</dd>
              <dt>status</dt><dd>{{ session.walletStatus() ?? kyc.status }}</dd>
            </dl>
          }
          @if (wallet(); as w) {
            <p>
              Wallet {{ w.id }}: saldo {{ w.balance }}, reservado {{ w.reserved }}, disponible {{ w.available }}
              {{ w.currency }} (céntimos). La wallet nueva no tiene fondos y esta consola no ofrece recarga.
            </p>
          }
          @switch (session.walletStatus()) {
            @case ('ACTIVE') {
              <p>Tu cuenta está activa.</p>
            }
            @case ('REJECTED') {
              <p class="error">La cuenta fue rechazada.</p>
            }
            @case ('PENDING') {
              <p>La verificación está en revisión manual: falta una decisión del operador.</p>
            }
          }
          <button type="button" [disabled]="session.walletStatus() !== 'ACTIVE'">
            Ir a pagos de bajo monto
          </button>
          @if (session.walletStatus() !== 'ACTIVE') {
            <p>El acceso a pagos está deshabilitado: solo una wallet ACTIVE puede pagar.</p>
          }
          <button type="button" (click)="restart()">Iniciar otro onboarding</button>
        }
      }

      @if (formError()) {
        <p class="error" role="alert">{{ formError() }}</p>
      }
      @if (apiError(); as e) {
        <p class="error" role="alert">{{ e.message }} {{ e.action }}</p>
      }
    </section>
  `,
})
export class OnboardingFlow implements OnInit {
  protected readonly session = inject(SessionService);
  private readonly api = inject(MockApiService);
  private readonly events = inject(OnboardingEventsService);

  protected readonly steps = ONBOARDING_STEPS;
  protected readonly stepIndex = signal(0);
  protected readonly document = signal('');
  protected readonly scenario = signal('APPROVED');
  protected readonly formError = signal<string | null>(null);
  protected readonly apiError = signal<ReadableError | null>(null);
  protected readonly loading = signal(false);
  protected readonly verification = signal<Kyc | null>(null);
  protected readonly wallet = signal<Wallet | null>(null);
  private flowId = '';

  ngOnInit(): void {
    this.restart();
  }

  protected valueOf(event: Event): string {
    return (event.target as HTMLInputElement | HTMLSelectElement).value;
  }

  protected restart(): void {
    this.flowId = crypto.randomUUID();
    this.stepIndex.set(0);
    this.document.set('');
    this.scenario.set('APPROVED');
    this.verification.set(null);
    this.wallet.set(null);
    this.formError.set(null);
    this.apiError.set(null);
    this.events.record('STARTED', this.flowId);
    if (this.session.scenarios().length === 0) this.loadScenarios();
  }

  protected loadScenarios(): void {
    this.api.scenarios().subscribe((result) => this.apiError.set(result.ok ? null : describeError(result)));
  }

  protected completeDocument(): void {
    const value = this.document().trim();
    if (value === '') {
      this.formError.set('Ingresa el documento para continuar.');
    } else if (!value.startsWith(DOCUMENT_PREFIX) || value.length === DOCUMENT_PREFIX.length) {
      this.formError.set('Solo se admiten documentos ficticios con prefijo TEST- (por ejemplo TEST-001).');
    } else {
      this.document.set(value);
      this.advance('documento');
    }
  }

  protected completeScenario(): void {
    if (!this.session.scenarios().includes(this.scenario())) {
      this.formError.set('Elige un escenario de la lista.');
      return;
    }
    this.advance('escenario');
  }

  protected submit(): void {
    this.loading.set(true);
    this.apiError.set(null);
    this.api
      .createVerification({ documentType: 'TEST', document: this.document(), scenario: this.scenario() })
      .subscribe((result) => {
        this.loading.set(false);
        if (!result.ok || !result.body) {
          this.apiError.set(describeError(result));
          return;
        }
        const kyc = result.body;
        this.verification.set(kyc);
        this.advance('verificacion');
        this.api.getWallet(kyc.wallet_id).subscribe((walletResult: ApiResult<Wallet>) => this.wallet.set(walletResult.body));
        this.events.record('CLOSED', this.flowId, { outcome: kyc.status, verificationId: kyc.id });
      });
  }

  private advance(step: string): void {
    this.formError.set(null);
    this.apiError.set(null);
    this.events.record('STEP_COMPLETED', this.flowId, { step });
    this.stepIndex.update((index) => index + 1);
  }
}
