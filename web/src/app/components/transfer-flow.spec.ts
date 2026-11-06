import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { TransferFlow } from './transfer-flow';

const BASE = environment.mockBaseUrl;
const PAYMENT = {
  id: 'pay_1',
  wallet_id: 'wallet-demo',
  recipient: 'contact-demo',
  amount: 1550,
  status: 'PENDING',
  scenario: 'APPROVED',
  idem: 'k',
};

describe('TransferFlow', () => {
  let fixture: ComponentFixture<TransferFlow>;
  let http: HttpTestingController;
  let root: HTMLElement;
  let closed: number;

  const tick = async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  };

  const button = (text: string): HTMLButtonElement => {
    const found = [...root.querySelectorAll('button')].find((b) => b.textContent?.trim() === text);
    if (!found) throw new Error(`No hay botón "${text}"`);
    return found;
  };

  const click = async (text: string) => {
    button(text).click();
    await tick();
  };

  const type = async (selector: string, value: string) => {
    const input = root.querySelector(selector) as HTMLInputElement;
    input.value = value;
    input.dispatchEvent(new Event('input'));
    await tick();
  };

  const create = async (available: number, method: 'contact' | 'qr' = 'contact') => {
    fixture = TestBed.createComponent(TransferFlow);
    fixture.componentRef.setInput('available', available);
    fixture.componentRef.setInput('initialMethod', method);
    fixture.componentInstance.closed.subscribe(() => closed++);
    root = fixture.nativeElement as HTMLElement;
    await tick();
  };

  const toCodeStep = async (amount: string) => {
    await click('CONTINUAR');
    await type('input[name="amount"]', amount);
    await click('CONTINUAR');
    await click('Continuar');
  };

  const currentCode = () => root.querySelector('.code')?.textContent?.trim() ?? '';

  beforeEach(() => {
    localStorage.clear();
    closed = 0;
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('empieza en el método de transferencia con las dos opciones', async () => {
    await create(100000);
    expect(root.textContent).toContain('Pago a contacto');
    expect(root.textContent).toContain('Pago con QR');
    expect(root.querySelector('li[aria-current="step"]')?.textContent).toContain('Método');
  });

  it('completa un pago a contacto: confirma, valida el código y muestra el resultado', async () => {
    await create(100000);
    await toCodeStep('15.50');
    expect(root.querySelector('li[aria-current="step"]')?.textContent).toContain('Validación');
    await type('input[name="code"]', currentCode());
    await click('Aprobar');

    const req = http.expectOne(`${BASE}/payments`);
    expect(req.request.headers.get('Idempotency-Key')).toBeTruthy();
    expect(req.request.body).toEqual({ walletId: 'wallet-demo', recipient: 'contact-demo', amountCents: 1550, currency: 'PEN' });
    req.flush(PAYMENT, { status: 202, statusText: 'Accepted' });
    http.expectOne(`${BASE}/payments/pay_1/resolve`).flush({ ...PAYMENT, status: 'SUCCEEDED' });
    await tick();

    expect(root.textContent).toContain('¡Listo! Tu transferencia fue exitosa');
    expect(root.textContent).toContain('S/ 15.50');
    await click('Cerrar');
    expect(closed).toBe(1);
  });

  it('con un monto inválido bloquea el avance', async () => {
    await create(100000);
    await click('CONTINUAR');
    await type('input[name="amount"]', 'abc');
    await click('CONTINUAR');
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('monto válido');
    expect(root.querySelector('li[aria-current="step"]')?.textContent).toContain('Datos');
  });

  it('con un monto mayor al saldo disponible bloquea el avance', async () => {
    await create(1000);
    await click('CONTINUAR');
    await type('input[name="amount"]', '20');
    await click('CONTINUAR');
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('Saldo insuficiente');
  });

  it('un código de validación incorrecto no crea el pago', async () => {
    await create(100000);
    await toCodeStep('5');
    await type('input[name="code"]', '000000X');
    await click('Aprobar');
    http.expectNone(`${BASE}/payments`);
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('El código no coincide');
  });

  it('rechazar en la confirmación cierra sin llamar a la API', async () => {
    await create(100000);
    await click('CONTINUAR');
    await type('input[name="amount"]', '5');
    await click('CONTINUAR');
    await click('Rechazar');
    expect(closed).toBe(1);
  });

  it('con 409 INSUFFICIENT_FUNDS del mock muestra el error y permite reintentar', async () => {
    await create(100000);
    await toCodeStep('5');
    await type('input[name="code"]', currentCode());
    await click('Aprobar');
    http.expectOne(`${BASE}/payments`).flush({ error: 'INSUFFICIENT_FUNDS' }, { status: 409, statusText: 'Conflict' });
    await tick();
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('Saldo insuficiente');
    expect(button('Aprobar').disabled).toBe(false);
  });

  it('con un pago pendiente tras resolver informa que está pendiente', async () => {
    await create(100000);
    await toCodeStep('5');
    await type('input[name="code"]', currentCode());
    await click('Aprobar');
    http.expectOne(`${BASE}/payments`).flush(PAYMENT, { status: 202, statusText: 'Accepted' });
    http.expectOne(`${BASE}/payments/pay_1/resolve`).flush({ status: 'PENDING', escalated: true }, { status: 202, statusText: 'Accepted' });
    await tick();
    expect(root.textContent).toContain('pendiente de confirmación');
  });

  it('pago con QR: genera un QR de prueba, lo valida e incluye qrId en el pago', async () => {
    await create(100000, 'qr');
    await click('CONTINUAR');
    await click('Generar QR de prueba');
    http.expectOne(`${BASE}/qrs`).flush({ id: 'qr_1', payload: 'qrmock:qr_1', amountCents: null, currency: 'PEN' }, { status: 201, statusText: 'Created' });
    await tick();
    expect((root.querySelector('input[name="qr"]') as HTMLInputElement).value).toBe('qrmock:qr_1');

    await click('Validar QR');
    http.expectOne(`${BASE}/qrs/resolve`).flush({ merchantId: 'merchant-demo', merchantName: 'Comercio de prueba', amountCents: null, currency: 'PEN' });
    await tick();
    expect(root.textContent).toContain('Comercio de prueba');

    await type('input[name="amount"]', '8');
    await click('CONTINUAR');
    await click('Continuar');
    await type('input[name="code"]', currentCode());
    await click('Aprobar');
    const req = http.expectOne(`${BASE}/payments`);
    expect(req.request.body).toEqual({ walletId: 'wallet-demo', recipient: 'merchant-demo', amountCents: 800, currency: 'PEN', qrId: 'qr_1' });
    req.flush({ ...PAYMENT, recipient: 'merchant-demo', amount: 800, status: 'SUCCEEDED' }, { status: 200, statusText: 'OK' });
    await tick();
    expect(root.textContent).toContain('¡Listo!');
  });

  it('pago con QR: exige validar el QR antes de continuar', async () => {
    await create(100000, 'qr');
    await click('CONTINUAR');
    await click('CONTINUAR');
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('Valida el QR');
  });

  it('pago con QR vencido muestra el error del mock', async () => {
    await create(100000, 'qr');
    await click('CONTINUAR');
    await type('input[name="qr"]', 'qrmock:old');
    await click('Validar QR');
    http.expectOne(`${BASE}/qrs/resolve`).flush({ error: 'QR_EXPIRED' }, { status: 410, statusText: 'Gone' });
    await tick();
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('El QR venció');
  });
});
