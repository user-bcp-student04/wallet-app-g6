// src/app/app.routes.ts
import { provideHttpClient } from '@angular/common/http';
import { Routes } from '@angular/router';

import { MockApiService } from './core/mock-api.service';
import { ownerGuard } from './core/owner.guard';

export const routes: Routes = [
  {
    path: '',
    // Ruta padre sin componente: provee HttpClient y MockApiService a todas las pantallas.
    providers: [provideHttpClient(), MockApiService],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'onboarding' },
      {
        path: 'identificar',
        loadComponent: () =>
          import('./identificar/identificar.component').then((m) => m.IdentificarComponent),
      },
      {
        path: 'onboarding',
        canActivate: [ownerGuard],
        loadComponent: () =>
          import('./onboarding/onboarding.component').then((m) => m.OnboardingComponent),
      },
      {
        path: 'pagos',
        canActivate: [ownerGuard],
        loadComponent: () => import('./pagos/pagos.component').then((m) => m.PagosComponent),
      },
      {
        path: 'consola',
        canActivate: [ownerGuard],
        loadComponent: () => import('./consola/consola.component').then((m) => m.ConsolaComponent),
      },
    ],
  },
  { path: '**', redirectTo: 'onboarding' },
];
