// src/app/app.component.ts
import { DOCUMENT } from '@angular/common';
import { Component, ViewEncapsulation, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter, skip } from 'rxjs';

import { SessionService } from './core/session.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.component.html',
  encapsulation: ViewEncapsulation.None,
  styles: [
    `
      body { margin: 0; font-family: system-ui, sans-serif; color: #1f2937; background: #f9fafb; line-height: 1.5; }
      .app-header { display: flex; flex-wrap: wrap; gap: 1rem; align-items: center; justify-content: space-between; padding: 0.75rem 1.5rem; background: #111827; color: #ffffff; }
      .app-header a { color: #ffffff; }
      .app-header ul { display: flex; gap: 1rem; list-style: none; margin: 0; padding: 0; }
      .app-header a.active { font-weight: 700; text-decoration: underline; }
      .app-header p { margin: 0; }
      main { max-width: 52rem; margin: 0 auto; padding: 1.5rem; }
      main:focus { outline: none; }
      :focus-visible { outline: 3px solid #1d4ed8; outline-offset: 2px; }
      .app-header :focus-visible { outline-color: #fbbf24; }
      .skip-link { position: absolute; left: -999px; top: 0; background: #ffffff; color: #111827; padding: 0.5rem 1rem; z-index: 10; }
      .skip-link:focus { left: 0; }
      .btn { display: inline-block; font: inherit; padding: 0.5rem 1rem; border: 1px solid #1d4ed8; border-radius: 0.375rem; background: #1d4ed8; color: #ffffff; cursor: pointer; text-decoration: none; }
      .btn-secondary { background: #ffffff; color: #1d4ed8; }
      .btn-danger { background: #b42318; border-color: #b42318; }
      .btn-link { background: transparent; border-color: transparent; color: inherit; text-decoration: underline; padding: 0.25rem 0.5rem; }
      .btn[aria-disabled='true'] { opacity: 0.6; cursor: not-allowed; }
      .actions { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem; }
      .panel { background: #ffffff; border: 1px solid #d1d5db; border-radius: 0.5rem; padding: 1rem 1.25rem; margin: 1rem 0; }
      .field { margin: 1rem 0; }
      .field label { display: block; font-weight: 600; margin-bottom: 0.25rem; }
      .field input, .field select { font: inherit; padding: 0.5rem; width: 100%; max-width: 28rem; box-sizing: border-box; border: 1px solid #6b7280; border-radius: 0.375rem; }
      .field input[aria-invalid='true'], .field select[aria-invalid='true'] { border-color: #b42318; border-width: 2px; }
      .hint { color: #4b5563; font-size: 0.9rem; margin: 0.25rem 0; }
      .field-error { color: #b42318; font-weight: 600; margin: 0.25rem 0; }
      .alert { border-left: 6px solid; border-radius: 0.375rem; padding: 0.75rem 1rem; margin: 1rem 0; }
      .alert p { margin: 0.25rem 0; }
      .alert-error { background: #fdecea; color: #611a15; border-color: #b42318; }
      .alert-ok { background: #ecfdf3; color: #054f31; border-color: #027a48; }
      .alert-info { background: #eff6ff; color: #1e3a8a; border-color: #1d4ed8; }
      .steps { list-style: none; padding: 0; margin: 1rem 0; display: grid; gap: 0.5rem; }
      .steps li { display: flex; gap: 0.75rem; align-items: center; padding: 0.5rem 0.75rem; border: 1px solid #d1d5db; border-radius: 0.375rem; background: #ffffff; }
      .steps li[aria-current='step'] { border: 2px solid #1d4ed8; background: #eff6ff; font-weight: 700; }
      .badge { margin-left: auto; font-size: 0.85rem; border: 1px solid #6b7280; border-radius: 999px; padding: 0 0.6rem; }
      dl.data { display: grid; grid-template-columns: max-content 1fr; gap: 0.25rem 1rem; }
      dl.data dt { font-weight: 600; }
      dl.data dd { margin: 0; word-break: break-all; }
      h1, h2 { line-height: 1.2; }
      h2[tabindex='-1']:focus, p[tabindex='-1']:focus { outline: 3px solid #1d4ed8; outline-offset: 2px; }
    `,
  ],
})
export class AppComponent {
  readonly session = inject(SessionService);
  private readonly router = inject(Router);
  private readonly doc = inject(DOCUMENT);

  constructor() {
    // Tras cada navegación (salvo la inicial) el foco va al contenido principal.
    this.router.events
      .pipe(
        filter((event): event is NavigationEnd => event instanceof NavigationEnd),
        skip(1),
        takeUntilDestroyed(),
      )
      .subscribe(() => this.focusMain());
  }

  skipToContent(event: Event): void {
    event.preventDefault();
    this.focusMain();
  }

  changeOwner(): void {
    this.session.clear();
    void this.router.navigate(['/identificar']);
  }

  private focusMain(): void {
    this.doc.getElementById('contenido')?.focus();
  }
}
