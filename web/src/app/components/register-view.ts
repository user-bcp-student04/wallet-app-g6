import { Component, inject, output, signal } from '@angular/core';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-register-view',
  template: `
    <main class="login">
      <section class="card login-card" aria-labelledby="register-title">
        @if (stage() === 'form') {
          <h1 id="register-title">Regístrate como cliente</h1>
          <form (submit)="submitForm($event)" novalidate>
            <label class="field">
              <span>Tipo de documento</span>
              <select name="documentType" [value]="documentType()" (change)="documentType.set(valueOf($event))">
                <option value="DNI" [selected]="documentType() === 'DNI'">DNI</option>
              </select>
            </label>
            <label class="field">
              <span>Número de documento</span>
              <input
                type="text"
                name="documentNumber"
                inputmode="numeric"
                maxlength="8"
                autocomplete="off"
                [value]="documentNumber()"
                (input)="documentNumber.set(valueOf($event))"
              />
            </label>
            @if (error()) {
              <p class="error" role="alert">{{ error() }}</p>
            }
            <button type="submit" class="btn btn-dark">REGISTRARME</button>
          </form>
          <button type="button" class="btn btn-link" (click)="loginRequested.emit()">Ya tengo cuenta, ingresar</button>
        } @else {
          <h1 id="register-title">Valida tu registro</h1>
          <p class="notice" role="status">
            Se ha enviado un OTP de aprobación al registro del DNI {{ documentNumber() }}.<br />
            Código de prueba (demo): <strong class="code">0000</strong>
          </p>
          <form (submit)="submitOtp($event)" novalidate>
            <label class="field">
              <span>Ingresa tu OTP</span>
              <input
                type="text"
                name="otp"
                inputmode="numeric"
                maxlength="4"
                autocomplete="one-time-code"
                [value]="otp()"
                (input)="otp.set(valueOf($event))"
              />
            </label>
            @if (error()) {
              <p class="error" role="alert">{{ error() }}</p>
            }
            <button type="submit" class="btn btn-dark">VALIDAR OTP</button>
          </form>
          <button type="button" class="btn btn-link" (click)="back()">Volver</button>
        }
      </section>
    </main>
  `,
})
export class RegisterView {
  private readonly auth = inject(AuthService);

  readonly loginRequested = output<void>();

  protected readonly stage = signal<'form' | 'otp'>('form');
  protected readonly documentType = signal('DNI');
  protected readonly documentNumber = signal('');
  protected readonly otp = signal('');
  protected readonly error = signal<string | null>(null);

  protected valueOf(event: Event): string {
    return (event.target as HTMLInputElement | HTMLSelectElement).value;
  }

  protected submitForm(event: Event): void {
    event.preventDefault();
    const problem = this.auth.validateRegistration(this.documentType(), this.documentNumber());
    this.error.set(problem);
    if (problem === null) {
      this.otp.set('');
      this.stage.set('otp');
    }
  }

  protected submitOtp(event: Event): void {
    event.preventDefault();
    this.error.set(this.auth.confirmOtp(this.documentNumber(), this.otp()));
  }

  protected back(): void {
    this.error.set(null);
    this.stage.set('form');
  }
}
