// src/app/identificar/identificar.component.ts
import { Component, ElementRef, inject } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { focusFirstInvalid } from '../core/a11y';
import { SessionService } from '../core/session.service';

@Component({
  selector: 'app-identificar',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <h1>Identifícate</h1>
    <p>
      Este es un entorno de pruebas. Indica el identificador de usuario con el que quieres
      probar el onboarding.
    </p>
    <form [formGroup]="form" (ngSubmit)="submit()" novalidate class="panel">
      <div class="field">
        <label for="owner-id">Identificador de usuario</label>
        <p id="owner-id-hint" class="hint">
          De 1 a 128 caracteres: letras, números, punto, guion o guion bajo. Ejemplo: demo-user-1.
        </p>
        <input
          id="owner-id"
          type="text"
          formControlName="ownerId"
          autocomplete="off"
          maxlength="128"
          [attr.aria-invalid]="showError() ? 'true' : null"
          [attr.aria-describedby]="showError() ? 'owner-id-hint owner-id-error' : 'owner-id-hint'"
        />
        @if (showError()) {
          <p id="owner-id-error" class="field-error">{{ errorMessage() }}</p>
        }
      </div>
      <div class="actions">
        <button type="submit" class="btn">Entrar</button>
      </div>
    </form>
  `,
})
export class IdentificarComponent {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  readonly form = this.fb.group({
    ownerId: this.fb.control('', [Validators.required, Validators.pattern(/^[A-Za-z0-9._-]{1,128}$/)]),
  });

  showError(): boolean {
    const control = this.form.controls.ownerId;
    return control.invalid && (control.touched || control.dirty);
  }

  errorMessage(): string {
    return this.form.controls.ownerId.hasError('required')
      ? 'Ingresa un identificador.'
      : 'Usa de 1 a 128 caracteres: letras, números, punto, guion o guion bajo.';
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      focusFirstInvalid(this.host.nativeElement);
      return;
    }
    this.session.setOwner(this.form.controls.ownerId.value);
    void this.router.navigate(['/onboarding']);
  }
}
