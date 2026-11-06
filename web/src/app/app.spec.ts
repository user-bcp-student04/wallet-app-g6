import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { environment } from '../environments/environment';
import { App } from './app';

const BASE = environment.mockBaseUrl;

describe('App', () => {
  let fixture: ComponentFixture<App>;
  let http: HttpTestingController;
  let root: HTMLElement;

  const tick = async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  };

  const type = async (selector: string, value: string) => {
    const input = root.querySelector(selector) as HTMLInputElement;
    input.value = value;
    input.dispatchEvent(new Event('input'));
    await tick();
  };

  const submit = async () => {
    (root.querySelector('form') as HTMLFormElement).dispatchEvent(new Event('submit', { cancelable: true }));
    await tick();
  };

  beforeEach(async () => {
    localStorage.clear();
    TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(App);
    root = fixture.nativeElement as HTMLElement;
    await tick();
  });

  afterEach(() => http.verify());

  const login = async (dni: string, password: string) => {
    await type('input[name="dni"]', dni);
    await type('input[name="password"]', password);
    await submit();
  };

  const flushDashboard = async () => {
    http.expectOne(`${BASE}/wallets/wallet-demo`).flush({ id: 'wallet-demo', status: 'ACTIVE', balance: 100000, reserved: 0, available: 100000, currency: 'PEN' });
    http.expectOne(`${BASE}/payments?walletId=wallet-demo`).flush([]);
    await tick();
  };

  it('sin sesión muestra solo el login con DNI y contraseña', () => {
    expect(root.querySelector('form')).not.toBeNull();
    expect(root.textContent).toContain('DNI');
    expect(root.textContent).toContain('Contraseña');
    expect(root.querySelector('.dashboard')).toBeNull();
  });

  it('un login vacío o incorrecto no da acceso y muestra el motivo', async () => {
    await submit();
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('Ingresa tu DNI');
    await login('admin', 'mala');
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('incorrectos');
    expect(root.querySelector('.dashboard')).toBeNull();
  });

  it('con admin/admin muestra el saldo, movimientos y opciones de transferencia', async () => {
    await login('admin', 'admin');
    await flushDashboard();
    expect(root.textContent).toContain('Saldo disponible');
    expect(root.textContent).toContain('S/ 1,000.00');
    expect(root.textContent).toContain('Últimos movimientos');
    expect(root.textContent).toContain('Pago a contacto');
    expect(root.textContent).toContain('Pago con QR');
    expect(root.querySelector('form')).toBeNull();
  });

  it('cerrar sesión vuelve al login', async () => {
    await login('admin', 'admin');
    await flushDashboard();
    ([...root.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Cerrar sesión') as HTMLButtonElement).click();
    await tick();
    expect(root.querySelector('form')).not.toBeNull();
  });
});
