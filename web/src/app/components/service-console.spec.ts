import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { OnboardingEventsService } from '../services/onboarding-events.service';
import { SessionService } from '../services/session.service';
import { ServiceConsole } from './service-console';

const BASE = environment.mockBaseUrl;

describe('ServiceConsole', () => {
  let fixture: ComponentFixture<ServiceConsole>;
  let http: HttpTestingController;
  let root: HTMLElement;

  const tick = async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  };

  const click = async (text: string) => {
    const found = [...root.querySelectorAll('button')].find((b) => b.textContent?.trim() === text);
    if (!found) throw new Error(`No hay botón "${text}"`);
    found.click();
    await tick();
  };

  beforeEach(async () => {
    localStorage.clear();
    TestBed.configureTestingModule({
      imports: [ServiceConsole],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(ServiceConsole);
    root = fixture.nativeElement as HTMLElement;
    await tick();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    http.verify();
  });

  it('muestra método, ruta, código HTTP, cuerpo y tiempo de respuesta', async () => {
    await click('Ejecutar');
    http.expectOne(`${BASE}/health`).flush({ status: 'ok', storage: 'memory' });
    await tick();
    const text = root.textContent ?? '';
    expect(text).toContain('GET /health');
    expect(text).toContain('Código HTTP: 200');
    expect(text).toContain('"status": "ok"');
    expect(text).toContain('ms');
  });

  it('POST /control/reset limpia identificadores y eventos locales tras confirmar', async () => {
    const session = TestBed.inject(SessionService);
    const events = TestBed.inject(OnboardingEventsService);
    session.rememberVerification('kyc-1', 'w-1', 'ACTIVE');
    events.record('STARTED', 'flow-1');
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    await click('POST /control/reset');
    await click('Ejecutar');
    http.expectOne(`${BASE}/control/reset`).flush({ reset: true });
    await tick();
    expect(session.verificationId()).toBeNull();
    expect(session.walletId()).toBeNull();
    expect(events.events()).toEqual([]);
  });

  it('cancelar la confirmación del reset no llama a la API', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    await click('POST /control/reset');
    await click('Ejecutar');
    http.expectNone(`${BASE}/control/reset`);
    expect(root.textContent).not.toContain('Código HTTP');
  });

  it('con 429 GROUP_LIMIT_RESET_REQUIRED indica reiniciar el grupo', async () => {
    await click('POST /kyc/verifications');
    await click('Ejecutar');
    http.expectOne(`${BASE}/kyc/verifications`).flush({ error: 'GROUP_LIMIT_RESET_REQUIRED' }, { status: 429, statusText: 'Too Many Requests' });
    await tick();
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('Reinicia el grupo');
  });

  it('reutiliza id y wallet_id de la última verificación como valores sugeridos', async () => {
    TestBed.inject(SessionService).rememberVerification('kyc-9', 'w-9', 'PENDING');
    await click('GET /kyc/verifications/{id}');
    expect((root.querySelector('input') as HTMLInputElement).value).toBe('kyc-9');
    await click('GET /wallets/{id}');
    expect((root.querySelector('input') as HTMLInputElement).value).toBe('w-9');
  });
});
