import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { DashboardView } from './dashboard-view';

const BASE = environment.mockBaseUrl;
const WALLET = { id: 'wallet-demo', status: 'ACTIVE', balance: 100000, reserved: 1500, available: 98500, currency: 'PEN' };

const payment = (n: number, status = 'SUCCEEDED', recipient = 'contact-demo') => ({
  id: `pay_${n}`,
  wallet_id: 'wallet-demo',
  recipient,
  amount: n * 100,
  status,
  scenario: 'APPROVED',
  idem: `k${n}`,
});

describe('DashboardView', () => {
  let fixture: ComponentFixture<DashboardView>;
  let http: HttpTestingController;
  let root: HTMLElement;

  const tick = async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  };

  const load = async (payments: unknown[] = [], wallet: object = WALLET) => {
    http.expectOne(`${BASE}/wallets/wallet-demo`).flush(wallet);
    http.expectOne(`${BASE}/payments?walletId=wallet-demo`).flush(payments);
    await tick();
  };

  beforeEach(async () => {
    localStorage.clear();
    TestBed.configureTestingModule({
      imports: [DashboardView],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(DashboardView);
    root = fixture.nativeElement as HTMLElement;
    await tick();
  });

  afterEach(() => http.verify());

  it('muestra el saldo de la cuenta', async () => {
    await load();
    expect(root.querySelector('[data-testid="balance"]')?.textContent).toContain('S/ 985.00');
    expect(root.textContent).toContain('Saldo contable S/ 1,000.00');
    expect(root.textContent).toContain('Reservado S/ 15.00');
  });

  it('muestra los últimos 5 movimientos, el más reciente primero', async () => {
    await load([1, 2, 3, 4, 5, 6, 7].map((n) => payment(n)));
    const items = [...root.querySelectorAll('.movement-list li')].map((li) => li.textContent?.replace(/\s+/g, ' ').trim());
    expect(items).toHaveLength(5);
    expect(items[0]).toContain('S/ 7.00');
    expect(items[4]).toContain('S/ 3.00');
  });

  it('muestra destinatario y estado de cada movimiento', async () => {
    await load([payment(2, 'PENDING', 'merchant-demo')]);
    const text = root.querySelector('.movement-list')?.textContent ?? '';
    expect(text).toContain('Comercio de prueba');
    expect(text).toContain('Pendiente');
  });

  it('sin movimientos muestra un estado vacío', async () => {
    await load([]);
    expect(root.querySelector('.movement-list')?.textContent).toContain('Aún no tienes movimientos');
  });

  it('ofrece las opciones de transferencia: pago a contacto y pago con QR', async () => {
    await load();
    const labels = [...root.querySelectorAll('.action-grid button')].map((b) => b.textContent?.trim());
    expect(labels).toEqual(['Pago a contacto', 'Pago con QR']);
  });

  it('al elegir Pago con QR abre la transferencia con ese método', async () => {
    await load();
    (root.querySelectorAll('.action-grid button')[1] as HTMLButtonElement).click();
    await tick();
    expect(root.textContent).toContain('Método de transferencia');
    expect((root.querySelectorAll('input[type="radio"]')[1] as HTMLInputElement).checked).toBe(true);
  });

  it('al cerrar la transferencia recarga saldo y movimientos', async () => {
    await load();
    (root.querySelector('.action-grid button') as HTMLButtonElement).click();
    await tick();
    [...root.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Cancelar')?.click();
    await tick();
    await load([payment(1)]);
    expect(root.querySelectorAll('.movement-list li')).toHaveLength(1);
  });

  it('si falla la carga muestra un error accionable y permite reintentar', async () => {
    http.expectOne(`${BASE}/wallets/wallet-demo`).flush({ error: 'NOT_FOUND' }, { status: 404, statusText: 'Not Found' });
    http.expectOne(`${BASE}/payments?walletId=wallet-demo`).flush([]);
    await tick();
    expect(root.querySelector('[role="alert"]')?.textContent).toContain('No se encontró');
    (root.querySelector('.balance button') as HTMLButtonElement).click();
    await tick();
    await load();
    expect(root.querySelector('[data-testid="balance"]')).not.toBeNull();
  });
});
