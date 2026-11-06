import { TestBed } from '@angular/core/testing';
import { AuthService, NOT_REGISTERED_MESSAGE } from './auth.service';

describe('AuthService', () => {
  let auth: AuthService;

  beforeEach(() => {
    localStorage.clear();
    auth = TestBed.inject(AuthService);
  });

  describe('login', () => {
    it('acepta el usuario dummy admin con contraseña admin', () => {
      expect(auth.login('admin', 'admin')).toBeNull();
      expect(auth.user()).toMatchObject({ dni: 'admin', role: 'admin' });
    });

    it.each([
      ['', 'admin', 'Ingresa tu DNI.'],
      ['admin', '', 'Ingresa tu contraseña.'],
      ['admin', 'otra', 'DNI o contraseña incorrectos.'],
    ])('rechaza dni "%s" y contraseña "%s"', (dni, password, message) => {
      expect(auth.login(dni, password)).toBe(message);
      expect(auth.user()).toBeNull();
    });

    it('si el cliente no existe indica que debe registrarse', () => {
      expect(auth.login('12345678', 'admin')).toBe('Ups, registrate como nuevo usuario');
      expect(NOT_REGISTERED_MESSAGE).toBe('Ups, registrate como nuevo usuario');
      expect(auth.user()).toBeNull();
    });
  });

  describe('registro', () => {
    it.each([['1'], ['12345678'], [' 87654321 ']])('acepta el número de documento "%s"', (number) => {
      expect(auth.validateRegistration('DNI', number)).toBeNull();
    });

    it.each([
      ['DNI', '', 'Ingresa tu número de documento.'],
      ['DNI', '1234a678', 'solo admite dígitos'],
      ['DNI', '-1234567', 'solo admite dígitos'],
      ['DNI', '123456789', 'máximo 8 dígitos'],
      ['CE', '12345678', 'tipo de documento DNI'],
    ])('rechaza tipo "%s" y número "%s"', (type, number, text) => {
      expect(auth.validateRegistration(type, number)).toContain(text);
    });

    it('con el OTP 0000 abre la sesión del cliente nuevo', () => {
      expect(auth.confirmOtp('12345678', '0000')).toBeNull();
      expect(auth.user()).toEqual({ dni: '12345678', name: 'Cliente 12345678', role: 'customer' });
    });

    it('con un OTP incorrecto no abre sesión', () => {
      expect(auth.confirmOtp('12345678', '1234')).toContain('OTP no es correcto');
      expect(auth.user()).toBeNull();
    });
  });

  it('cerrar sesión borra el usuario', () => {
    auth.login('admin', 'admin');
    auth.logout();
    expect(auth.user()).toBeNull();
    expect(localStorage.getItem('wallet.auth')).toBeNull();
  });
});
