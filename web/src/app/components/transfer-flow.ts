import { Component, OnInit, computed, inject, input, output, signal } from '@angular/core';
import { environment } from '../../environments/environment';
import { ApiResult, Payment, ResolvedQr } from '../models/mock.models';
import { describeError } from '../services/error-messages';
import { MockApiService } from '../services/mock-api.service';
import { RECIPIENT_LABELS, formatPen, parsePenToCents } from '../services/money';

export type TransferStep = 'metodo' | 'datos' | 'confirmacion' | 'codigo' | 'listo';
type TransferMethod = 'contact' | 'qr';

const STEPS: readonly { key: TransferStep; label: string }[] = [
  { key: 'metodo', label: 'Método' },
  { key: 'datos', label: 'Datos' },
  { key: 'confirmacion', label: 'Confirmación' },
  { key: 'codigo', label: 'Validación' },
  { key: 'listo', label: 'Resultado' },
];
const MAX_CENTS = 100_000_000;

@Component({
  selector: 'app-transfer-flow',
  template: `
    <section class="card transfer" aria-labelledby="transfer-title">
      <h2 id="transfer-title">Transferencia</h2>
      <ol class="stepper" aria-label="Pasos de la transferencia">
        @for (s of steps; track s.key; let i = $index) {
          <li [attr.aria-current]="s.key === step() ? 'step' : null" [class.current]="s.key === step()">
            <span class="dot">{{ i + 1 }}</span><span class="label">{{ s.label }}</span>
          </li>
        }
      </ol>

      @switch (step()) {
        @case ('metodo') {
          <h3>Método de transferencia</h3>
          <div class="options" role="radiogroup" aria-label="Método de transferencia">
            <label class="option" [class.selected]="method() === 'contact'">
              <input type="radio" name="method" [checked]="method() === 'contact'" (change)="method.set('contact')" />
              <span><strong>Pago a contacto</strong><small>Envía dinero a un contacto</small></span>
            </label>
            <label class="option" [class.selected]="method() === 'qr'">
              <input type="radio" name="method" [checked]="method() === 'qr'" (change)="method.set('qr')" />
              <span><strong>Pago con QR</strong><small>Paga a un comercio con su QR</small></span>
            </label>
          </div>
          <button type="button" class="btn btn-dark" (click)="step.set('datos')">CONTINUAR</button>
          <button type="button" class="btn btn-link" (click)="close()">Cancelar</button>
        }
        @case ('datos') {
          @if (method() === 'contact') {
            <h3>Pago a contacto</h3>
            <p>Destinatario: <strong>{{ recipientLabel() }}</strong></p>
          } @else {
            <h3>Pago con QR</h3>
            <label class="field">
              <span>Texto del QR</span>
              <input
                type="text"
                name="qr"
                placeholder="qrmock:..."
                [value]="qrPayload()"
                (input)="onQrInput($event)"
              />
            </label>
            <div class="row">
              <button type="button" class="btn btn-outline" (click)="generateDemoQr()">Generar QR de prueba</button>
              <button type="button" class="btn btn-primary" [disabled]="loading()" (click)="validateQr()">Validar QR</button>
            </div>
            @if (qrInfo(); as q) {
              <p>
                Comercio: <strong>{{ q.merchantName }}</strong> ·
                {{ q.amountCents === null ? 'Monto abierto' : 'Monto: ' + money(q.amountCents) }}
              </p>
            }
          }
          @if (method() === 'contact' || (qrInfo() && qrInfo()?.amountCents === null)) {
            <label class="field">
              <span>Monto (S/)</span>
              <input
                type="text"
                name="amount"
                inputmode="decimal"
                placeholder="0.00"
                [value]="amountInput()"
                (input)="amountInput.set(valueOf($event))"
              />
            </label>
          }
          <p class="hint">Saldo disponible: {{ money(available()) }}</p>
          <button type="button" class="btn btn-dark" (click)="continueFromData()">CONTINUAR</button>
          <button type="button" class="btn btn-link" (click)="step.set('metodo')">Volver</button>
        }
        @case ('confirmacion') {
          <h3>¿Deseas confirmar la transferencia?</h3>
          <ul class="summary">
            <li>Destinatario: <strong>{{ recipientLabel() }}</strong></li>
            <li>Monto: <strong>{{ money(amountCents()) }}</strong></li>
            <li>Saldo disponible actual: {{ money(available()) }}</li>
            <li>Al aprobar se descontará de tu wallet.</li>
          </ul>
          <button type="button" class="btn btn-primary" (click)="confirm()">Continuar</button>
          <button type="button" class="btn btn-outline" (click)="close()">Rechazar</button>
        }
        @case ('codigo') {
          <div class="notice" role="status">
            Código de validación: <strong class="code">{{ code() }}</strong><br />
            EVITA LOS FRAUDES, nunca compartas tu código.
          </div>
          <h3>Ingresa tu código de validación</h3>
          <label class="field">
            <span>Código de 6 dígitos</span>
            <input
              type="text"
              name="code"
              inputmode="numeric"
              maxlength="6"
              autocomplete="one-time-code"
              [value]="codeInput()"
              (input)="codeInput.set(valueOf($event))"
            />
          </label>
          <button type="button" class="btn btn-primary" [disabled]="loading()" (click)="approve()">
            {{ loading() ? 'Procesando...' : 'Aprobar' }}
          </button>
        }
        @case ('listo') {
          <div class="result" aria-live="polite">
            @switch (payment()?.status) {
              @case ('SUCCEEDED') {
                <p class="big ok">✓</p>
                <h3>¡Listo! Tu transferencia fue exitosa</h3>
              }
              @case ('REJECTED') {
                <p class="big bad">✗</p>
                <h3>El pago fue rechazado</h3>
              }
              @default {
                <p class="big">…</p>
                <h3>Tu pago está pendiente de confirmación</h3>
              }
            }
            <ul class="summary">
              <li>Destinatario: <strong>{{ recipientLabel() }}</strong></li>
              <li>Monto: <strong>{{ money(amountCents()) }}</strong></li>
              @if (payment(); as p) {
                <li>Operación: {{ p.id }}</li>
              }
            </ul>
            <button type="button" class="btn btn-primary" (click)="close()">Cerrar</button>
          </div>
        }
      }

      @if (error()) {
        <p class="error" role="alert">{{ error() }}</p>
      }
    </section>
  `,
})
export class TransferFlow implements OnInit {
  private readonly api = inject(MockApiService);

  readonly available = input.required<number>();
  readonly initialMethod = input<TransferMethod>('contact');
  readonly closed = output<void>();

  protected readonly steps = STEPS;
  protected readonly step = signal<TransferStep>('metodo');
  protected readonly method = signal<TransferMethod>('contact');
  protected readonly amountInput = signal('');
  protected readonly qrPayload = signal('');
  protected readonly qrInfo = signal<ResolvedQr | null>(null);
  protected readonly amountCents = signal(0);
  protected readonly code = signal('');
  protected readonly codeInput = signal('');
  protected readonly error = signal<string | null>(null);
  protected readonly loading = signal(false);
  protected readonly payment = signal<Payment | null>(null);
  protected readonly recipient = computed(() => (this.method() === 'contact' ? 'contact-demo' : 'merchant-demo'));
  protected readonly recipientLabel = computed(() => RECIPIENT_LABELS[this.recipient()]);
  private readonly idempotencyKey = crypto.randomUUID();

  protected money = formatPen;

  ngOnInit(): void {
    this.method.set(this.initialMethod());
  }

  protected valueOf(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }

  protected close(): void {
    this.closed.emit();
  }

  protected onQrInput(event: Event): void {
    this.qrPayload.set(this.valueOf(event));
    this.qrInfo.set(null);
  }

  protected generateDemoQr(): void {
    this.error.set(null);
    this.api.createQr({ merchantId: 'merchant-demo' }).subscribe((result) => {
      if (result.ok && result.body) {
        this.qrPayload.set(result.body.payload);
        this.qrInfo.set(null);
      } else {
        this.show(result);
      }
    });
  }

  protected validateQr(): void {
    this.error.set(null);
    this.loading.set(true);
    this.api.resolveQr(this.qrPayload().trim()).subscribe((result) => {
      this.loading.set(false);
      if (result.ok && result.body) this.qrInfo.set(result.body);
      else this.show(result);
    });
  }

  protected continueFromData(): void {
    this.error.set(null);
    let cents: number | null;
    if (this.method() === 'qr') {
      const info = this.qrInfo();
      if (!info) {
        this.error.set('Valida el QR antes de continuar.');
        return;
      }
      cents = info.amountCents ?? parsePenToCents(this.amountInput());
    } else {
      cents = parsePenToCents(this.amountInput());
    }
    if (cents === null || cents < 1 || cents > MAX_CENTS) {
      this.error.set('Ingresa un monto válido en soles, por ejemplo 15.50.');
    } else if (cents > this.available()) {
      this.error.set(`Saldo insuficiente. Tu saldo disponible es ${formatPen(this.available())}.`);
    } else {
      this.amountCents.set(cents);
      this.step.set('confirmacion');
    }
  }

  protected confirm(): void {
    const digits = crypto.getRandomValues(new Uint32Array(1))[0] % 1_000_000;
    this.code.set(String(digits).padStart(6, '0'));
    this.codeInput.set('');
    this.error.set(null);
    this.step.set('codigo');
  }

  protected approve(): void {
    if (this.codeInput().trim() !== this.code()) {
      this.error.set('El código no coincide. Revisa el código de validación e inténtalo de nuevo.');
      return;
    }
    this.error.set(null);
    this.loading.set(true);
    const qrId = this.method() === 'qr' ? this.qrPayload().trim().replace(/^qrmock:/, '') : null;
    this.api
      .createPayment(
        {
          walletId: environment.accountWalletId,
          recipient: this.recipient(),
          amountCents: this.amountCents(),
          currency: 'PEN',
          ...(qrId ? { qrId } : {}),
        },
        this.idempotencyKey,
      )
      .subscribe((result) => {
        if (!result.ok || !result.body) {
          this.loading.set(false);
          this.show(result);
          return;
        }
        this.payment.set(result.body);
        if (result.body.status === 'PENDING') this.resolve(result.body.id);
        else this.finish();
      });
  }

  private resolve(id: string): void {
    this.api.resolvePayment(id).subscribe((result) => {
      if (result.ok && result.body && 'id' in result.body) this.payment.set(result.body);
      this.finish();
    });
  }

  private finish(): void {
    this.loading.set(false);
    this.step.set('listo');
  }

  private show<T>(result: ApiResult<T>): void {
    const readable = describeError(result);
    this.error.set(`${readable.message} ${readable.action}`);
  }
}
