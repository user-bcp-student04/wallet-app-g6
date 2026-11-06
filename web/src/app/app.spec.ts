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

  const clickText = async (text: string) => {
    const found = [...root.querySelectorAll('button')].find((b) => b.textContent?.trim() === text);
    if (!found) throw new Error(`No hay botón "${text}"`);
    found.click();
    await tick();
  };

  const alertText = () => root.querySelector('[role="alert"]')?.textContent ?? '';

  const flushDashboard = async () => {
    http.expectOne(`${BASE}/wallets/wallet-demo`).flush({ id: 'wallet-demo', status: 'ACTIVE', balance: 100000, reserved: 0, available: 100000, currency: 'PEN' });
    http.expectOne(`${BASE}/payments?walletId=wallet-demo`).flush([]);
    await tick();
  };

  const login = async (dni: string, password: string) => {
    await type('input[name="dni"]', dni);
    await type('input[name="password"]', password);
    await submit();
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

  describe('registro', () => {
    it('sin sesión empieza en el registro con tipo de documento DNI y número de documento', () => {
      expect(root.textContent).toContain('Regístrate como cliente');
      expect((root.querySelector('select[name="documentType"]') as HTMLSelectElement).value).toBe('DNI');
      expect((root.querySelector('input[name="documentNumber"]') as HTMLInputElement).maxLength).toBe(8);
      expect(root.querySelector('input[name="password"]')).toBeNull();
    });

    it.each([
      ['', 'Ingresa tu número de documento'],
      ['12a45678', 'solo admite dígitos'],
      ['123456789', 'máximo 8 dígitos'],
    ])('con el número "%s" bloquea el registro', async (number, text) => {
      await type('input[name="documentNumber"]', number);
      await submit();
      expect(alertText()).toContain(text);
      expect(root.querySelector('input[name="otp"]')).toBeNull();
    });

    it('un registro válido indica que se envió un OTP de aprobación', async () => {
      await type('input[name="documentNumber"]', '12345678');
      await submit();
      expect(root.textContent).toContain('Se ha enviado un OTP de aprobación');
      expect(root.querySelector('input[name="otp"]')).not.toBeNull();
    });

    it('un OTP incorrecto no da acceso', async () => {
      await type('input[name="documentNumber"]', '12345678');
      await submit();
      await type('input[name="otp"]', '1111');
      await submit();
      expect(alertText()).toContain('OTP no es correcto');
      expect(root.querySelector('.dashboard')).toBeNull();
    });

    it('con el OTP 0000 entra al panel de saldo, movimientos y transferencias', async () => {
      await type('input[name="documentNumber"]', '12345678');
      await submit();
      await type('input[name="otp"]', '0000');
      await submit();
      await flushDashboard();
      expect(root.textContent).toContain('Saldo disponible');
      expect(root.textContent).toContain('Últimos movimientos');
      expect(root.textContent).toContain('Pago a contacto');
      expect(root.textContent).toContain('Pago con QR');
      expect(root.textContent).toContain('Cliente 12345678');
      expect(root.textContent).not.toContain('Consola de pruebas');
    });

    it('Volver regresa al formulario de registro', async () => {
      await type('input[name="documentNumber"]', '12345678');
      await submit();
      await clickText('Volver');
      expect(root.querySelector('input[name="documentNumber"]')).not.toBeNull();
    });
  });

  describe('login', () => {
    beforeEach(async () => {
      await clickText('Ya tengo cuenta, ingresar');
    });

    it('muestra DNI y contraseña', () => {
      expect(root.textContent).toContain('DNI');
      expect(root.textContent).toContain('Contraseña');
      expect(root.querySelector('.dashboard')).toBeNull();
    });

    it('un login vacío o con contraseña incorrecta no da acceso', async () => {
      await submit();
      expect(alertText()).toContain('Ingresa tu DNI');
      await login('admin', 'mala');
      expect(alertText()).toContain('incorrectos');
      expect(root.querySelector('.dashboard')).toBeNull();
    });

    it('si el cliente no existe muestra "Ups, registrate como nuevo usuario"', async () => {
      await login('12345678', 'cualquiera');
      expect(alertText()).toBe('Ups, registrate como nuevo usuario');
      expect(root.querySelector('.dashboard')).toBeNull();
    });

    it('desde el login se puede volver al registro', async () => {
      await clickText('¿Eres nuevo? Regístrate');
      expect(root.textContent).toContain('Regístrate como cliente');
    });

    it('con admin/admin muestra el saldo, movimientos y opciones de transferencia', async () => {
      await login('admin', 'admin');
      await flushDashboard();
      expect(root.textContent).toContain('Saldo disponible');
      expect(root.textContent).toContain('S/ 1,000.00');
      expect(root.textContent).toContain('Últimos movimientos');
      expect(root.textContent).toContain('Pago a contacto');
      expect(root.textContent).toContain('Pago con QR');
      expect(root.textContent).toContain('Consola de pruebas');
    });

    it('cerrar sesión vuelve al login', async () => {
      await login('admin', 'admin');
      await flushDashboard();
      await clickText('Cerrar sesión');
      expect(root.querySelector('input[name="password"]')).not.toBeNull();
    });
  });
});
