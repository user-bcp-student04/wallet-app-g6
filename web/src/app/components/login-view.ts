import { Component, inject, signal } from '@angular/core';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-login-view',
  template: `
    <main class="login">
      <section class="card login-card" aria-labelledby="login-title">
        <h1 id="login-title">Ingresa a tu wallet</h1>
        <form (submit)="submit($event)" novalidate>
          <label class="field">
            <span>DNI</span>
            <input
              type="text"
              name="dni"
              autocomplete="username"
              autocapitalize="none"
              [value]="dni()"
              (input)="dni.set(valueOf($event))"
            />
          </label>
          <label class="field">
            <span>Contraseña</span>
            <input
              type="password"
              name="password"
              autocomplete="current-password"
              [value]="password()"
              (input)="password.set(valueOf($event))"
            />
          </label>
          @if (error()) {
            <p class="error" role="alert">{{ error() }}</p>
          }
          <button type="submit" class="btn btn-dark">Ingresar</button>
        </form>
      </section>
    </main>
  `,
})
export class LoginView {
  private readonly auth = inject(AuthService);
  protected readonly dni = signal('');
  protected readonly password = signal('');
  protected readonly error = signal<string | null>(null);

  protected valueOf(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }

  protected submit(event: Event): void {
    event.preventDefault();
    this.error.set(this.auth.login(this.dni(), this.password()));
  }
}
