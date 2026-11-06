import { formatPen, parsePenToCents } from './money';

describe('money', () => {
  it('formatea céntimos como soles', () => {
    expect(formatPen(100000)).toBe('S/ 1,000.00');
    expect(formatPen(1550)).toBe('S/ 15.50');
    expect(formatPen(0)).toBe('S/ 0.00');
  });

  it.each([
    ['15.50', 1550],
    ['15', 1500],
    ['0.01', 1],
    [' 8 ', 800],
  ])('convierte "%s" en %s céntimos', (text, cents) => {
    expect(parsePenToCents(text)).toBe(cents);
  });

  it.each(['', 'abc', '1.234', '-5', '1,5'])('rechaza "%s"', (text) => {
    expect(parsePenToCents(text)).toBeNull();
  });
});
