import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { OnboardingEventsService } from '../services/onboarding-events.service';
import { SessionService } from '../services/session.service';
import { OnboardingFlow } from './onboarding-flow';

const BASE = environment.mockBaseUrl;
const SCENARIOS = { kyc: ['APPROVED', 'REJECTED', 'MANUAL_REVIEW', 'UNAVAILABLE'], payments: [], settlements: [] };

describe('OnboardingFlow', () => {
  let fixture: ComponentFixture<OnboardingFlow>;
  let http: HttpTestingController;
  let events: OnboardingEventsService;
  let root: HTMLElement;

  const tick = async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  };

  const button = (text: string): HTMLButtonElement => {
    const found = [...root.querySelectorAll('button')].find((b) => b.textContent?.includes(text));
    if (!found) throw new Error(`No hay botón "${text}"`);
    return found;
  };

  const typeDocument = async (value: string) => {
    const input = root.querySelector('input') as HTMLInputElement;
    input.value = value;
    input.dispatchEvent(new Event('input'));
    await tick();
  };

  const goToScenarioStep = async () => {
    await typeDocument('TEST-001');
    button('Continuar').click();
    await tick();
  };

  const submitWith = async (scenario: string, status: string) => {
    await goToScenarioStep();
    const select = root.querySelector('select') as HTMLSelectElement;
    select.value = scenario;
    select.dispatchEvent(new Event('change'));
    await tick();
    button('Continuar').click();
    await tick();
    button('Enviar verificación').click();
    http
      .expectOne(`${BASE}/kyc/verifications`)
      .flush({ id: 'kyc-1', wallet_id: 'w-1', scenario, status }, { status: 201, statusText: 'Created' });
    http
      .expectOne(`${BASE}/wallets/w-1`)
      .flush({ id: 'w-1', status, balance: 0, reserved: 0, available: 0, currency: 'PEN' });
    await tick();
  };

  beforeEach(async () => {
    localStorage.clear();
    TestBed.configureTestingModule({
      imports: [OnboardingFlow],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
    events = TestBed.inject(OnboardingEventsService);
    fixture = TestBed.createComponent(OnboardingFlow);
    root = fixture.nativeElement as HTMLElement;
    await tick();
    http.expectOne(`${BASE}/scenarios`).flush(SCENARIOS);
    await tick();
  });

  afterEach(() => http.verify());

  it('muestra la secuencia completa de pasos y el paso actual', () => {
    const items = [...root.querySelectorAll('ol li')];
    expect(items.map((li) => li.textContent?.trim())).toEqual(['1. documento', '2. escenario', '3. verificacion', '4. resultado']);
    expect(items[0].getAttribute('aria-current')).toBe('step');
    expect(root.textContent).toContain('Paso actual: documento');
  });

  it('bloquea el avance si falta el documento', async () => {
    button('Continuar').click();
    await tick();
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('Ingresa el documento');
    expect(root.textContent).toContain('Paso actual: documento');
  });

  it('bloquea un documento sin prefijo TEST- con mensaje accionable', async () => {
    await typeDocument('12345678');
    button('Continuar').click();
    await tick();
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('prefijo TEST-');
    expect(root.textContent).toContain('Paso actual: documento');
  });

  it('con APPROVED activa la wallet y habilita el acceso a pagos', async () => {
    await submitWith('APPROVED', 'ACTIVE');
    expect(root.textContent).toContain('Paso actual: resultado');
    expect(root.textContent).toContain('Tu cuenta está activa');
    expect(button('Ir a pagos de bajo monto').disabled).toBe(false);
  });

  it('no cambia el estado del flujo si la consola crea otra verificación', async () => {
    await submitWith('APPROVED', 'ACTIVE');
    TestBed.inject(SessionService).rememberVerification('kyc-2', 'w-2', 'PENDING');
    await tick();
    expect(root.textContent).toContain('Tu cuenta está activa');
    expect(button('Ir a pagos de bajo monto').disabled).toBe(false);
  });

  it.each([
    ['REJECTED', 'REJECTED', 'La cuenta fue rechazada'],
    ['MANUAL_REVIEW', 'PENDING', 'falta una decisión'],
  ])('con %s deshabilita el acceso a pagos y lo explica', async (scenario, status, text) => {
    await submitWith(scenario, status);
    expect(root.textContent).toContain(text);
    expect(button('Ir a pagos de bajo monto').disabled).toBe(true);
    expect(root.textContent).toContain('deshabilitado');
  });

  it('con 503 KYC_UNAVAILABLE no avanza y permite reintentar', async () => {
    await goToScenarioStep();
    button('Continuar').click();
    await tick();
    button('Enviar verificación').click();
    http.expectOne(`${BASE}/kyc/verifications`).flush({ error: 'KYC_UNAVAILABLE' }, { status: 503, statusText: 'Unavailable' });
    await tick();
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('Reintenta');
    expect(button('Enviar verificación').disabled).toBe(false);
  });

  it('registra inicio, cada paso y cierre en un onboarding completo', async () => {
    await submitWith('APPROVED', 'ACTIVE');
    const list = events.events();
    expect(list.map((e) => e.type)).toEqual(['STARTED', 'STEP_COMPLETED', 'STEP_COMPLETED', 'STEP_COMPLETED', 'CLOSED']);
    expect(list.filter((e) => e.type === 'STEP_COMPLETED').map((e) => e.step)).toEqual(['documento', 'escenario', 'verificacion']);
    expect(list.every((e) => e.userId === list[0].userId && !!e.timestamp)).toBe(true);
    expect(events.durations()).toHaveLength(1);
  });

  it('un onboarding abandonado no tiene evento de cierre', async () => {
    await goToScenarioStep();
    expect(events.events().map((e) => e.type)).toEqual(['STARTED', 'STEP_COMPLETED']);
    expect(events.durations()).toHaveLength(0);
  });
});
