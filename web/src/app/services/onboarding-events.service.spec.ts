import { TestBed } from '@angular/core/testing';
import { OnboardingEventsService } from './onboarding-events.service';

describe('OnboardingEventsService', () => {
  let service: OnboardingEventsService;

  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-11-01T10:00:00Z'));
    service = TestBed.inject(OnboardingEventsService);
  });

  afterEach(() => vi.useRealTimers());

  const flow = (userId: string, seconds: number, outcome: 'ACTIVE' | 'PENDING' = 'ACTIVE') => {
    service.record('STARTED', userId);
    vi.advanceTimersByTime(seconds * 1000);
    service.record('CLOSED', userId, { outcome });
  };

  it('calcula la duración desde STARTED hasta CLOSED', () => {
    flow('a', 120);
    expect(service.durations()).toEqual([{ userId: 'a', ms: 120000 }]);
  });

  it('calcula la mediana de varias duraciones', () => {
    flow('a', 120);
    flow('b', 180);
    flow('c', 240);
    expect(service.medianMs()).toBe(180000);
  });

  it('ignora los onboardings abandonados en la mediana', () => {
    flow('a', 60);
    service.record('STARTED', 'abandonado');
    expect(service.durations()).toHaveLength(1);
  });

  it('cuenta nuevos usuarios activos por mes y calcula el CAC', () => {
    flow('a', 10);
    flow('b', 10);
    flow('c', 10, 'PENDING');
    expect(service.monthlySummary({ '2026-11': 20 })).toEqual([
      { month: '2026-11', newActiveUsers: 2, attributedSpendPen: 20, cacPen: 10 },
    ]);
  });

  it('clear borra los eventos', () => {
    flow('a', 5);
    service.clear();
    expect(service.events()).toEqual([]);
  });
});
