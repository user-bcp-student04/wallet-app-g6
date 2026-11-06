import { Component, inject, signal } from '@angular/core';
import { SessionService } from '../services/session.service';

@Component({
  selector: 'app-config-panel',
  template: `
    <section class="panel" aria-labelledby="config-title">
      <h2 id="config-title">Configuración</h2>
      <label>
        URL base del grupo
        <input type="text" [value]="baseUrlDraft()" (input)="baseUrlDraft.set(valueOf($event))" />
      </label>
      <button type="button" (click)="applyBaseUrl()">Aplicar URL</button>
      @if (baseUrlError()) {
        <p class="error" role="alert">{{ baseUrlError() }}</p>
      }
      <label>
        Latencia simulada (0 a 5000 ms)
        <input
          type="text"
          inputmode="numeric"
          [value]="session.latencyInput()"
          (input)="session.setLatencyInput(valueOf($event))"
        />
      </label>
      @if (session.latencyError()) {
        <p class="error" role="alert">{{ session.latencyError() }} No se llamará a la API hasta corregirla.</p>
      }
    </section>
  `,
})
export class ConfigPanel {
  protected readonly session = inject(SessionService);
  protected readonly baseUrlDraft = signal(this.session.baseUrl());
  protected readonly baseUrlError = signal<string | null>(null);

  protected valueOf(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }

  protected applyBaseUrl(): void {
    this.baseUrlError.set(this.session.setBaseUrl(this.baseUrlDraft()));
  }
}
