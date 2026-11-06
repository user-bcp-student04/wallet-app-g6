export function formatPen(cents: number): string {
  const sign = cents < 0 ? '-' : '';
  const value = Math.abs(cents) / 100;
  return `${sign}S/ ${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/** Convierte "15.50" en 1550 céntimos; null si el texto no es un importe válido. */
export function parsePenToCents(text: string): number | null {
  const value = text.trim();
  if (!/^\d+(\.\d{1,2})?$/.test(value)) return null;
  return Math.round(Number(value) * 100);
}

export const RECIPIENT_LABELS: Record<string, string> = {
  'contact-demo': 'Contacto demo',
  'merchant-demo': 'Comercio de prueba',
};
