import { Injectable, computed, signal } from '@angular/core';
import { environment } from '../../environments/environment';
import { WalletStatus } from '../models/mock.models';

const KEY_BASE_URL = 'wallet.baseUrl';
const KEY_LATENCY = 'wallet.latency';
const MAX_LATENCY_MS = 5000;

@Injectable({ providedIn: 'root' })
export class SessionService {
  readonly baseUrl = signal(this.readStore<string>(KEY_BASE_URL, environment.mockBaseUrl));
  readonly latencyInput = signal(this.readStore<string>(KEY_LATENCY, '0'));
  readonly verificationId = signal<string | null>(null);
  readonly walletId = signal<string | null>(null);
  readonly walletStatus = signal<WalletStatus | null>(null);
  readonly scenarios = signal<string[]>([]);

  readonly latencyError = computed(() => {
    const raw = this.latencyInput().trim();
    if (raw === '') return null;
    const valid = /^\d+$/.test(raw) && Number(raw) <= MAX_LATENCY_MS;
    return valid ? null : `La latencia debe ser un entero entre 0 y ${MAX_LATENCY_MS} ms.`;
  });

  readonly latencyMs = computed(() => {
    const raw = this.latencyInput().trim();
    return this.latencyError() === null ? Number(raw === '' ? '0' : raw) : null;
  });

  setBaseUrl(value: string): string | null {
    const trimmed = value.trim().replace(/\/+$/, '');
    try {
      const url = new URL(trimmed);
      if (url.protocol !== 'http:' && url.protocol !== 'https:') throw new Error('protocol');
    } catch {
      return 'La URL base debe empezar con http:// o https://.';
    }
    this.baseUrl.set(trimmed);
    this.writeStore(KEY_BASE_URL, trimmed);
    return null;
  }

  setLatencyInput(value: string): void {
    this.latencyInput.set(value);
    this.writeStore(KEY_LATENCY, value);
  }

  rememberVerification(id: string, walletId: string, status: WalletStatus): void {
    this.verificationId.set(id);
    this.walletId.set(walletId);
    this.walletStatus.set(status);
  }

  clearIdentifiers(): void {
    this.verificationId.set(null);
    this.walletId.set(null);
    this.walletStatus.set(null);
  }

  readStore<T>(key: string, fallback: T): T {
    try {
      const raw = localStorage.getItem(key);
      return raw === null ? fallback : (JSON.parse(raw) as T);
    } catch {
      return fallback;
    }
  }

  writeStore(key: string, value: unknown): void {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Sin almacenamiento disponible: la sesión sigue en memoria.
    }
  }

  removeStore(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch {
      // Sin almacenamiento disponible.
    }
  }
}
