import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { environment } from '../../environments/environment';
import { Payment, PaymentStatus, Wallet } from '../models/mock.models';
import { ReadableError, describeError } from '../services/error-messages';
import { MockApiService } from '../services/mock-api.service';
import { RECIPIENT_LABELS, formatPen } from '../services/money';
import { TransferFlow } from './transfer-flow';

const STATUS_LABELS: Record<PaymentStatus, string> = {
  PENDING: 'Pendiente',
  SUCCEEDED: 'Exitoso',
  REJECTED: 'Rechazado',
  REVERSED: 'Revertido',
};
const MAX_MOVEMENTS = 5;

@Component({
  selector: 'app-dashboard-view',
  imports: [TransferFlow],
  template: `
    <div class="dashboard">
      @if (transferring()) {
        <app-transfer-flow
          [available]="wallet()?.available ?? 0"
          [initialMethod]="transferMethod()"
          (closed)="closeTransfer()"
        />
      } @else {
        <section class="card balance" aria-labelledby="balance-title">
          <h2 id="balance-title">Saldo disponible</h2>
          @if (wallet(); as w) {
            <p class="amount" data-testid="balance">{{ money(w.available) }}</p>
            <p class="hint">Saldo contable {{ money(w.balance) }} · Reservado {{ money(w.reserved) }}</p>
          } @else {
            <p class="amount">{{ loading() ? 'Cargando...' : '—' }}</p>
          }
          @if (loadError(); as e) {
            <p class="error" role="alert">{{ e.message }} {{ e.action }}</p>
            <button type="button" class="btn btn-outline" (click)="reload()">Reintentar</button>
          }
        </section>

        <section class="card actions" aria-labelledby="actions-title">
          <h2 id="actions-title">Transferir</h2>
          <div class="action-grid">
            <button type="button" class="btn btn-primary" (click)="startTransfer('contact')">Pago a contacto</button>
            <button type="button" class="btn btn-primary" (click)="startTransfer('qr')">Pago con QR</button>
          </div>
        </section>

        <section class="card movements" aria-labelledby="movements-title">
          <h2 id="movements-title">Últimos movimientos</h2>
          <ul class="movement-list">
            @for (p of recent(); track p.id) {
              <li>
                <span class="who">{{ label(p.recipient) }}<small>{{ statusLabel(p.status) }}</small></span>
                <span class="value" [class.struck]="p.status === 'REJECTED'">- {{ money(p.amount) }}</span>
              </li>
            } @empty {
              <li class="empty">Aún no tienes movimientos.</li>
            }
          </ul>
        </section>
      }
    </div>
  `,
})
export class DashboardView implements OnInit {
  private readonly api = inject(MockApiService);

  protected readonly wallet = signal<Wallet | null>(null);
  protected readonly payments = signal<Payment[]>([]);
  protected readonly loading = signal(false);
  protected readonly loadError = signal<ReadableError | null>(null);
  protected readonly transferring = signal(false);
  protected readonly transferMethod = signal<'contact' | 'qr'>('contact');
  protected readonly recent = computed(() => [...this.payments()].reverse().slice(0, MAX_MOVEMENTS));

  protected money = formatPen;

  ngOnInit(): void {
    this.reload();
  }

  protected reload(): void {
    this.loading.set(true);
    this.loadError.set(null);
    this.api.getWallet(environment.accountWalletId).subscribe((result) => {
      this.loading.set(false);
      if (result.ok && result.body) this.wallet.set(result.body);
      else this.loadError.set(describeError(result));
    });
    this.api.listPayments(environment.accountWalletId).subscribe((result) => {
      if (result.ok && result.body) this.payments.set(result.body);
      else this.loadError.set(describeError(result));
    });
  }

  protected startTransfer(method: 'contact' | 'qr'): void {
    this.transferMethod.set(method);
    this.transferring.set(true);
  }

  protected closeTransfer(): void {
    this.transferring.set(false);
    this.reload();
  }

  protected label(recipient: string): string {
    return RECIPIENT_LABELS[recipient] ?? recipient;
  }

  protected statusLabel(status: PaymentStatus): string {
    return STATUS_LABELS[status];
  }
}
