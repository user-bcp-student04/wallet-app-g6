// src/app/onboarding/onboarding.component.ts
import { DatePipe } from '@angular/common';
import { Component, ElementRef, OnInit, inject, signal } from '@angular/core';
import { AbstractControl, NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { focusFirstInvalid, focusLater } from '../core/a11y';
import {
  ApiErrorView,
  KycDecision,
  KycScenario,
  OnboardingStateResponse,
  ScenarioItem,
  StepId,
  StepStatus,
  VerificationResponse,
  VerificationStatus,
  WalletStatus,
} from '../core/api.models';
import { documentErrorMessage, testDocumentValidator } from '../core/document.validator';
import {
  STEP_LABELS,
  STEP_STATUS_LABELS,
  VERIFICATION_STATUS_LABELS,
  WALLET_STATUS_LABELS,
} from '../core/labels';
import { MockApiService } from '../core/mock-api.service';
import { SessionService } from '../core/session.service';

const VERIFICATION_MESSAGES: Record<VerificationStatus, string> = {
  APPROVED: 'Verificación aprobada. Completa el paso de verificación para continuar.',
  PENDING: 'Verificación pendiente. Registra una decisión o actualiza el estado.',
  REJECTED: 'Verificación rechazada. Crea una nueva con un documento TEST- válido.',
  EXPIRED: 'Verificación expirada. Crea una nueva verificación.',
};

@Component({
  selector: 'app-onboarding',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe],
  templateUrl: './onboarding.component.html',
})
export class OnboardingComponent implements OnInit {
  private readonly api = inject(MockApiService);
  private readonly session = inject(SessionService);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  readonly loading = signal(true);
  readonly loadError = signal<ApiErrorView | null>(null);
  readonly state = signal<OnboardingStateResponse | null>(null);

  readonly scenarios = signal<ScenarioItem[]>([]);
  readonly scenariosLoading = signal(false);
  readonly scenariosError = signal<ApiErrorView | null>(null);

  /** Acción en curso (null = ninguna). Evita envíos duplicados. */
  readonly busy = signal<string | null>(null);
  readonly actionError = signal<ApiErrorView | null>(null);
  readonly success = signal<string | null>(null);

  readonly verification = this.session.verification;

  readonly registroForm = this.fb.group({
    document_number: this.fb.control('', testDocumentValidator),
  });

  readonly kycForm = this.fb.group({
    document_number: this.fb.control('', testDocumentValidator),
    scenario: this.fb.control<KycScenario | ''>('', Validators.required),
  });

  ngOnInit(): void {
    void this.load();
  }

  // ---------- Etiquetas y ayudas de plantilla ----------
  stepLabel(id: StepId): string {
    return STEP_LABELS[id] ?? id;
  }

  stepStatusLabel(status: StepStatus): string {
    return STEP_STATUS_LABELS[status] ?? status;
  }

  walletLabel(status: WalletStatus): string {
    return WALLET_STATUS_LABELS[status] ?? status;
  }

  verificationLabel(status: VerificationStatus): string {
    return VERIFICATION_STATUS_LABELS[status] ?? status;
  }

  docError(control: AbstractControl): string | null {
    return control.invalid && (control.touched || control.dirty)
      ? documentErrorMessage(control.errors)
      : null;
  }

  scenarioInvalid(): boolean {
    const control = this.kycForm.controls.scenario;
    return control.invalid && (control.touched || control.dirty);
  }

  ariaDisabled(): 'true' | null {
    return this.busy() !== null ? 'true' : null;
  }

  // ---------- Carga ----------
  async load(): Promise<void> {
    this.loading.set(true);
    this.loadError.set(null);
    try {
      this.applyState(await firstValueFrom(this.api.getOnboarding()));
    } catch (error) {
      this.loadError.set(error as ApiErrorView);
      this.loading.set(false);
      return;
    }
    this.loading.set(false);
    await Promise.all([this.loadScenarios(), this.recoverPending()]);
  }

  async loadScenarios(): Promise<void> {
    if (this.scenariosLoading()) {
      return;
    }
    this.scenariosLoading.set(true);
    this.scenariosError.set(null);
    try {
      this.scenarios.set((await firstValueFrom(this.api.scenarios())).scenarios);
    } catch (error) {
      this.scenariosError.set(error as ApiErrorView);
    } finally {
      this.scenariosLoading.set(false);
    }
  }

  /** Tras recargar con KYC pendiente, recupera la verificación pendiente más reciente. */
  private async recoverPending(): Promise<void> {
    if (this.state()?.wallet_status !== 'KYC_PENDING' || this.verification()) {
      return;
    }
    try {
      const cases = await firstValueFrom(this.api.supportCases());
      const pending = [...cases.cases].reverse().find((item) => item.status === 'PENDING');
      if (pending) {
        const detail = await firstValueFrom(
          this.api.getVerification({ verification_id: pending.verification_id }),
        );
        this.session.setVerification(detail);
      }
    } catch (error) {
      this.actionError.set(error as ApiErrorView);
    }
  }

  // ---------- Acciones ----------
  async submitRegistro(): Promise<void> {
    if (this.busy() !== null) {
      return;
    }
    if (this.registroForm.invalid) {
      this.registroForm.markAllAsTouched();
      focusFirstInvalid(this.host.nativeElement);
      return;
    }
    const documentNumber = this.registroForm.controls.document_number.value;
    await this.run(
      'registro',
      () => firstValueFrom(this.api.submitStep({ step_id: 'registro', document_number: documentNumber })),
      (state) => {
        this.applyState(state);
        this.success.set('Registro completado. Continúa con la verificación KYC.');
        this.focusStepHeading();
      },
    );
  }

  async createVerification(): Promise<void> {
    if (this.busy() !== null) {
      return;
    }
    if (this.kycForm.invalid) {
      this.kycForm.markAllAsTouched();
      focusFirstInvalid(this.host.nativeElement);
      return;
    }
    const value = this.kycForm.getRawValue();
    await this.run(
      'crear-kyc',
      async () => {
        const created = await firstValueFrom(
          this.api.createVerification({
            document_number: value.document_number,
            scenario: value.scenario as KycScenario,
          }),
        );
        const state = await firstValueFrom(this.api.getOnboarding()).catch(() => null);
        return { created, state };
      },
      ({ created, state }) => {
        this.session.setVerification(created);
        if (state) {
          this.applyState(state);
        }
        this.success.set(VERIFICATION_MESSAGES[created.status]);
      },
    );
  }

  async decide(decision: KycDecision): Promise<void> {
    const current = this.verification();
    if (this.busy() !== null || !current) {
      return;
    }
    await this.run(
      'decidir-kyc',
      async () => {
        const decided = await firstValueFrom(
          this.api.decideVerification({ verification_id: current.verification_id, decision }),
        );
        const state = await firstValueFrom(this.api.getOnboarding()).catch(() => null);
        return { decided, state };
      },
      ({ decided, state }) => {
        this.session.setVerification(decided);
        if (state) {
          this.applyState(state);
        }
        this.success.set(
          decision === 'APPROVED'
            ? 'Decisión registrada: verificación aprobada.'
            : 'Decisión registrada: verificación rechazada.',
        );
      },
    );
  }

  async refreshVerification(): Promise<void> {
    const current = this.verification();
    if (this.busy() !== null || !current) {
      return;
    }
    await this.run(
      'actualizar-kyc',
      async () => {
        const updated = await firstValueFrom(
          this.api.getVerification({ verification_id: current.verification_id }),
        );
        const state = await firstValueFrom(this.api.getOnboarding()).catch(() => null);
        return { updated, state };
      },
      ({ updated, state }) => {
        this.session.setVerification(updated);
        if (state) {
          this.applyState(state);
        }
        this.success.set('Estado actualizado.');
      },
    );
  }

  async completeStep(step: 'kyc' | 'activacion'): Promise<void> {
    if (this.busy() !== null) {
      return;
    }
    await this.run(
      `paso-${step}`,
      () => firstValueFrom(this.api.submitStep({ step_id: step })),
      (state) => {
        this.applyState(state);
        this.success.set(
          step === 'kyc'
            ? 'Verificación completada. Ya puedes activar tu wallet.'
            : '¡Wallet activa! Ya puedes acceder a pagos de bajo monto.',
        );
        this.focusStepHeading();
      },
    );
  }

  // ---------- Internos ----------
  private applyState(state: OnboardingStateResponse): void {
    this.state.set(state);
    this.session.setWallet(state);
  }

  private focusStepHeading(): void {
    focusLater(this.host.nativeElement, '[data-step-heading]');
  }

  private async run<T>(key: string, action: () => Promise<T>, onSuccess: (result: T) => void): Promise<void> {
    if (this.busy() !== null) {
      return;
    }
    this.busy.set(key);
    this.actionError.set(null);
    this.success.set(null);
    try {
      onSuccess(await action());
    } catch (error) {
      this.actionError.set(error as ApiErrorView);
    } finally {
      this.busy.set(null);
    }
  }
}
