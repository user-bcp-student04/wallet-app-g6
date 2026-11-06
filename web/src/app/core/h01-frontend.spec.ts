// src/app/core/h01-frontend.spec.ts
// Supuestos (T-11): Jasmine/Karma (Angular 17 por defecto), rutas src/app/... de frontend_spec.md.
// Comando: ng test --watch=false --browsers=ChromeHeadless
import { Component } from '@angular/core';
import { HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { FormControl } from '@angular/forms';
import { provideRouter } from '@angular/router';
import { Subject, of, throwError } from 'rxjs';

import { OnboardingStateResponse } from './api.models';
import { documentErrorMessage, testDocumentValidator } from './document.validator';
import { MockApiService, toApiErrorView } from './mock-api.service';
import { SessionService } from './session.service';
import { ConsolaComponent } from '../consola/consola.component';
import { OnboardingComponent } from '../onboarding/onboarding.component';
import { PagosComponent } from '../pagos/pagos.component';

@Component({ standalone: true, template: '' })
class VacioComponent {}

function estado(over: Partial<OnboardingStateResponse> = {}): OnboardingStateResponse {
  return {
    wallet_status: 'IN_PROGRESS',
    current_step: 'kyc',
    steps: [
      { id: 'registro', order: 1, status: 'COMPLETED' },
      { id: 'kyc', order: 2, status: 'CURRENT' },
      { id: 'activacion', order: 3, status: 'LOCKED' },
    ],
    low_amount_payments_enabled: false,
    duration_seconds: null,
    ...over,
  };
}

describe('SessionService (CA-2.2b)', () => {
  beforeEach(() => sessionStorage.clear());

  it('devuelve la misma instancia en dos inyecciones', () => {
    expect(TestBed.inject(SessionService)).toBe(TestBed.inject(SessionService));
  });

  it('descarta wallet y verificación al cambiar de usuario', () => {
    const s = TestBed.inject(SessionService);
    s.setOwner('usuario-1');
    s.setWallet(estado());
    s.setOwner('usuario-2');
    expect(s.wallet()).toBeNull();
    expect(s.verification()).toBeNull();
  });
});

describe('toApiErrorView (CA-2.3d, CA-2.7b)', () => {
  it('conserva code y message del API', () => {
    const e = new HttpErrorResponse({ status: 409, error: { code: 'STEP_BLOCKED', message: 'Completa el paso previo.' } });
    expect(toApiErrorView(e)).toEqual({ status: 409, code: 'STEP_BLOCKED', message: 'Completa el paso previo.' });
  });

  it('mapea status 0 a NETWORK_ERROR', () => {
    expect(toApiErrorView(new HttpErrorResponse({ status: 0 })).code).toBe('NETWORK_ERROR');
  });

  it('usa un mensaje por defecto si el cuerpo no es {code,message}', () => {
    const e = toApiErrorView(new HttpErrorResponse({ status: 422, error: '<html>' }));
    expect(e.code).toBe('VALIDATION_ERROR');
    expect(e.message.length).toBeGreaterThan(0);
    expect(toApiErrorView(new HttpErrorResponse({ status: 502, error: '<html>' })).code).toBe('HTTP_ERROR');
  });

  it('un error que no es HTTP se vuelve UNKNOWN_ERROR', () => {
    expect(toApiErrorView(new Error('x')).code).toBe('UNKNOWN_ERROR');
  });
});

describe('testDocumentValidator (CA-2.3c)', () => {
  const casos: Array<[string, object | null]> = [
    ['TEST-0001', null],
    ['TEST-' + 'A'.repeat(59), null],
    ['', { required: true }],
    ['12345678', { notTest: true }],
    ['test-1', { notTest: true }],
    ['TEST-', { suffix: true }],
    ['TEST-a b', { suffix: true }],
    ['TEST-' + 'A'.repeat(60), { maxlength: true }],
  ];
  for (const [valor, esperado] of casos) {
    it(`valida "${valor.slice(0, 20)}"`, () => {
      expect(testDocumentValidator(new FormControl(valor))).toEqual(esperado);
    });
  }

  it('el mensaje de prefijo es accionable', () => {
    expect(documentErrorMessage({ notTest: true })).toContain('TEST-');
  });
});

describe('MockApiService (CA-2.2a, transversal-1)', () => {
  let http: HttpTestingController;
  let api: MockApiService;
  let session: SessionService;

  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: 'identificar', component: VacioComponent }]),
        MockApiService,
      ],
    });
    http = TestBed.inject(HttpTestingController);
    api = TestBed.inject(MockApiService);
    session = TestBed.inject(SessionService);
  });

  afterEach(() => http.verify());

  it('expone un método por endpoint', () => {
    for (const m of ['health', 'scenarios', 'supportCases', 'createVerification', 'getVerification', 'decideVerification', 'getOnboarding', 'submitStep', 'reset']) {
      expect(typeof (api as unknown as Record<string, unknown>)[m]).toBe('function');
    }
  });

  it('envía X-Owner-Id y nunca el propietario en el cuerpo', () => {
    session.setOwner('demo-user-1');
    api.createVerification({ document_number: 'TEST-0001', scenario: 'APPROVED' }).subscribe();
    const req = http.expectOne('/kyc/verifications');
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('X-Owner-Id')).toBe('demo-user-1');
    expect(Object.keys(req.request.body as object).sort()).toEqual(['document_number', 'scenario']);
    req.flush({});
  });

  it('submitStep de kyc envía cuerpo vacío a la ruta del paso', () => {
    session.setOwner('demo-user-1');
    api.submitStep({ step_id: 'kyc' }).subscribe();
    const req = http.expectOne('/onboarding/steps/kyc');
    expect(req.request.body).toEqual({});
    req.flush(estado());
  });

  it('un 401 limpia la sesión y propaga el error legible', () => {
    session.setOwner('demo-user-1');
    let error: { code?: string } | undefined;
    api.getOnboarding().subscribe({ error: (e) => (error = e) });
    http.expectOne('/onboarding').flush({ code: 'UNAUTHENTICATED', message: 'No se pudo identificar al usuario.' }, { status: 401, statusText: 'Unauthorized' });
    expect(session.isIdentified()).toBeFalse();
    expect(error?.code).toBe('UNAUTHENTICATED');
  });
});

function stubApi() {
  return jasmine.createSpyObj<MockApiService>('MockApiService', [
    'health', 'scenarios', 'supportCases', 'createVerification', 'getVerification',
    'decideVerification', 'getOnboarding', 'submitStep', 'reset',
  ]);
}

describe('ConsolaComponent (CA-2.7a, 2.7b, 2.7c)', () => {
  let api: jasmine.SpyObj<MockApiService>;

  beforeEach(() => {
    api = stubApi();
    TestBed.configureTestingModule({
      imports: [ConsolaComponent],
      providers: [{ provide: MockApiService, useValue: api }, provideRouter([])],
    });
  });

  it('reset: sin confirmar no llama al API; cancelar tampoco', () => {
    const c = TestBed.createComponent(ConsolaComponent).componentInstance;
    c.askReset();
    expect(c.confirmingReset()).toBeTrue();
    expect(api.reset).not.toHaveBeenCalled();
    c.cancelReset();
    expect(c.confirmingReset()).toBeFalse();
    expect(api.reset).not.toHaveBeenCalled();
  });

  it('reset: confirmar llama una sola vez', async () => {
    api.reset.and.returnValue(of({ status: 'reset' }));
    const c = TestBed.createComponent(ConsolaComponent).componentInstance;
    c.askReset();
    await c.confirmReset();
    expect(api.reset).toHaveBeenCalledTimes(1);
    expect(c.resetDone()).toBeTrue();
  });

  it('ejecuta un servicio individual sin llamar a los demás', async () => {
    api.health.and.returnValue(of({ status: 'ok' }));
    const c = TestBed.createComponent(ConsolaComponent).componentInstance;
    await c.run('health');
    expect(api.health).toHaveBeenCalledTimes(1);
    expect(api.scenarios).not.toHaveBeenCalled();
    expect(api.supportCases).not.toHaveBeenCalled();
    expect(c.health()?.status).toBe('ok');
  });

  it('muestra el message del API, no JSON crudo', async () => {
    api.health.and.returnValue(throwError(() => ({ status: 409, code: 'X', message: 'Mensaje legible' })));
    const fixture = TestBed.createComponent(ConsolaComponent);
    await fixture.componentInstance.run('health');
    fixture.detectChanges();
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('Mensaje legible');
    expect(texto).not.toContain('{"code"');
  });

  it('no permite ejecuciones duplicadas simultáneas', async () => {
    const respuesta = new Subject<{ status: string }>();
    api.health.and.returnValue(respuesta);
    const c = TestBed.createComponent(ConsolaComponent).componentInstance;
    const p1 = c.run('health');
    const p2 = c.run('health');
    expect(api.health).toHaveBeenCalledTimes(1);
    respuesta.next({ status: 'ok' });
    respuesta.complete();
    await Promise.all([p1, p2]);
  });
});

describe('PagosComponent (CA-2.6b)', () => {
  async function render(habilitado: boolean): Promise<string> {
    const api = stubApi();
    api.getOnboarding.and.returnValue(of(estado({ low_amount_payments_enabled: habilitado, wallet_status: habilitado ? 'ACTIVE' : 'IN_PROGRESS' })));
    TestBed.configureTestingModule({
      imports: [PagosComponent],
      providers: [{ provide: MockApiService, useValue: api }, provideRouter([])],
    });
    const fixture = TestBed.createComponent(PagosComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  it('habilita el acceso solo con wallet activa', async () => {
    expect(await render(true)).toContain('Acceso habilitado');
  });

  it('bloquea el acceso si la wallet no está activa', async () => {
    expect(await render(false)).toContain('Acceso bloqueado');
  });
});

describe('OnboardingComponent (CA-2.6a, duplicados)', () => {
  let api: jasmine.SpyObj<MockApiService>;

  beforeEach(() => {
    api = stubApi();
    api.getOnboarding.and.returnValue(of(estado()));
    api.scenarios.and.returnValue(of({ scenarios: [] }));
    api.supportCases.and.returnValue(of({ cases: [] }));
    TestBed.configureTestingModule({
      imports: [OnboardingComponent],
      providers: [{ provide: MockApiService, useValue: api }, provideRouter([])],
    });
  });

  it('marca el paso actual con aria-current="step"', async () => {
    const fixture = TestBed.createComponent(OnboardingComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const actual = (fixture.nativeElement as HTMLElement).querySelector('[aria-current="step"]');
    expect(actual?.textContent).toContain('Verificación KYC');
    expect(actual?.textContent).toContain('Paso actual');
  });

  it('no envía dos veces el registro con doble clic', async () => {
    api.getOnboarding.and.returnValue(of(estado({ current_step: 'registro', wallet_status: 'NOT_STARTED' })));
    const respuesta = new Subject<OnboardingStateResponse>();
    api.submitStep.and.returnValue(respuesta);
    const fixture = TestBed.createComponent(OnboardingComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    const c = fixture.componentInstance;
    c.registroForm.controls.document_number.setValue('TEST-0001');
    const p1 = c.submitRegistro();
    const p2 = c.submitRegistro();
    expect(api.submitStep).toHaveBeenCalledTimes(1);
    respuesta.next(estado());
    respuesta.complete();
    await Promise.all([p1, p2]);
  });
});
