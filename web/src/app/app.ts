import { Component, computed, inject, signal } from '@angular/core';
import { DashboardView } from './components/dashboard-view';
import { LoginView } from './components/login-view';
import { RegisterView } from './components/register-view';
import { TestConsole } from './components/test-console';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  imports: [LoginView, RegisterView, DashboardView, TestConsole],
  template: `
    @if (auth.user(); as user) {
      <header class="topbar">
        <span class="brand">Wallet</span>
        <nav aria-label="Navegación principal">
          <button type="button" class="btn btn-link" [class.current]="view() === 'home'" (click)="view.set('home')">
            Inicio
          </button>
          @if (isAdmin()) {
            <button
              type="button"
              class="btn btn-link"
              [class.current]="view() === 'console'"
              (click)="view.set('console')"
            >
              Consola de pruebas
            </button>
          }
          <span class="user">{{ user.name }}</span>
          <button type="button" class="btn btn-link" (click)="logout()">Cerrar sesión</button>
        </nav>
      </header>
      <main class="content">
        @if (view() === 'console' && isAdmin()) {
          <app-test-console />
        } @else {
          <app-dashboard-view />
        }
      </main>
    } @else if (guest() === 'login') {
      <app-login-view (registerRequested)="guest.set('register')" />
    } @else {
      <app-register-view (loginRequested)="guest.set('login')" />
    }
  `,
})
export class App {
  protected readonly auth = inject(AuthService);
  protected readonly view = signal<'home' | 'console'>('home');
  protected readonly guest = signal<'register' | 'login'>('register');
  protected readonly isAdmin = computed(() => this.auth.user()?.role === 'admin');

  protected logout(): void {
    this.view.set('home');
    this.guest.set('login');
    this.auth.logout();
  }
}
