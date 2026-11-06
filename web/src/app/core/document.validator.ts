// src/app/core/document.validator.ts
import { AbstractControl, ValidationErrors } from '@angular/forms';

export const DOCUMENT_PREFIX = 'TEST-';
const SUFFIX_PATTERN = /^[A-Za-z0-9-]{1,59}$/;
const MAX_DOCUMENT_LENGTH = 64;

/** Espejo de la validación del servidor (el servidor sigue siendo la autoridad). */
export function testDocumentValidator(control: AbstractControl): ValidationErrors | null {
  const value: unknown = control.value;
  if (typeof value !== 'string' || value.length === 0) {
    return { required: true };
  }
  if (value.length > MAX_DOCUMENT_LENGTH) {
    return { maxlength: true };
  }
  if (!value.startsWith(DOCUMENT_PREFIX)) {
    return { notTest: true };
  }
  if (!SUFFIX_PATTERN.test(value.slice(DOCUMENT_PREFIX.length))) {
    return { suffix: true };
  }
  return null;
}

export function documentErrorMessage(errors: ValidationErrors | null): string | null {
  if (!errors) {
    return null;
  }
  if (errors['required']) {
    return 'Ingresa el número de documento.';
  }
  if (errors['maxlength']) {
    return 'El documento admite hasta 64 caracteres.';
  }
  if (errors['notTest']) {
    return 'El documento debe comenzar con TEST- (en mayúsculas). Ejemplo: TEST-0001.';
  }
  if (errors['suffix']) {
    return 'Después de TEST- usa de 1 a 59 caracteres: letras, números o guiones, sin espacios.';
  }
  return 'El documento no es válido.';
}
