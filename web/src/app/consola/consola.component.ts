// src/app/consola/consola.component.ts
import { Component, ElementRef, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { focusLater } from '../core/a11y';
import { ApiErrorView, HealthResponse, ScenarioItem, SupportCase } from '../core/api.models';
import { MockApiService } from '../core/mock-api.service';
import { SessionService } from '../core/session.service';

export type ServiceKey = 'health' | 'scenarios' | 'cases';
type ErrorKey = ServiceKey | 'reset';

interface ServiceDef {
  key: ServiceKey;
  method: 'GET';
  path: string;
  description: string;
}

@Component({
  selector: 'app-consola',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './consola.component.html',
})
export class ConsolaComponent {
  private readonly api = inject(MockApiService);
  private readonly session = inject(SessionService);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  readonly services: readonly ServiceDef[] = [
    { key: 'health', method: 'GET', path: '/health', description: 'Comprueba que el servicio responde.' },
    { key: 'scenarios', method: 'GET', path: '/scenarios', description: 'Lista los escenarios KYC disponibles.' },
    {
      key: 'cases',
      method: 'GET',
      path: '/support/cases',
      description: 'Lista tus verificaciones que requieren atención (no aprobadas).',
    },
  ];

  /** Servicio o acción en curso (null = ninguno). Evita ejecuciones duplicadas. */
  readonly running = signal<ErrorKey | null>(null);
  readonly errors = signal<Partial<Record<ErrorKey, ApiErrorView>>>({});

  readonly health = signal<HealthResponse | null>(null);
  readonly scenarios = signal<ScenarioItem[] | null>(null);
  readonly cases = signal<SupportCase[] | null>(null);

  readonly confirmingReset = signal(false);
  readonly resetDone = signal(false);

  ariaDisabled(): 'true' | null {
    return this.running() !== null ? 'true' : null;
  }

  async run(key: ServiceKey): Promise<void> {
    if (this.running() !== null) {
      return;
    }
    this.running.set(key);
    this.setError(key, null);
    try {
      switch (key) {
        case 'health':
          this.health.set(await firstValueFrom(this.api.health()));
          break;
        case 'scenarios':
          this.scenarios.set((await firstValueFrom(this.api.scenarios())).scenarios);
          break;
        case 'cases':
          this.cases.set((await firstValueFrom(this.api.supportCases())).cases);
          break;
      }
    } catch (error) {
      this.clearResult(key);
      this.setError(key, error as ApiErrorView);
    } finally {
      this.running.set(null);
    }
  }

  askReset(): void {
    if (this.running() !== null) {
      return;
    }
    this.resetDone.set(false);
    this.setError('reset', null);
    this.confirmingReset.set(true);
    focusLater(this.host.nativeElement, '#reset-confirm-text');
  }

  cancelReset(): void {
    this.confirmingReset.set(false);
    focusLater(this.host.nativeElement, '#reset-open');
  }

  async confirmReset(): Promise<void> {
    if (this.running() !== null) {
      return;
    }
    this.running.set('reset');
    this.setError('reset', null);
    try {
      await firstValueFrom(this.api.reset());
      this.session.resetProgress();
      this.health.set(null);
      this.scenarios.set(null);
      this.cases.set(null);
      this.resetDone.set(true);
    } catch (error) {
      this.setError('reset', error as ApiErrorView);
    } finally {
      this.running.set(null);
      this.confirmingReset.set(false);
      focusLater(this.host.nativeElement, '#reset-open');
    }
  }

  private clearResult(key: ServiceKey): void {
    if (key === 'health') {
      this.health.set(null);
    } else if (key === 'scenarios') {
      this.scenarios.set(null);
    } else {
      this.cases.set(null);
    }
  }

  private setError(key: ErrorKey, error: ApiErrorView | null): void {
    this.errors.update((current) => {
      const next = { ...current };
      if (error) {
        next[key] = error;
      } else {
        delete next[key];
      }
      return next;
    });
  }
}
