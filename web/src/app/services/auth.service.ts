import { Injectable, inject, signal } from '@angular/core';
import { SessionService } from './session.service';

export interface AuthUser {
  dni: string;
  name: string;
  role: 'admin' | 'customer';
}

const KEY_AUTH = 'wallet.auth';
// Datos dummy de la demo: estas comprobaciones en el cliente no son autenticación real.
const DUMMY = { dni: 'admin', password: 'admin', name: 'Administrador' };
const DUMMY_OTP = '0000';
const MAX_DOCUMENT_LENGTH = 8;

export const NOT_REGISTERED_MESSAGE = 'Ups, registrate como nuevo usuario';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly session = inject(SessionService);
  readonly user = signal<AuthUser | null>(this.session.readStore<AuthUser | null>(KEY_AUTH, null));

  login(dni: string, password: string): string | null {
    if (dni.trim() === '') return 'Ingresa tu DNI.';
    if (password === '') return 'Ingresa tu contraseña.';
    if (dni.trim() !== DUMMY.dni) return NOT_REGISTERED_MESSAGE;
    if (password !== DUMMY.password) return 'DNI o contraseña incorrectos.';
    this.open({ dni: DUMMY.dni, name: DUMMY.name, role: 'admin' });
    return null;
  }

  validateRegistration(documentType: string, documentNumber: string): string | null {
    if (documentType !== 'DNI') return 'Elige el tipo de documento DNI.';
    const number = documentNumber.trim();
    if (number === '') return 'Ingresa tu número de documento.';
    if (!/^\d+$/.test(number)) return 'El número de documento solo admite dígitos.';
    if (number.length > MAX_DOCUMENT_LENGTH) return `El número de documento admite máximo ${MAX_DOCUMENT_LENGTH} dígitos.`;
    return null;
  }

  confirmOtp(documentNumber: string, otp: string): string | null {
    if (otp.trim() !== DUMMY_OTP) return 'El OTP no es correcto. Revisa el código e inténtalo de nuevo.';
    this.open({ dni: documentNumber.trim(), name: `Cliente ${documentNumber.trim()}`, role: 'customer' });
    return null;
  }

  logout(): void {
    this.user.set(null);
    this.session.removeStore(KEY_AUTH);
  }

  private open(user: AuthUser): void {
    this.user.set(user);
    this.session.writeStore(KEY_AUTH, user);
  }
}
