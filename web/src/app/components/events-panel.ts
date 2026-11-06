import { Component, computed, inject, signal } from '@angular/core';
import { OnboardingEventsService } from '../services/onboarding-events.service';

@Component({
  selector: 'app-events-panel',
  template: `
    <section class="panel" aria-labelledby="events-title">
      <h2 id="events-title">Eventos de onboarding</h2>
      <p>
        Duración de la última sesión cerrada:
        {{ lastDuration() === null ? '—' : lastDuration() + ' s' }} · Mediana:
        {{ median() === null ? '—' : median() + ' s' }}
      </p>
      <ul>
        @for (event of events.events(); track $index) {
          <li>{{ event.timestamp }} · {{ event.type }} · {{ event.userId }}{{ event.step ? ' · ' + event.step : '' }}</li>
        } @empty {
          <li>Sin eventos.</li>
        }
      </ul>
      <h3>Salida mensual (eventos locales)</h3>
      <label>
        Gasto de adquisición atribuido, PEN (mes actual)
        <input type="text" inputmode="decimal" [value]="spendInput()" (input)="spendInput.set(valueOf($event))" />
      </label>
      <table>
        <thead>
          <tr><th>Mes</th><th>Nuevos usuarios activos</th><th>Gasto (PEN)</th><th>CAC (PEN)</th></tr>
        </thead>
        <tbody>
          @for (row of summary(); track row.month) {
            <tr>
              <td>{{ row.month }}</td>
              <td>{{ row.newActiveUsers }}</td>
              <td>{{ row.attributedSpendPen ?? '—' }}</td>
              <td>{{ row.cacPen ?? '—' }}</td>
            </tr>
          }
        </tbody>
      </table>
      <p>Los eventos viven en el navegador: no sirven para medir MAU y CAC reales.</p>
    </section>
  `,
})
export class EventsPanel {
  protected readonly events = inject(OnboardingEventsService);
  protected readonly spendInput = signal('');

  protected readonly lastDuration = computed(() => {
    const all = this.events.durations();
    return all.length === 0 ? null : Math.round(all[all.length - 1].ms / 1000);
  });
  protected readonly median = computed(() => {
    const ms = this.events.medianMs();
    return ms === null ? null : Math.round(ms / 1000);
  });
  protected readonly summary = computed(() => {
    const spend = Number(this.spendInput());
    const month = new Date().toISOString().slice(0, 7);
    return this.events.monthlySummary(this.spendInput().trim() !== '' && spend >= 0 ? { [month]: spend } : {});
  });

  protected valueOf(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }
}
