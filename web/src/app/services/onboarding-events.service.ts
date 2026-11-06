import { Injectable, computed, inject, signal } from '@angular/core';
import { OnboardingEvent, OnboardingEventType, WalletStatus } from '../models/mock.models';
import { SessionService } from './session.service';

const KEY_EVENTS = 'wallet.onboardingEvents';

export interface OnboardingDuration {
  userId: string;
  ms: number;
}

export interface MonthlySummary {
  month: string;
  newActiveUsers: number;
  attributedSpendPen: number | null;
  cacPen: number | null;
}

@Injectable({ providedIn: 'root' })
export class OnboardingEventsService {
  private readonly session = inject(SessionService);

  readonly events = signal<OnboardingEvent[]>(this.session.readStore<OnboardingEvent[]>(KEY_EVENTS, []));

  readonly durations = computed<OnboardingDuration[]>(() => {
    const started = new Map<string, number>();
    const result: OnboardingDuration[] = [];
    for (const event of this.events()) {
      const time = Date.parse(event.timestamp);
      if (event.type === 'STARTED') started.set(event.userId, time);
      const start = started.get(event.userId);
      if (event.type === 'CLOSED' && start !== undefined) result.push({ userId: event.userId, ms: time - start });
    }
    return result;
  });

  readonly medianMs = computed<number | null>(() => {
    const sorted = this.durations()
      .map((d) => d.ms)
      .sort((a, b) => a - b);
    if (sorted.length === 0) return null;
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
  });

  record(
    type: OnboardingEventType,
    userId: string,
    extra: { step?: string; outcome?: WalletStatus; verificationId?: string } = {},
  ): void {
    const next = [...this.events(), { type, userId, ...extra, timestamp: new Date().toISOString() }];
    this.events.set(next);
    this.session.writeStore(KEY_EVENTS, next);
  }

  clear(): void {
    this.events.set([]);
    this.session.removeStore(KEY_EVENTS);
  }

  monthlySummary(spendByMonth: Record<string, number>): MonthlySummary[] {
    const active = new Map<string, Set<string>>();
    for (const event of this.events()) {
      if (event.type !== 'CLOSED' || event.outcome !== 'ACTIVE') continue;
      const month = event.timestamp.slice(0, 7);
      active.set(month, (active.get(month) ?? new Set<string>()).add(event.userId));
    }
    return [...active.keys()].sort().map((month) => {
      const newActiveUsers = active.get(month)?.size ?? 0;
      const spend = spendByMonth[month];
      return {
        month,
        newActiveUsers,
        attributedSpendPen: spend ?? null,
        cacPen: spend !== undefined && newActiveUsers > 0 ? spend / newActiveUsers : null,
      };
    });
  }
}
