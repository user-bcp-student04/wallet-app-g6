// src/app/pagos/pagos.component.ts
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { ApiErrorView, OnboardingStateResponse } from '../core/api.models';
import { WALLET_STATUS_LABELS } from '../core/labels';
import { MockApiService } from '../core/mock-api.service';

@Component({
  selector: 'app-pagos',
  standalone: true,
  imports: [RouterLink],
  template: `
    <h1>Pagos de bajo monto</h1>

    @if (loading()) {
      <p role="status">Verificando el estado de tu wallet…</p>
    } @else if (error()) {
      <div role="alert" class="alert alert-error">
        <p><strong>Error:</strong> {{ error()!.message }}</p>
        <p class="hint">Código: {{ error()!.code }}</p>
        <button type="button" class="btn" (click)="load()">Reintentar</button>
      </div>
    } @else if (state()?.low_amount_payments_enabled) {
      <div role="status" class="alert alert-ok">
        <p><strong>Acceso habilitado.</strong> Tu wallet está activa y puedes realizar pagos de bajo monto.</p>
      </div>
      <p class="hint">
        El contrato de API aprobado no define endpoints de pagos, por lo que esta pantalla solo confirma el acceso.
      </p>
    } @else {
      <div role="alert" class="alert alert-error">
        <p>
          <strong>Acceso bloqueado.</strong> Estado actual de la wallet: {{ walletLabel() }}. Completa el
          onboarding para habilitar los pagos de bajo monto.
        </p>
      </div>
      <a routerLink="/onboarding" class="btn">Volver al onboarding</a>
    }
  `,
})
export class PagosComponent implements OnInit {
  private readonly api = inject(MockApiService);

  readonly loading = signal(true);
  readonly error = signal<ApiErrorView | null>(null);
  readonly state = signal<OnboardingStateResponse | null>(null);

  ngOnInit(): void {
    void this.load();
  }

  walletLabel(): string {
    const status = this.state()?.wallet_status;
    return status ? WALLET_STATUS_LABELS[status] : '';
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      this.state.set(await firstValueFrom(this.api.getOnboarding()));
    } catch (error) {
      this.error.set(error as ApiErrorView);
    } finally {
      this.loading.set(false);
    }
  }
}
