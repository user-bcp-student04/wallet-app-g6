import { TestBed } from '@angular/core/testing';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let auth: AuthService;

  beforeEach(() => {
    localStorage.clear();
    auth = TestBed.inject(AuthService);
  });

  it('acepta el usuario dummy admin con contraseña admin', () => {
    expect(auth.login('admin', 'admin')).toBeNull();
    expect(auth.user()).toMatchObject({ dni: 'admin', role: 'admin' });
  });

  it.each([
    ['', 'admin', 'Ingresa tu DNI.'],
    ['admin', '', 'Ingresa tu contraseña.'],
    ['admin', 'otra', 'DNI o contraseña incorrectos.'],
    ['12345678', 'admin', 'DNI o contraseña incorrectos.'],
  ])('rechaza dni "%s" y contraseña "%s"', (dni, password, message) => {
    expect(auth.login(dni, password)).toBe(message);
    expect(auth.user()).toBeNull();
  });

  it('cerrar sesión borra el usuario', () => {
    auth.login('admin', 'admin');
    auth.logout();
    expect(auth.user()).toBeNull();
    expect(localStorage.getItem('wallet.auth')).toBeNull();
  });
});
