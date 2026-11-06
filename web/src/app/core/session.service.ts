// src/app/core/session.service.ts
import { Injectable, computed, signal } from '@angular/core';

import { OnboardingStateResponse, VerificationResponse } from './api.models';

const OWNER_STORAGE_KEY = 'wallet.ownerId';

function readStoredOwner(): string | null {
  try {
    return sessionStorage.getItem(OWNER_STORAGE_KEY);
  } catch {
    return null;
  }
}

function writeStoredOwner(value: string | null): void {
  try {
    if (value === null) {
      sessionStorage.removeItem(OWNER_STORAGE_KEY);
    } else {
      sessionStorage.setItem(OWNER_STORAGE_KEY, value);
    }
  } catch {
    // Sin almacenamiento disponible: la sesión vive solo en memoria.
  }
}

/** Única fuente de sesión del flujo (singleton). */
@Injectable({ providedIn: 'root' })
export class SessionService {
  private readonly ownerIdState = signal<string | null>(readStoredOwner());
  private readonly walletState = signal<OnboardingStateResponse | null>(null);
  private readonly verificationState = signal<VerificationResponse | null>(null);

  readonly ownerId = this.ownerIdState.asReadonly();
  readonly isIdentified = computed(() => this.ownerIdState() !== null);
  readonly wallet = this.walletState.asReadonly();
  readonly verification = this.verificationState.asReadonly();

  setOwner(ownerId: string): void {
    if (ownerId !== this.ownerIdState()) {
      this.resetProgress();
    }
    this.ownerIdState.set(ownerId);
    writeStoredOwner(ownerId);
  }

  setWallet(wallet: OnboardingStateResponse | null): void {
    this.walletState.set(wallet);
  }

  setVerification(verification: VerificationResponse | null): void {
    this.verificationState.set(verification);
  }

  /** Descarta lo cacheado del progreso (tras un reset o un cambio de usuario). */
  resetProgress(): void {
    this.walletState.set(null);
    this.verificationState.set(null);
  }

  clear(): void {
    this.resetProgress();
    this.ownerIdState.set(null);
    writeStoredOwner(null);
  }
}
