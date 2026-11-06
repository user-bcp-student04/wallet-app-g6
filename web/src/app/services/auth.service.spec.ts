import { TestBed } from '@angular/core/testing';
import { AuthService, NOT_REGISTERED_MESSAGE } from './auth.service';

describe('AuthService', () => {
  let auth: AuthService;

  beforeEach(() => {
    localStorage.clear();
    auth = TestBed.inject(AuthService);
  });

  describe('login', () => {
    it('acepta el usuario dummy admin con contraseña admin', async () => {
      expect(await auth.login('admin', 'admin')).toBeNull();
      expect(auth.user()).toMatchObject({ dni: 'admin', role: 'admin' });
    });

    it.each([
      ['', 'admin', 'Ingresa tu DNI.'],
      ['admin', '', 'Ingresa tu contraseña.'],
      ['admin', 'otra', 'DNI o contraseña incorrectos.'],
    ])('rechaza dni "%s" y contraseña "%s"', async (dni, password, message) => {
      expect(await auth.login(dni, password)).toBe(message);
      expect(auth.user()).toBeNull();
    });

    it('si el cliente no existe indica que debe registrarse', async () => {
      expect(await auth.login('12345678', 'admin')).toBe('Ups, registrate como nuevo usuario');
      expect(NOT_REGISTERED_MESSAGE).toBe('Ups, registrate como nuevo usuario');
      expect(auth.user()).toBeNull();
    });
  });

  describe('registro', () => {
    it.each([['1'], ['12345678'], [' 87654321 ']])('acepta el número de documento "%s"', (number) => {
      expect(auth.validateRegistration('DNI', number, 'clave')).toBeNull();
    });

    it.each([
      ['DNI', '', 'clave', 'Ingresa tu número de documento.'],
      ['DNI', '1234a678', 'clave', 'solo admite dígitos'],
      ['DNI', '-1234567', 'clave', 'solo admite dígitos'],
      ['DNI', '123456789', 'clave', 'máximo 8 dígitos'],
      ['CE', '12345678', 'clave', 'tipo de documento DNI'],
      ['DNI', '12345678', '', 'Ingresa tu contraseña.'],
      ['DNI', '12345678', 'abc', 'al menos 4 caracteres'],
    ])('rechaza tipo "%s", número "%s" y contraseña "%s"', (type, number, password, text) => {
      expect(auth.validateRegistration(type, number, password)).toContain(text);
    });

    it('con el OTP 0000 abre la sesión del cliente nuevo', async () => {
      expect(await auth.confirmOtp('12345678', 'clave', '0000')).toBeNull();
      expect(auth.user()).toEqual({ dni: '12345678', name: 'Cliente 12345678', role: 'customer' });
    });

    it('con un OTP incorrecto no abre sesión ni guarda al cliente', async () => {
      expect(await auth.confirmOtp('12345678', 'clave', '1234')).toContain('OTP no es correcto');
      expect(auth.user()).toBeNull();
      expect(localStorage.getItem('wallet.clients')).toBeNull();
    });

    it('guarda la contraseña derivada y nunca en texto plano', async () => {
      await auth.confirmOtp('12345678', 'clave-secreta', '0000');
      const stored = localStorage.getItem('wallet.clients') ?? '';
      expect(stored).toContain('12345678');
      expect(stored).not.toContain('clave-secreta');
    });

    it('el cliente registrado puede iniciar sesión con su contraseña', async () => {
      await auth.confirmOtp('12345678', 'clave', '0000');
      auth.logout();
      expect(await auth.login('12345678', 'otra')).toBe('DNI o contraseña incorrectos.');
      expect(auth.user()).toBeNull();
      expect(await auth.login('12345678', 'clave')).toBeNull();
      expect(auth.user()).toMatchObject({ dni: '12345678', role: 'customer' });
    });

    it('un DNI ya registrado no se vuelve a registrar', async () => {
      await auth.confirmOtp('12345678', 'clave', '0000');
      expect(auth.validateRegistration('DNI', '12345678', 'otra-clave')).toContain('ya está registrado');
    });
  });

  it('cerrar sesión borra el usuario', async () => {
    await auth.login('admin', 'admin');
    auth.logout();
    expect(auth.user()).toBeNull();
    expect(localStorage.getItem('wallet.auth')).toBeNull();
  });
});
