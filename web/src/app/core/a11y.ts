// src/app/core/a11y.ts
/** Lleva el foco al primer campo inválido del contenedor. */
export function focusFirstInvalid(root: HTMLElement): void {
  root.querySelector<HTMLElement>('input.ng-invalid, select.ng-invalid')?.focus();
}

/** Lleva el foco a un elemento cuando Angular ya actualizó el DOM. */
export function focusLater(root: HTMLElement, selector: string): void {
  setTimeout(() => root.querySelector<HTMLElement>(selector)?.focus(), 0);
}
