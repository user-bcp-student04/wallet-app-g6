import { Injectable, inject, signal } from '@angular/core';
import { SessionService } from './session.service';

export interface AuthUser {
  dni: string;
  name: string;
  role: 'admin';
}

const KEY_AUTH = 'wallet.auth';
// Usuario dummy de la demo: la comprobación en el cliente no es autenticación real.
const DUMMY = { dni: 'admin', password: 'admin', name: 'Administrador' };

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly session = inject(SessionService);
  readonly user = signal<AuthUser | null>(this.session.readStore<AuthUser | null>(KEY_AUTH, null));

  login(dni: string, password: string): string | null {
    if (dni.trim() === '') return 'Ingresa tu DNI.';
    if (password === '') return 'Ingresa tu contraseña.';
    if (dni.trim() !== DUMMY.dni || password !== DUMMY.password) return 'DNI o contraseña incorrectos.';
    const user: AuthUser = { dni: DUMMY.dni, name: DUMMY.name, role: 'admin' };
    this.user.set(user);
    this.session.writeStore(KEY_AUTH, user);
    return null;
  }

  logout(): void {
    this.user.set(null);
    this.session.removeStore(KEY_AUTH);
  }
}
