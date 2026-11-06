import { Injectable, inject, signal } from '@angular/core';
import { SessionService } from './session.service';

export interface AuthUser {
  dni: string;
  name: string;
  role: 'admin' | 'customer';
}

interface Credential {
  salt: string;
  hash: string;
}

const KEY_AUTH = 'wallet.auth';
const KEY_CLIENTS = 'wallet.clients';
// Datos dummy de la demo: estas comprobaciones en el cliente no son autenticación real.
const DUMMY = { dni: 'admin', password: 'admin', name: 'Administrador' };
const DUMMY_OTP = '0000';
const MAX_DOCUMENT_LENGTH = 8;
const MIN_PASSWORD_LENGTH = 4;
const PBKDF2_ITERATIONS = 100_000;

export const NOT_REGISTERED_MESSAGE = 'Ups, registrate como nuevo usuario';

const toHex = (bytes: Uint8Array): string => [...bytes].map((b) => b.toString(16).padStart(2, '0')).join('');

async function derive(password: string, salt: string): Promise<string> {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey('raw', encoder.encode(password), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', hash: 'SHA-256', salt: encoder.encode(salt), iterations: PBKDF2_ITERATIONS },
    key,
    256,
  );
  return toHex(new Uint8Array(bits));
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly session = inject(SessionService);
  readonly user = signal<AuthUser | null>(this.session.readStore<AuthUser | null>(KEY_AUTH, null));

  async login(dni: string, password: string): Promise<string | null> {
    const id = dni.trim();
    if (id === '') return 'Ingresa tu DNI.';
    if (password === '') return 'Ingresa tu contraseña.';
    if (id === DUMMY.dni) {
      if (password !== DUMMY.password) return 'DNI o contraseña incorrectos.';
      this.open({ dni: DUMMY.dni, name: DUMMY.name, role: 'admin' });
      return null;
    }
    const credential = this.clients()[id];
    if (!credential) return NOT_REGISTERED_MESSAGE;
    if ((await derive(password, credential.salt)) !== credential.hash) return 'DNI o contraseña incorrectos.';
    this.open({ dni: id, name: `Cliente ${id}`, role: 'customer' });
    return null;
  }

  validateRegistration(documentType: string, documentNumber: string, password: string): string | null {
    if (documentType !== 'DNI') return 'Elige el tipo de documento DNI.';
    const number = documentNumber.trim();
    if (number === '') return 'Ingresa tu número de documento.';
    if (!/^\d+$/.test(number)) return 'El número de documento solo admite dígitos.';
    if (number.length > MAX_DOCUMENT_LENGTH) return `El número de documento admite máximo ${MAX_DOCUMENT_LENGTH} dígitos.`;
    if (password === '') return 'Ingresa tu contraseña.';
    if (password.length < MIN_PASSWORD_LENGTH) return `La contraseña debe tener al menos ${MIN_PASSWORD_LENGTH} caracteres.`;
    if (this.clients()[number]) return 'Este DNI ya está registrado. Ingresa con tu contraseña.';
    return null;
  }

  async confirmOtp(documentNumber: string, password: string, otp: string): Promise<string | null> {
    if (otp.trim() !== DUMMY_OTP) return 'El OTP no es correcto. Revisa el código e inténtalo de nuevo.';
    const id = documentNumber.trim();
    const salt = toHex(crypto.getRandomValues(new Uint8Array(16)));
    this.session.writeStore(KEY_CLIENTS, { ...this.clients(), [id]: { salt, hash: await derive(password, salt) } });
    this.open({ dni: id, name: `Cliente ${id}`, role: 'customer' });
    return null;
  }

  logout(): void {
    this.user.set(null);
    this.session.removeStore(KEY_AUTH);
  }

  private clients(): Record<string, Credential> {
    return this.session.readStore<Record<string, Credential>>(KEY_CLIENTS, {});
  }

  private open(user: AuthUser): void {
    this.user.set(user);
    this.session.writeStore(KEY_AUTH, user);
  }
}
