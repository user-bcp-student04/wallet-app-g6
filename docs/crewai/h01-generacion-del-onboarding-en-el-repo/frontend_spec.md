# frontend_spec.md

## 1. Alcance y fuentes

- **Fuentes.** El Issue H01 (tareas 2.2 a 2.8), `user_story.md` del Arquitecto y `backend_spec.md`. No tengo el contenido de `spec.md` (P-1), así que los criterios son los derivados por el Arquitecto.
- **El frontend cambia.** Se implementan las partes de frontend de las tareas:
  - **2.2:** `MockApiService` tipado y `SessionService` único.
  - **2.3:** presentación del estado de wallet, del bloqueo de pasos, del documento `TEST-` y de los mensajes accionables.
  - **2.4:** interfaz de KYC (crear, consultar y decidir sobre `PENDING`).
  - **2.6:** flujo guiado y acceso a pagos de bajo monto.
  - **2.7:** consola de servicios y reset con confirmación.
- **Sin interfaz en esta entrega.** 2.5 (eventos y duración) y 2.8 (analítica mensual) son solo backend y no exponen endpoint. El frontend solo muestra `duration_seconds` de `GET /onboarding`.
- **Contrato consumido sin inventar.** Todo sale de `schemas.py` y de la sección 3 de `backend_spec.md`. Las rutas y campos provisionales (S-4, P-3, P-4) están marcados en la sección 11.
- **Pagos.** El contrato no define endpoints ni umbral de pagos. La pantalla `/pagos` solo confirma o bloquea el acceso según `low_amount_payments_enabled`.
- **Dependencias.** No se añade ningún paquete npm. Se usa solo Angular 17 (`@angular/common/http`, `forms`, `router`) y `rxjs`.

## 2. Endpoints consumidos (todos vía `MockApiService`)

| Método | Ruta | Request (interfaz) | Response (interfaz) | Uso en la UI |
|---|---|---|---|---|
| GET | `/health` | `HealthRequest` (sin entrada) | `HealthResponse` | Consola |
| GET | `/scenarios` | `ScenariosRequest` (sin entrada) | `ScenariosResponse` | Consola y selector de escenario KYC |
| GET | `/support/cases` | `SupportCasesRequest` (sin entrada) | `SupportCasesResponse` | Consola; recuperar verificación `PENDING` tras recargar |
| POST | `/kyc/verifications` | `CreateVerificationRequest` | `VerificationResponse` | Paso KYC |
| GET | `/kyc/verifications/{verification_id}` | `GetVerificationRequest` | `VerificationResponse` | «Actualizar estado» |
| POST | `/kyc/verifications/{verification_id}/decision` | `DecideVerificationRequest` | `VerificationResponse` | Aprobar o rechazar una verificación `PENDING` |
| GET | `/onboarding` | `GetOnboardingRequest` (sin entrada) | `OnboardingStateResponse` | Flujo guiado y pagos |
| POST | `/onboarding/steps/{step_id}` | `SubmitStepRequest` | `OnboardingStateResponse` | Registro, KYC y activación |
| POST | `/control/reset` | `ResetRequest` (sin cuerpo) | `ResetResponse` | Consola, con confirmación |

**Identidad.** Cada llamada envía la cabecera `X-Owner-Id` con el identificador guardado en `SessionService`. El propietario nunca va en el cuerpo ni en la URL.

## 3. Archivos entregados

Todos están bajo `src/app/`.

| Archivo | Responsabilidad |
|---|---|
| `app.routes.ts` | Rutas y providers HTTP |
| `app.component.ts` y `.html` | Cabecera, navegación, «saltar al contenido» y `<router-outlet>` |
| `core/api.models.ts` | Interfaces de request y response por endpoint |
| `core/mock-api.service.ts` | Cliente tipado y mapeo de errores `{code,message}` |
| `core/session.service.ts` | Sesión única (identificador, wallet cacheada, última verificación) |
| `core/owner.guard.ts` | Exige identificador para entrar a las pantallas |
| `core/document.validator.ts` | Validación del documento `TEST-` y sus mensajes |
| `core/labels.ts` | Textos legibles de estados y pasos |
| `core/a11y.ts` | Utilidades de foco |
| `identificar/identificar.component.ts` | Captura del identificador de usuario |
| `onboarding/onboarding.component.ts` y `.html` | Flujo guiado |
| `consola/consola.component.ts` y `.html` | Consola de servicios y reset |
| `pagos/pagos.component.ts` | Acceso a pagos de bajo monto según el estado de la wallet |

**Providers HTTP.** No regeneré `main.ts`. `app.routes.ts` declara en una ruta padre sin componente `provideHttpClient()` y `MockApiService`. Así funciona aunque `main.ts` no los tenga, y no choca si ya existen. `SessionService` es `providedIn: 'root'`, por lo que sigue siendo único.

## 4. Campos y validaciones

| Pantalla | Campo | Reglas en cliente (espejo del servidor) | Mensaje |
|---|---|---|---|
| Identificar | Identificador de usuario (`ownerId`) | Obligatorio; `^[A-Za-z0-9._-]{1,128}$` | «Ingresa un identificador.» / «Usa de 1 a 128 caracteres: letras, números, punto, guion o guion bajo.» |
| Registro | `document_number` | Obligatorio; máx. 64; empieza por `TEST-` (mayúsculas); tras el prefijo, 1 a 59 caracteres `[A-Za-z0-9-]` | «Ingresa el número de documento.» / «El documento debe comenzar con TEST- (en mayúsculas). Ejemplo: TEST-0001.» / «Después de TEST- usa de 1 a 59 caracteres: letras, números o guiones, sin espacios.» |
| KYC | `document_number` | Igual que en Registro | Igual que en Registro |
| KYC | `scenario` | Obligatorio; opciones cargadas desde `GET /scenarios` (`APPROVED`, `REJECTED`, `PENDING`, `EXPIRED`) | «Selecciona un escenario.» |

- La validación del cliente es una ayuda de usabilidad. El servidor sigue siendo la autoridad y sus errores se muestran tal cual.
- El valor del documento no se recorta ni se modifica. Un espacio se rechaza, igual que en el servidor.

## 5. Acciones y mensajes

| Acción | Llamada | Éxito (`role="status"`) |
|---|---|---|
| Entrar | Ninguna; guarda el identificador en `SessionService` | Navega a `/onboarding` |
| Continuar (registro) | `POST /onboarding/steps/registro` con `{document_number}` | «Registro completado. Continúa con la verificación KYC.» |
| Crear verificación | `POST /kyc/verifications`, luego `GET /onboarding` para refrescar | Según el estado: aprobada, pendiente, rechazada o expirada, con la acción a seguir |
| Aprobar o Rechazar | `POST /kyc/verifications/{id}/decision`, luego refresco | «Decisión registrada: verificación aprobada.» o «…rechazada.» |
| Actualizar estado | `GET /kyc/verifications/{id}` | «Estado actualizado.» |
| Completar paso de verificación | `POST /onboarding/steps/kyc` con `{}` | «Verificación completada. Ya puedes activar tu wallet.» |
| Activar wallet | `POST /onboarding/steps/activacion` con `{}` | «¡Wallet activa! Ya puedes acceder a pagos de bajo monto.» |
| Ejecutar servicio (consola) | `GET /health`, `/scenarios` o `/support/cases` | Resultado legible en pantalla |
| Reiniciar mi estado (consola) | Confirmación en pantalla, luego `POST /control/reset` | «Estado reiniciado. Puedes empezar el onboarding de nuevo.» |

## 6. Estados por pantalla

| Estado | Onboarding | Consola | Pagos |
|---|---|---|---|
| **Carga** | «Cargando tu progreso…» (`role="status"`); botones con «Guardando…», «Creando…», etc. y `aria-busy` | «Ejecutando…» en el servicio activo | «Verificando el estado de tu wallet…» |
| **Vacío** | Sin escenarios: «No hay escenarios disponibles.» | Escenarios: «El API no devolvió escenarios.» Casos: «No hay casos de soporte para tu usuario.» | No aplica |
| **Éxito** | Mensajes de la sección 5; al terminar, panel «Wallet activa» con duración | Resultado por servicio; confirmación de reset | «Acceso habilitado» |
| **Error** | `role="alert"` con el `message` del API más «Código: X», y «Reintentar» si falló la carga | Alerta por servicio con `message` y código | «Acceso bloqueado» con el estado actual, o error con «Reintentar» |

Si la lista de pasos llega con `current_step = null`, se muestra el panel de wallet activa.

### Errores del API → mensaje

Siempre se muestra el `message` del API. Si no hay cuerpo `{code,message}` válido, se usa un mensaje por defecto.

| Situación | `code` | Mensaje mostrado |
|---|---|---|
| Sin red o servicio caído (status 0) | `NETWORK_ERROR` | «No se pudo conectar con el servicio. Revisa tu conexión e inténtalo de nuevo.» |
| 401 | `UNAUTHENTICATED` | El `message` del API. Además se limpia la sesión y se redirige a `/identificar` |
| 404, 409 (`STEP_BLOCKED`, `VERIFICATION_NOT_PENDING`, `LIMIT_REACHED`), 413, 422, 500 | Los del contrato | El `message` del API |
| Sin cuerpo válido | `HTTP_ERROR` | Mensaje por defecto según el estado HTTP |

## 7. Prevención de envíos duplicados

- Onboarding y consola usan una señal `busy` o `running` con la acción en curso. Mientras no es nula, cualquier otra acción retorna sin llamar al API.
- Los botones usan `aria-disabled="true"` y `aria-busy`, en lugar de `disabled`, para no perder el foco. Además el manejador ignora el clic.
- El envío por `Enter` en un formulario pasa por el mismo manejador protegido.
- Tras crear la verificación o decidir sobre ella, el refresco de `GET /onboarding` va dentro de la misma acción bloqueada. Si ese refresco falla, la acción principal sigue contando como éxito.

## 8. Accesibilidad

- Cada control tiene `<label for>` y un texto de ayuda enlazado con `aria-describedby`. Los errores de campo se enlazan igual y el campo lleva `aria-invalid`.
- Al enviar con errores, el foco va al primer campo inválido.
- El paso actual lleva `aria-current="step"` y su estado se indica con texto («Paso actual», «Completado», «Bloqueado»), no solo con color.
- Las alertas de error usan `role="alert"` y las de éxito `role="status"`. Los contenedores están siempre presentes para que se anuncien los cambios. Cada mensaje lleva un prefijo textual («Error:», «Listo:»).
- Al avanzar de paso, el foco se mueve al encabezado del nuevo panel (`tabindex="-1"`).
- Hay un enlace «Saltar al contenido» y el foco va a `<main>` tras cada navegación.
- El foco es visible en todos los elementos mediante `:focus-visible` con contorno de 3 px.
- Todo se maneja con teclado. La confirmación de reset es un grupo en la página, no un diálogo nativo:
  - Al abrirla, el foco va a su texto.
  - `Esc` o «Cancelar» la cierra y devuelven el foco al botón que la abrió.
- El acceso a pagos bloqueado es un botón con `aria-disabled` y una explicación enlazada, de modo que sigue siendo alcanzable con teclado.

## 9. Sesión y estado

- `SessionService` es el único dueño de la sesión: `ownerId` (persistido en `sessionStorage`, clave `wallet.ownerId`), `wallet` cacheada y `verification` (última verificación).
- Al cambiar de usuario o reiniciar, se descartan la wallet y la verificación cacheadas.
- Si la wallet está en `KYC_PENDING` y no hay verificación en sesión (por ejemplo tras recargar), el flujo la recupera con `GET /support/cases` y `GET /kyc/verifications/{id}`.

## 10. Cómo comprobar el recorrido y sus errores (NO EJECUTADO)

Nada de esto se ha ejecutado. Conserva la salida real al verificarlo.

**Preparación**
1. Levanta el API: `cd api && uvicorn app.main:app --reload`.
2. Levanta el frontend con `ng serve`. El API no configura CORS y el cliente envía `X-Owner-Id`, así que el frontend debe servirse bajo el mismo origen. Usa un proxy de desarrollo (`ng serve --proxy-config <archivo>`) hacia `http://127.0.0.1:8000`. `API_BASE_URL` queda vacío por defecto. Ese archivo de proxy no forma parte de esta entrega.

**Recorrido feliz**
1. Abre `/`. Sin identificador, redirige a `/identificar`. Escribe `demo-user-1` y pulsa «Entrar».
2. Verás el paso 1 como «Paso actual» y los otros dos como «Bloqueado». El acceso a pagos aparece bloqueado.
3. En Registro escribe `TEST-0001` y pulsa «Continuar». Aparece el mensaje de éxito y el foco pasa al paso 2.
4. En KYC elige `APPROVED` y documento `TEST-0001`, y pulsa «Crear verificación». Pulsa «Completar paso de verificación».
5. Pulsa «Activar wallet». Aparece «Wallet activa», la duración en segundos y el enlace a pagos. En `/pagos` verás «Acceso habilitado».

**Errores y estados límite**
1. **Documento inválido (cliente).** Escribe `12345678` y pulsa «Continuar». No se envía la petición. Verás el mensaje de `TEST-` y el foco va al campo. Prueba también `test-1` y `TEST-` sin sufijo.
2. **Doble clic.** Pulsa «Continuar» o «Activar wallet» dos veces seguidas con red lenta (DevTools → Network → Slow 3G). Debe verse una sola petición.
3. **`STEP_BLOCKED`.** Con un usuario nuevo, crea una verificación `REJECTED` y pulsa «Completar paso de verificación». Verás el mensaje 409 del API pidiendo crear una nueva. Repite con `PENDING`: el mensaje indica que está pendiente.
4. **`PENDING` y decisión.** Crea una `PENDING`. Prueba «Actualizar estado», «Aprobar» y luego «Completar paso».
5. **`VERIFICATION_NOT_PENDING`.** Abre dos pestañas con el mismo usuario y una verificación `PENDING`. Decide en una. En la otra, pulsa «Aprobar» sin recargar y verás el 409.
6. **Recuperación.** Con una verificación `PENDING`, recarga la página. El panel de verificación debe reaparecer.
7. **`NETWORK_ERROR`.** Detén el API y pulsa cualquier acción. Verás el mensaje de conexión y, al recargar, «Reintentar».
8. **`UNAUTHENTICATED`.** En DevTools → Application → Session Storage, cambia `wallet.ownerId` por un valor con espacios o caracteres no permitidos y ejecuta una acción. Verás el error y la redirección a `/identificar`.
9. **`LIMIT_REACHED`.** Crea 51 verificaciones. La 51 debe mostrar el mensaje 409 indicando usar el reset.
10. **Consola.** En `/consola` ejecuta cada servicio por separado y comprueba el resultado y el estado vacío (sin escenarios ni casos). Con el API detenido, comprueba el error legible por servicio.
11. **Reset.** Pulsa «Reiniciar mi estado…». Verifica que:
    - `Esc` o «Cancelar» cierran sin llamar al API.
    - «Sí, reiniciar» llama a `POST /control/reset`.
    - Tras el reset, `/onboarding` vuelve al estado inicial.
12. **Teclado.** Recorre todo con `Tab`, `Shift+Tab`, `Enter`, `Space` y `Esc`, y comprueba que el foco siempre es visible.

**Pruebas automáticas.** No se entregan. Si se añaden, deben cubrir al menos:
- una sola instancia de `SessionService`;
- el mapeo de errores de `MockApiService`;
- el validador de documento;
- el bloqueo de duplicados;
- la confirmación previa al reset.

## 11. Supuestos y pendientes

- **Rutas y campos provisionales.** Los endpoints de la sección 3.2 del Arquitecto (S-4), los campos de KYC, los cuatro escenarios, los pasos (`registro`, `kyc`, `activacion`) y los estados de wallet son los del backend, sin confirmar con `spec.md` (P-1, P-3, P-4). Si cambian, se actualizan `api.models.ts` y las etiquetas de `labels.ts`.
- **Identidad (P-9).** La credencial es la cabecera `X-Owner-Id`, una credencial de mock introducida por el usuario. Sustituirla por el mecanismo real solo afecta a `SessionService` y `MockApiService`.
- **Base URL y CORS.** Se asume mismo origen mediante proxy. El backend no define CORS.
- **Pagos (P-6).** No hay endpoint ni umbral de «bajo monto». `/pagos` solo refleja `low_amount_payments_enabled`.
- **Eventos y analítica (2.5, 2.8).** Sin pantalla ni consumo. No existen endpoints públicos (S-6, P-8).
- **Mensajes de éxito de la interfaz.** Los textos de la sección 5 son decisiones de interfaz.
- **Idioma de fechas.** La fecha usa el formato `dd/MM/yyyy HH:mm:ss` con la localización por defecto de Angular.
- **Alcance de la consola.** Los tres servicios se ejecutan de uno en uno. Mientras uno corre, los demás quedan bloqueados.

---

# Código

```typescript
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
```

```typescript
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
```

```html
<!-- src/app/app.component.html -->
<a class="skip-link" href="#contenido" (click)="skipToContent($event)">Saltar al contenido</a>

<header class="app-header">
  <p><strong>Wallet · Onboarding de pruebas</strong></p>
  @if (session.isIdentified()) {
    <nav aria-label="Principal">
      <ul>
        <li><a routerLink="/onboarding" routerLinkActive="active" ariaCurrentWhenActive="page">Onboarding</a></li>
        <li><a routerLink="/pagos" routerLinkActive="active" ariaCurrentWhenActive="page">Pagos de bajo monto</a></li>
        <li><a routerLink="/consola" routerLinkActive="active" ariaCurrentWhenActive="page">Consola de servicios</a></li>
      </ul>
    </nav>
    <p>
      Usuario: <strong>{{ session.ownerId() }}</strong>
      <button type="button" class="btn btn-link" (click)="changeOwner()">Cambiar usuario</button>
    </p>
  }
</header>

<main id="contenido" tabindex="-1">
  <router-outlet />
</main>
```

```typescript
// src/app/core/api.models.ts
// Espejo en TypeScript de api/app/schemas.py. Una interfaz de request y una de response por endpoint.

export type KycScenario = 'APPROVED' | 'REJECTED' | 'PENDING' | 'EXPIRED';
export type VerificationStatus = 'APPROVED' | 'REJECTED' | 'PENDING' | 'EXPIRED';
export type KycDecision = 'APPROVED' | 'REJECTED';
export type WalletStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'KYC_PENDING' | 'KYC_FAILED' | 'ACTIVE';
export type StepId = 'registro' | 'kyc' | 'activacion';
export type StepStatus = 'COMPLETED' | 'CURRENT' | 'LOCKED';

/** Cuerpo de error único del API. */
export interface ApiErrorBody {
  code: string;
  message: string;
}

/** Error ya normalizado para la interfaz (status 0 = sin conexión). */
export interface ApiErrorView extends ApiErrorBody {
  status: number;
}

// GET /health (sin entrada)
export type HealthRequest = void;
export interface HealthResponse {
  status: string;
}

// GET /scenarios (sin entrada)
export type ScenariosRequest = void;
export interface ScenarioItem {
  name: KycScenario;
  description: string;
}
export interface ScenariosResponse {
  scenarios: ScenarioItem[];
}

// GET /support/cases (sin entrada)
export type SupportCasesRequest = void;
export interface SupportCase {
  verification_id: string;
  status: VerificationStatus;
  message: string;
}
export interface SupportCasesResponse {
  cases: SupportCase[];
}

// Respuesta común de KYC
export interface VerificationResponse {
  verification_id: string;
  document_number: string;
  scenario: KycScenario;
  status: VerificationStatus;
  created_at: string;
  decided_at: string | null;
}

// POST /kyc/verifications
export interface CreateVerificationRequest {
  document_number: string;
  scenario: KycScenario;
}

// GET /kyc/verifications/{verification_id}
export interface GetVerificationRequest {
  verification_id: string;
}

// POST /kyc/verifications/{verification_id}/decision
export interface DecideVerificationRequest {
  verification_id: string;
  decision: KycDecision;
}

// Respuesta común de onboarding
export interface StepInfo {
  id: StepId;
  order: number;
  status: StepStatus;
}
export interface OnboardingStateResponse {
  wallet_status: WalletStatus;
  current_step: StepId | null;
  steps: StepInfo[];
  low_amount_payments_enabled: boolean;
  duration_seconds: number | null;
}

// GET /onboarding (sin entrada)
export type GetOnboardingRequest = void;

// POST /onboarding/steps/{step_id}  (document_number solo en 'registro')
export interface SubmitStepRequest {
  step_id: StepId;
  document_number?: string;
}

// POST /control/reset (sin cuerpo)
export type ResetRequest = void;
export interface ResetResponse {
  status: string;
}
```

```typescript
// src/app/core/session.service.ts
import { Injectable, computed, signal } from '@angular/core';

import { OnboardingStateResponse, VerificationResponse } from './api.models';

const OWNER_STORAGE_KEY = 'wallet.ownerId';

function readStoredOwner(): string | null {
  try {
    return sessionStorage.getItem(OWNER_STORAGE_KEY);
  } catch {
    return null;
  }
}

function writeStoredOwner(value: string | null): void {
  try {
    if (value === null) {
      sessionStorage.removeItem(OWNER_STORAGE_KEY);
    } else {
      sessionStorage.setItem(OWNER_STORAGE_KEY, value);
    }
  } catch {
    // Sin almacenamiento disponible: la sesión vive solo en memoria.
  }
}

/** Única fuente de sesión del flujo (singleton). */
@Injectable({ providedIn: 'root' })
export class SessionService {
  private readonly ownerIdState = signal<string | null>(readStoredOwner());
  private readonly walletState = signal<OnboardingStateResponse | null>(null);
  private readonly verificationState = signal<VerificationResponse | null>(null);

  readonly ownerId = this.ownerIdState.asReadonly();
  readonly isIdentified = computed(() => this.ownerIdState() !== null);
  readonly wallet = this.walletState.asReadonly();
  readonly verification = this.verificationState.asReadonly();

  setOwner(ownerId: string): void {
    if (ownerId !== this.ownerIdState()) {
      this.resetProgress();
    }
    this.ownerIdState.set(ownerId);
    writeStoredOwner(ownerId);
  }

  setWallet(wallet: OnboardingStateResponse | null): void {
    this.walletState.set(wallet);
  }

  setVerification(verification: VerificationResponse | null): void {
    this.verificationState.set(verification);
  }

  /** Descarta lo cacheado del progreso (tras un reset o un cambio de usuario). */
  resetProgress(): void {
    this.walletState.set(null);
    this.verificationState.set(null);
  }

  clear(): void {
    this.resetProgress();
    this.ownerIdState.set(null);
    writeStoredOwner(null);
  }
}
```

```typescript
// src/app/core/mock-api.service.ts
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Injectable, InjectionToken, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, throwError } from 'rxjs';

import {
  ApiErrorView,
  CreateVerificationRequest,
  DecideVerificationRequest,
  GetVerificationRequest,
  HealthResponse,
  OnboardingStateResponse,
  ResetResponse,
  ScenariosResponse,
  SubmitStepRequest,
  SupportCasesResponse,
  VerificationResponse,
} from './api.models';
import { SessionService } from './session.service';

/** Base del API. Vacío = mismo origen (proxy de desarrollo). */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  providedIn: 'root',
  factory: () => '',
});

const OWNER_HEADER = 'X-Owner-Id';

const DEFAULT_MESSAGES: Record<number, { code: string; message: string }> = {
  0: {
    code: 'NETWORK_ERROR',
    message: 'No se pudo conectar con el servicio. Revisa tu conexión e inténtalo de nuevo.',
  },
  401: { code: 'UNAUTHENTICATED', message: 'No se pudo identificar al usuario. Vuelve a identificarte.' },
  404: { code: 'NOT_FOUND', message: 'El recurso solicitado no existe.' },
  409: { code: 'CONFLICT', message: 'La acción no es posible en el estado actual. Actualiza e inténtalo de nuevo.' },
  413: { code: 'PAYLOAD_TOO_LARGE', message: 'Los datos enviados son demasiado grandes. Envía menos datos.' },
  422: { code: 'VALIDATION_ERROR', message: 'Los datos enviados no son válidos. Revísalos e inténtalo de nuevo.' },
  500: { code: 'INTERNAL_ERROR', message: 'Ocurrió un error interno. Inténtalo de nuevo más tarde.' },
};

/** Convierte cualquier error HTTP en {status, code, message}; prefiere el cuerpo del API. */
export function toApiErrorView(error: unknown): ApiErrorView {
  if (error instanceof HttpErrorResponse) {
    const body: unknown = error.error;
    if (
      typeof body === 'object' &&
      body !== null &&
      typeof (body as { code?: unknown }).code === 'string' &&
      typeof (body as { message?: unknown }).message === 'string'
    ) {
      const { code, message } = body as { code: string; message: string };
      return { status: error.status, code, message };
    }
    const fallback = DEFAULT_MESSAGES[error.status];
    if (fallback) {
      return { status: error.status, ...fallback };
    }
    return {
      status: error.status,
      code: 'HTTP_ERROR',
      message: 'No se pudo completar la solicitud. Inténtalo de nuevo.',
    };
  }
  return {
    status: -1,
    code: 'UNKNOWN_ERROR',
    message: 'Ocurrió un error inesperado. Inténtalo de nuevo.',
  };
}

/** Único punto de acceso al API. No contiene reglas de negocio. */
@Injectable()
export class MockApiService {
  private readonly http = inject(HttpClient);
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);
  private readonly base = inject(API_BASE_URL);

  health(): Observable<HealthResponse> {
    return this.get<HealthResponse>('/health');
  }

  scenarios(): Observable<ScenariosResponse> {
    return this.get<ScenariosResponse>('/scenarios');
  }

  supportCases(): Observable<SupportCasesResponse> {
    return this.get<SupportCasesResponse>('/support/cases');
  }

  createVerification(request: CreateVerificationRequest): Observable<VerificationResponse> {
    return this.post<VerificationResponse>('/kyc/verifications', {
      document_number: request.document_number,
      scenario: request.scenario,
    });
  }

  getVerification(request: GetVerificationRequest): Observable<VerificationResponse> {
    return this.get<VerificationResponse>(
      `/kyc/verifications/${encodeURIComponent(request.verification_id)}`,
    );
  }

  decideVerification(request: DecideVerificationRequest): Observable<VerificationResponse> {
    return this.post<VerificationResponse>(
      `/kyc/verifications/${encodeURIComponent(request.verification_id)}/decision`,
      { decision: request.decision },
    );
  }

  getOnboarding(): Observable<OnboardingStateResponse> {
    return this.get<OnboardingStateResponse>('/onboarding');
  }

  submitStep(request: SubmitStepRequest): Observable<OnboardingStateResponse> {
    const body: { document_number?: string } = {};
    if (request.document_number !== undefined) {
      body.document_number = request.document_number;
    }
    return this.post<OnboardingStateResponse>(
      `/onboarding/steps/${encodeURIComponent(request.step_id)}`,
      body,
    );
  }

  reset(): Observable<ResetResponse> {
    return this.post<ResetResponse>('/control/reset', null);
  }

  private get<T>(path: string): Observable<T> {
    return this.http
      .get<T>(`${this.base}${path}`, this.options())
      .pipe(catchError((error: unknown) => this.fail(error)));
  }

  private post<T>(path: string, body: unknown): Observable<T> {
    return this.http
      .post<T>(`${this.base}${path}`, body, this.options())
      .pipe(catchError((error: unknown) => this.fail(error)));
  }

  private options(): { headers?: HttpHeaders } {
    const owner = this.session.ownerId();
    return owner ? { headers: new HttpHeaders({ [OWNER_HEADER]: owner }) } : {};
  }

  private fail(error: unknown): Observable<never> {
    const view = toApiErrorView(error);
    if (view.code === 'UNAUTHENTICATED') {
      this.session.clear();
      void this.router.navigate(['/identificar']);
    }
    return throwError(() => view);
  }
}
```

```typescript
// src/app/core/owner.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { SessionService } from './session.service';

export const ownerGuard: CanActivateFn = () => {
  const session = inject(SessionService);
  return session.isIdentified() ? true : inject(Router).createUrlTree(['/identificar']);
};
```

```typescript
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
```

```typescript
// src/app/core/labels.ts
import { StepId, StepStatus, VerificationStatus, WalletStatus } from './api.models';

export const WALLET_STATUS_LABELS: Record<WalletStatus, string> = {
  NOT_STARTED: 'No iniciada',
  IN_PROGRESS: 'En progreso',
  KYC_PENDING: 'Verificación pendiente',
  KYC_FAILED: 'Verificación fallida',
  ACTIVE: 'Activa',
};

export const STEP_LABELS: Record<StepId, string> = {
  registro: 'Registro',
  kyc: 'Verificación KYC',
  activacion: 'Activación',
};

export const STEP_STATUS_LABELS: Record<StepStatus, string> = {
  COMPLETED: 'Completado',
  CURRENT: 'Paso actual',
  LOCKED: 'Bloqueado',
};

export const VERIFICATION_STATUS_LABELS: Record<VerificationStatus, string> = {
  APPROVED: 'Aprobada',
  REJECTED: 'Rechazada',
  PENDING: 'Pendiente',
  EXPIRED: 'Expirada',
};
```

```typescript
// src/app/core/a11y.ts
/** Lleva el foco al primer campo inválido del contenedor. */
export function focusFirstInvalid(root: HTMLElement): void {
  root.querySelector<HTMLElement>('input.ng-invalid, select.ng-invalid')?.focus();
}

/** Lleva el foco a un elemento cuando Angular ya actualizó el DOM. */
export function focusLater(root: HTMLElement, selector: string): void {
  setTimeout(() => root.querySelector<HTMLElement>(selector)?.focus(), 0);
}
```

```typescript
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
```

```typescript
// src/app/onboarding/onboarding.component.ts
import { DatePipe } from '@angular/common';
import { Component, ElementRef, OnInit, inject, signal } from '@angular/core';
import { AbstractControl, NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { focusFirstInvalid, focusLater } from '../core/a11y';
import {
  ApiErrorView,
  KycDecision,
  KycScenario,
  OnboardingStateResponse,
  ScenarioItem,
  StepId,
  StepStatus,
  VerificationResponse,
  VerificationStatus,
  WalletStatus,
} from '../core/api.models';
import { documentErrorMessage, testDocumentValidator } from '../core/document.validator';
import {
  STEP_LABELS,
  STEP_STATUS_LABELS,
  VERIFICATION_STATUS_LABELS,
  WALLET_STATUS_LABELS,
} from '../core/labels';
import { MockApiService } from '../core/mock-api.service';
import { SessionService } from '../core/session.service';

const VERIFICATION_MESSAGES: Record<VerificationStatus, string> = {
  APPROVED: 'Verificación aprobada. Completa el paso de verificación para continuar.',
  PENDING: 'Verificación pendiente. Registra una decisión o actualiza el estado.',
  REJECTED: 'Verificación rechazada. Crea una nueva con un documento TEST- válido.',
  EXPIRED: 'Verificación expirada. Crea una nueva verificación.',
};

@Component({
  selector: 'app-onboarding',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe],
  templateUrl: './onboarding.component.html',
})
export class OnboardingComponent implements OnInit {
  private readonly api = inject(MockApiService);
  private readonly session = inject(SessionService);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  readonly loading = signal(true);
  readonly loadError = signal<ApiErrorView | null>(null);
  readonly state = signal<OnboardingStateResponse | null>(null);

  readonly scenarios = signal<ScenarioItem[]>([]);
  readonly scenariosLoading = signal(false);
  readonly scenariosError = signal<ApiErrorView | null>(null);

  /** Acción en curso (null = ninguna). Evita envíos duplicados. */
  readonly busy = signal<string | null>(null);
  readonly actionError = signal<ApiErrorView | null>(null);
  readonly success = signal<string | null>(null);

  readonly verification = this.session.verification;

  readonly registroForm = this.fb.group({
    document_number: this.fb.control('', testDocumentValidator),
  });

  readonly kycForm = this.fb.group({
    document_number: this.fb.control('', testDocumentValidator),
    scenario: this.fb.control<KycScenario | ''>('', Validators.required),
  });

  ngOnInit(): void {
    void this.load();
  }

  // ---------- Etiquetas y ayudas de plantilla ----------
  stepLabel(id: StepId): string {
    return STEP_LABELS[id] ?? id;
  }

  stepStatusLabel(status: StepStatus): string {
    return STEP_STATUS_LABELS[status] ?? status;
  }

  walletLabel(status: WalletStatus): string {
    return WALLET_STATUS_LABELS[status] ?? status;
  }

  verificationLabel(status: VerificationStatus): string {
    return VERIFICATION_STATUS_LABELS[status] ?? status;
  }

  docError(control: AbstractControl): string | null {
    return control.invalid && (control.touched || control.dirty)
      ? documentErrorMessage(control.errors)
      : null;
  }

  scenarioInvalid(): boolean {
    const control = this.kycForm.controls.scenario;
    return control.invalid && (control.touched || control.dirty);
  }

  ariaDisabled(): 'true' | null {
    return this.busy() !== null ? 'true' : null;
  }

  // ---------- Carga ----------
  async load(): Promise<void> {
    this.loading.set(true);
    this.loadError.set(null);
    try {
      this.applyState(await firstValueFrom(this.api.getOnboarding()));
    } catch (error) {
      this.loadError.set(error as ApiErrorView);
      this.loading.set(false);
      return;
    }
    this.loading.set(false);
    await Promise.all([this.loadScenarios(), this.recoverPending()]);
  }

  async loadScenarios(): Promise<void> {
    if (this.scenariosLoading()) {
      return;
    }
    this.scenariosLoading.set(true);
    this.scenariosError.set(null);
    try {
      this.scenarios.set((await firstValueFrom(this.api.scenarios())).scenarios);
    } catch (error) {
      this.scenariosError.set(error as ApiErrorView);
    } finally {
      this.scenariosLoading.set(false);
    }
  }

  /** Tras recargar con KYC pendiente, recupera la verificación pendiente más reciente. */
  private async recoverPending(): Promise<void> {
    if (this.state()?.wallet_status !== 'KYC_PENDING' || this.verification()) {
      return;
    }
    try {
      const cases = await firstValueFrom(this.api.supportCases());
      const pending = [...cases.cases].reverse().find((item) => item.status === 'PENDING');
      if (pending) {
        const detail = await firstValueFrom(
          this.api.getVerification({ verification_id: pending.verification_id }),
        );
        this.session.setVerification(detail);
      }
    } catch (error) {
      this.actionError.set(error as ApiErrorView);
    }
  }

  // ---------- Acciones ----------
  async submitRegistro(): Promise<void> {
    if (this.busy() !== null) {
      return;
    }
    if (this.registroForm.invalid) {
      this.registroForm.markAllAsTouched();
      focusFirstInvalid(this.host.nativeElement);
      return;
    }
    const documentNumber = this.registroForm.controls.document_number.value;
    await this.run(
      'registro',
      () => firstValueFrom(this.api.submitStep({ step_id: 'registro', document_number: documentNumber })),
      (state) => {
        this.applyState(state);
        this.success.set('Registro completado. Continúa con la verificación KYC.');
        this.focusStepHeading();
      },
    );
  }

  async createVerification(): Promise<void> {
    if (this.busy() !== null) {
      return;
    }
    if (this.kycForm.invalid) {
      this.kycForm.markAllAsTouched();
      focusFirstInvalid(this.host.nativeElement);
      return;
    }
    const value = this.kycForm.getRawValue();
    await this.run(
      'crear-kyc',
      async () => {
        const created = await firstValueFrom(
          this.api.createVerification({
            document_number: value.document_number,
            scenario: value.scenario as KycScenario,
          }),
        );
        const state = await firstValueFrom(this.api.getOnboarding()).catch(() => null);
        return { created, state };
      },
      ({ created, state }) => {
        this.session.setVerification(created);
        if (state) {
          this.applyState(state);
        }
        this.success.set(VERIFICATION_MESSAGES[created.status]);
      },
    );
  }

  async decide(decision: KycDecision): Promise<void> {
    const current = this.verification();
    if (this.busy() !== null || !current) {
      return;
    }
    await this.run(
      'decidir-kyc',
      async () => {
        const decided = await firstValueFrom(
          this.api.decideVerification({ verification_id: current.verification_id, decision }),
        );
        const state = await firstValueFrom(this.api.getOnboarding()).catch(() => null);
        return { decided, state };
      },
      ({ decided, state }) => {
        this.session.setVerification(decided);
        if (state) {
          this.applyState(state);
        }
        this.success.set(
          decision === 'APPROVED'
            ? 'Decisión registrada: verificación aprobada.'
            : 'Decisión registrada: verificación rechazada.',
        );
      },
    );
  }

  async refreshVerification(): Promise<void> {
    const current = this.verification();
    if (this.busy() !== null || !current) {
      return;
    }
    await this.run(
      'actualizar-kyc',
      async () => {
        const updated = await firstValueFrom(
          this.api.getVerification({ verification_id: current.verification_id }),
        );
        const state = await firstValueFrom(this.api.getOnboarding()).catch(() => null);
        return { updated, state };
      },
      ({ updated, state }) => {
        this.session.setVerification(updated);
        if (state) {
          this.applyState(state);
        }
        this.success.set('Estado actualizado.');
      },
    );
  }

  async completeStep(step: 'kyc' | 'activacion'): Promise<void> {
    if (this.busy() !== null) {
      return;
    }
    await this.run(
      `paso-${step}`,
      () => firstValueFrom(this.api.submitStep({ step_id: step })),
      (state) => {
        this.applyState(state);
        this.success.set(
          step === 'kyc'
            ? 'Verificación completada. Ya puedes activar tu wallet.'
            : '¡Wallet activa! Ya puedes acceder a pagos de bajo monto.',
        );
        this.focusStepHeading();
      },
    );
  }

  // ---------- Internos ----------
  private applyState(state: OnboardingStateResponse): void {
    this.state.set(state);
    this.session.setWallet(state);
  }

  private focusStepHeading(): void {
    focusLater(this.host.nativeElement, '[data-step-heading]');
  }

  private async run<T>(key: string, action: () => Promise<T>, onSuccess: (result: T) => void): Promise<void> {
    if (this.busy() !== null) {
      return;
    }
    this.busy.set(key);
    this.actionError.set(null);
    this.success.set(null);
    try {
      onSuccess(await action());
    } catch (error) {
      this.actionError.set(error as ApiErrorView);
    } finally {
      this.busy.set(null);
    }
  }
}
```

```html
<!-- src/app/onboarding/onboarding.component.html -->
<h1>Activa tu wallet</h1>

@if (loading()) {
  <p role="status">Cargando tu progreso…</p>
} @else if (loadError()) {
  <div role="alert" class="alert alert-error">
    <p><strong>Error:</strong> {{ loadError()!.message }}</p>
    <p class="hint">Código: {{ loadError()!.code }}</p>
    <button type="button" class="btn" (click)="load()">Reintentar</button>
  </div>
} @else {
  @if (state(); as s) {
    <section aria-labelledby="wallet-h" class="panel">
      <h2 id="wallet-h">Estado de la wallet</h2>
      <p>
        <strong>{{ walletLabel(s.wallet_status) }}</strong>
      </p>
    </section>

    <section aria-labelledby="pasos-h">
      <h2 id="pasos-h">Pasos del onboarding</h2>
      <ol class="steps">
        @for (step of s.steps; track step.id) {
          <li [attr.aria-current]="step.status === 'CURRENT' ? 'step' : null">
            <span>{{ step.order }}.</span>
            <span>{{ stepLabel(step.id) }}</span>
            <span class="badge">{{ stepStatusLabel(step.status) }}</span>
          </li>
        }
      </ol>
    </section>

    <div role="status">
      @if (success()) {
        <p class="alert alert-ok"><strong>Listo:</strong> {{ success() }}</p>
      }
    </div>
    <div role="alert">
      @if (actionError()) {
        <div class="alert alert-error">
          <p><strong>Error:</strong> {{ actionError()!.message }}</p>
          <p class="hint">Código: {{ actionError()!.code }}</p>
        </div>
      }
    </div>

    @switch (s.current_step) {
      @case ('registro') {
        <section aria-labelledby="registro-h" class="panel">
          <h2 id="registro-h" tabindex="-1" data-step-heading>Paso 1: Registro</h2>
          <form [formGroup]="registroForm" (ngSubmit)="submitRegistro()" novalidate>
            <div class="field">
              <label for="reg-doc">Número de documento</label>
              <p id="reg-doc-hint" class="hint">
                Entorno de pruebas: debe comenzar con TEST- y seguir con letras, números o guiones.
                Ejemplo: TEST-0001.
              </p>
              <input
                id="reg-doc"
                type="text"
                formControlName="document_number"
                autocomplete="off"
                maxlength="64"
                [attr.aria-invalid]="docError(registroForm.controls.document_number) ? 'true' : null"
                [attr.aria-describedby]="docError(registroForm.controls.document_number) ? 'reg-doc-hint reg-doc-err' : 'reg-doc-hint'"
              />
              @if (docError(registroForm.controls.document_number); as msg) {
                <p id="reg-doc-err" class="field-error">{{ msg }}</p>
              }
            </div>
            <div class="actions">
              <button
                type="submit"
                class="btn"
                [attr.aria-disabled]="ariaDisabled()"
                [attr.aria-busy]="busy() === 'registro'"
              >
                @if (busy() === 'registro') { Guardando… } @else { Continuar }
              </button>
            </div>
          </form>
        </section>
      }

      @case ('kyc') {
        <section aria-labelledby="kyc-h" class="panel">
          <h2 id="kyc-h" tabindex="-1" data-step-heading>Paso 2: Verificación KYC</h2>
          <p class="hint">Crea una verificación de prueba y elige el escenario que quieres simular.</p>

          @if (scenariosLoading()) {
            <p role="status">Cargando escenarios…</p>
          }
          @if (scenariosError()) {
            <div role="alert" class="alert alert-error">
              <p><strong>Error:</strong> {{ scenariosError()!.message }}</p>
              <p class="hint">Código: {{ scenariosError()!.code }}</p>
              <button type="button" class="btn btn-secondary" (click)="loadScenarios()">Reintentar</button>
            </div>
          } @else if (!scenariosLoading() && scenarios().length === 0) {
            <p class="alert alert-info">No hay escenarios disponibles.</p>
          }

          <form [formGroup]="kycForm" (ngSubmit)="createVerification()" novalidate>
            <div class="field">
              <label for="kyc-doc">Número de documento</label>
              <p id="kyc-doc-hint" class="hint">Debe comenzar con TEST-. Ejemplo: TEST-0001.</p>
              <input
                id="kyc-doc"
                type="text"
                formControlName="document_number"
                autocomplete="off"
                maxlength="64"
                [attr.aria-invalid]="docError(kycForm.controls.document_number) ? 'true' : null"
                [attr.aria-describedby]="docError(kycForm.controls.document_number) ? 'kyc-doc-hint kyc-doc-err' : 'kyc-doc-hint'"
              />
              @if (docError(kycForm.controls.document_number); as msg) {
                <p id="kyc-doc-err" class="field-error">{{ msg }}</p>
              }
            </div>

            <div class="field">
              <label for="kyc-scenario">Escenario</label>
              <p id="kyc-scenario-hint" class="hint">Resultado que simulará la verificación.</p>
              <select
                id="kyc-scenario"
                formControlName="scenario"
                [attr.aria-invalid]="scenarioInvalid() ? 'true' : null"
                [attr.aria-describedby]="scenarioInvalid() ? 'kyc-scenario-hint kyc-scenario-err' : 'kyc-scenario-hint'"
              >
                <option value="">Selecciona un escenario</option>
                @for (scenario of scenarios(); track scenario.name) {
                  <option [value]="scenario.name">{{ scenario.name }} — {{ scenario.description }}</option>
                }
              </select>
              @if (scenarioInvalid()) {
                <p id="kyc-scenario-err" class="field-error">Selecciona un escenario.</p>
              }
            </div>

            <div class="actions">
              <button
                type="submit"
                class="btn"
                [attr.aria-disabled]="ariaDisabled()"
                [attr.aria-busy]="busy() === 'crear-kyc'"
              >
                @if (busy() === 'crear-kyc') { Creando verificación… } @else { Crear verificación }
              </button>
            </div>
          </form>

          @if (verification(); as v) {
            <section aria-labelledby="ver-h" class="panel">
              <h3 id="ver-h">Última verificación</h3>
              <dl class="data">
                <dt>Identificador</dt>
                <dd>{{ v.verification_id }}</dd>
                <dt>Documento</dt>
                <dd>{{ v.document_number }}</dd>
                <dt>Escenario</dt>
                <dd>{{ v.scenario }}</dd>
                <dt>Estado</dt>
                <dd><strong>{{ verificationLabel(v.status) }}</strong></dd>
                <dt>Creada</dt>
                <dd>{{ v.created_at | date: 'dd/MM/yyyy HH:mm:ss' }}</dd>
                @if (v.decided_at) {
                  <dt>Resuelta</dt>
                  <dd>{{ v.decided_at | date: 'dd/MM/yyyy HH:mm:ss' }}</dd>
                }
              </dl>

              @if (v.status === 'PENDING') {
                <p class="hint">La verificación está pendiente: registra una decisión o actualiza su estado.</p>
                <div class="actions">
                  <button
                    type="button"
                    class="btn"
                    [attr.aria-disabled]="ariaDisabled()"
                    [attr.aria-busy]="busy() === 'decidir-kyc'"
                    (click)="decide('APPROVED')"
                  >
                    Aprobar
                  </button>
                  <button
                    type="button"
                    class="btn btn-danger"
                    [attr.aria-disabled]="ariaDisabled()"
                    [attr.aria-busy]="busy() === 'decidir-kyc'"
                    (click)="decide('REJECTED')"
                  >
                    Rechazar
                  </button>
                  <button
                    type="button"
                    class="btn btn-secondary"
                    [attr.aria-disabled]="ariaDisabled()"
                    [attr.aria-busy]="busy() === 'actualizar-kyc'"
                    (click)="refreshVerification()"
                  >
                    Actualizar estado
                  </button>
                </div>
              } @else if (v.status === 'APPROVED') {
                <p class="hint">Verificación aprobada: ya puedes completar este paso.</p>
              } @else {
                <p class="hint">Esta verificación no está aprobada. Crea una nueva para continuar.</p>
              }
            </section>
          }

          <div class="actions">
            <button
              type="button"
              class="btn"
              [attr.aria-disabled]="ariaDisabled()"
              [attr.aria-busy]="busy() === 'paso-kyc'"
              (click)="completeStep('kyc')"
            >
              @if (busy() === 'paso-kyc') { Completando… } @else { Completar paso de verificación }
            </button>
          </div>
        </section>
      }

      @case ('activacion') {
        <section aria-labelledby="act-h" class="panel">
          <h2 id="act-h" tabindex="-1" data-step-heading>Paso 3: Activación</h2>
          <p>Tu verificación está completa. Activa la wallet para terminar el onboarding.</p>
          <div class="actions">
            <button
              type="button"
              class="btn"
              [attr.aria-disabled]="ariaDisabled()"
              [attr.aria-busy]="busy() === 'paso-activacion'"
              (click)="completeStep('activacion')"
            >
              @if (busy() === 'paso-activacion') { Activando… } @else { Activar wallet }
            </button>
          </div>
        </section>
      }

      @default {
        <section aria-labelledby="fin-h" class="panel">
          <h2 id="fin-h" tabindex="-1" data-step-heading>Wallet activa</h2>
          <p>Completaste todos los pasos del onboarding.</p>
          @if (s.duration_seconds !== null) {
            <p>Duración del onboarding: <strong>{{ s.duration_seconds }} s</strong>.</p>
          }
        </section>
      }
    }

    <section aria-labelledby="pagos-h" class="panel">
      <h2 id="pagos-h">Pagos de bajo monto</h2>
      @if (s.low_amount_payments_enabled) {
        <p>Tu wallet está activa y puedes acceder a pagos de bajo monto.</p>
        <a routerLink="/pagos" class="btn">Ir a pagos de bajo monto</a>
      } @else {
        <p id="pagos-ayuda">
          No disponible todavía. Se habilita cuando la wallet esté activa (estado actual:
          {{ walletLabel(s.wallet_status) }}).
        </p>
        <button type="button" class="btn" aria-disabled="true" aria-describedby="pagos-ayuda">
          Ir a pagos de bajo monto
        </button>
      }
    </section>
  }
}
```

```typescript
// src/app/consola/consola.component.ts
import { Component, ElementRef, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { focusLater } from '../core/a11y';
import { ApiErrorView, HealthResponse, ScenarioItem, SupportCase } from '../core/api.models';
import { MockApiService } from '../core/mock-api.service';
import { SessionService } from '../core/session.service';

export type ServiceKey = 'health' | 'scenarios' | 'cases';
type ErrorKey = ServiceKey | 'reset';

interface ServiceDef {
  key: ServiceKey;
  method: 'GET';
  path: string;
  description: string;
}

@Component({
  selector: 'app-consola',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './consola.component.html',
})
export class ConsolaComponent {
  private readonly api = inject(MockApiService);
  private readonly session = inject(SessionService);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  readonly services: readonly ServiceDef[] = [
    { key: 'health', method: 'GET', path: '/health', description: 'Comprueba que el servicio responde.' },
    { key: 'scenarios', method: 'GET', path: '/scenarios', description: 'Lista los escenarios KYC disponibles.' },
    {
      key: 'cases',
      method: 'GET',
      path: '/support/cases',
      description: 'Lista tus verificaciones que requieren atención (no aprobadas).',
    },
  ];

  /** Servicio o acción en curso (null = ninguno). Evita ejecuciones duplicadas. */
  readonly running = signal<ErrorKey | null>(null);
  readonly errors = signal<Partial<Record<ErrorKey, ApiErrorView>>>({});

  readonly health = signal<HealthResponse | null>(null);
  readonly scenarios = signal<ScenarioItem[] | null>(null);
  readonly cases = signal<SupportCase[] | null>(null);

  readonly confirmingReset = signal(false);
  readonly resetDone = signal(false);

  ariaDisabled(): 'true' | null {
    return this.running() !== null ? 'true' : null;
  }

  async run(key: ServiceKey): Promise<void> {
    if (this.running() !== null) {
      return;
    }
    this.running.set(key);
    this.setError(key, null);
    try {
      switch (key) {
        case 'health':
          this.health.set(await firstValueFrom(this.api.health()));
          break;
        case 'scenarios':
          this.scenarios.set((await firstValueFrom(this.api.scenarios())).scenarios);
          break;
        case 'cases':
          this.cases.set((await firstValueFrom(this.api.supportCases())).cases);
          break;
      }
    } catch (error) {
      this.clearResult(key);
      this.setError(key, error as ApiErrorView);
    } finally {
      this.running.set(null);
    }
  }

  askReset(): void {
    if (this.running() !== null) {
      return;
    }
    this.resetDone.set(false);
    this.setError('reset', null);
    this.confirmingReset.set(true);
    focusLater(this.host.nativeElement, '#reset-confirm-text');
  }

  cancelReset(): void {
    this.confirmingReset.set(false);
    focusLater(this.host.nativeElement, '#reset-open');
  }

  async confirmReset(): Promise<void> {
    if (this.running() !== null) {
      return;
    }
    this.running.set('reset');
    this.setError('reset', null);
    try {
      await firstValueFrom(this.api.reset());
      this.session.resetProgress();
      this.health.set(null);
      this.scenarios.set(null);
      this.cases.set(null);
      this.resetDone.set(true);
    } catch (error) {
      this.setError('reset', error as ApiErrorView);
    } finally {
      this.running.set(null);
      this.confirmingReset.set(false);
      focusLater(this.host.nativeElement, '#reset-open');
    }
  }

  private clearResult(key: ServiceKey): void {
    if (key === 'health') {
      this.health.set(null);
    } else if (key === 'scenarios') {
      this.scenarios.set(null);
    } else {
      this.cases.set(null);
    }
  }

  private setError(key: ErrorKey, error: ApiErrorView | null): void {
    this.errors.update((current) => {
      const next = { ...current };
      if (error) {
        next[key] = error;
      } else {
        delete next[key];
      }
      return next;
    });
  }
}
```

```html
<!-- src/app/consola/consola.component.html -->
<h1>Consola de servicios</h1>
<p>Ejecuta cada servicio del mock por separado y revisa su resultado.</p>

@for (svc of services; track svc.key) {
  <section class="panel" [attr.aria-labelledby]="'svc-' + svc.key">
    <h2 [id]="'svc-' + svc.key">{{ svc.method }} {{ svc.path }}</h2>
    <p class="hint">{{ svc.description }}</p>

    <div class="actions">
      <button
        type="button"
        class="btn"
        [attr.aria-label]="'Ejecutar ' + svc.method + ' ' + svc.path"
        [attr.aria-disabled]="ariaDisabled()"
        [attr.aria-busy]="running() === svc.key"
        (click)="run(svc.key)"
      >
        @if (running() === svc.key) { Ejecutando… } @else { Ejecutar }
      </button>
    </div>

    <div role="status">
      @if (running() === svc.key) {
        <p>Ejecutando {{ svc.method }} {{ svc.path }}…</p>
      }
    </div>

    <div role="alert">
      @if (errors()[svc.key]; as err) {
        <div class="alert alert-error">
          <p><strong>Error:</strong> {{ err.message }}</p>
          <p class="hint">Código: {{ err.code }}</p>
        </div>
      }
    </div>

    @switch (svc.key) {
      @case ('health') {
        @if (health(); as h) {
          <p class="alert alert-ok"><strong>Resultado:</strong> el servicio responde (estado: {{ h.status }}).</p>
        }
      }
      @case ('scenarios') {
        @if (scenarios(); as list) {
          @if (list.length === 0) {
            <p class="alert alert-info">El API no devolvió escenarios.</p>
          } @else {
            <ul>
              @for (item of list; track item.name) {
                <li><strong>{{ item.name }}</strong>: {{ item.description }}</li>
              }
            </ul>
          }
        }
      }
      @case ('cases') {
        @if (cases(); as list) {
          @if (list.length === 0) {
            <p class="alert alert-info">No hay casos de soporte para tu usuario.</p>
          } @else {
            <ul>
              @for (item of list; track item.verification_id) {
                <li>
                  <strong>{{ item.status }}</strong> — {{ item.message }}
                  <span class="hint">(verificación {{ item.verification_id }})</span>
                </li>
              }
            </ul>
          }
        }
      }
    }
  </section>
}

<section class="panel" aria-labelledby="reset-h">
  <h2 id="reset-h">POST /control/reset</h2>
  <p class="hint">
    Borra todo el progreso de tu usuario (pasos, verificaciones y eventos). Esta acción no se puede deshacer.
  </p>

  <div role="status">
    @if (running() === 'reset') {
      <p>Reiniciando tu estado…</p>
    }
    @if (resetDone()) {
      <p class="alert alert-ok">
        <strong>Listo:</strong> Estado reiniciado. Puedes empezar el onboarding de nuevo.
        <a routerLink="/onboarding">Ir al onboarding</a>
      </p>
    }
  </div>

  <div role="alert">
    @if (errors()['reset']; as err) {
      <div class="alert alert-error">
        <p><strong>Error:</strong> {{ err.message }}</p>
        <p class="hint">Código: {{ err.code }}</p>
      </div>
    }
  </div>

  @if (!confirmingReset()) {
    <button
      id="reset-open"
      type="button"
      class="btn btn-danger"
      [attr.aria-disabled]="ariaDisabled()"
      (click)="askReset()"
    >
      Reiniciar mi estado…
    </button>
  } @else {
    <div role="group" aria-labelledby="reset-confirm-text" class="alert alert-info" (keydown.escape)="cancelReset()">
      <p id="reset-confirm-text" tabindex="-1">
        ¿Seguro que quieres reiniciar tu estado? Se perderá todo tu progreso de onboarding.
      </p>
      <div class="actions">
        <button
          type="button"
          class="btn btn-danger"
          [attr.aria-disabled]="ariaDisabled()"
          [attr.aria-busy]="running() === 'reset'"
          (click)="confirmReset()"
        >
          @if (running() === 'reset') { Reiniciando… } @else { Sí, reiniciar }
        </button>
        <button type="button" class="btn btn-secondary" (click)="cancelReset()">Cancelar</button>
      </div>
      <p class="hint">Pulsa Esc para cancelar.</p>
    </div>
  }
</section>
```

```typescript
// src/app/pagos/pagos.component.ts
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { ApiErrorView, OnboardingStateResponse } from '../core/api.models';
import { WALLET_STATUS_LABELS } from '../core/labels';
import { MockApiService } from '../core/mock-api.service';

@Component({
  selector: 'app-pagos',
  standalone: true,
  imports: [RouterLink],
  template: `
    <h1>Pagos de bajo monto</h1>

    @if (loading()) {
      <p role="status">Verificando el estado de tu wallet…</p>
    } @else if (error()) {
      <div role="alert" class="alert alert-error">
        <p><strong>Error:</strong> {{ error()!.message }}</p>
        <p class="hint">Código: {{ error()!.code }}</p>
        <button type="button" class="btn" (click)="load()">Reintentar</button>
      </div>
    } @else if (state()?.low_amount_payments_enabled) {
      <div role="status" class="alert alert-ok">
        <p><strong>Acceso habilitado.</strong> Tu wallet está activa y puedes realizar pagos de bajo monto.</p>
      </div>
      <p class="hint">
        El contrato de API aprobado no define endpoints de pagos, por lo que esta pantalla solo confirma el acceso.
      </p>
    } @else {
      <div role="alert" class="alert alert-error">
        <p>
          <strong>Acceso bloqueado.</strong> Estado actual de la wallet: {{ walletLabel() }}. Completa el
          onboarding para habilitar los pagos de bajo monto.
        </p>
      </div>
      <a routerLink="/onboarding" class="btn">Volver al onboarding</a>
    }
  `,
})
export class PagosComponent implements OnInit {
  private readonly api = inject(MockApiService);

  readonly loading = signal(true);
  readonly error = signal<ApiErrorView | null>(null);
  readonly state = signal<OnboardingStateResponse | null>(null);

  ngOnInit(): void {
    void this.load();
  }

  walletLabel(): string {
    const status = this.state()?.wallet_status;
    return status ? WALLET_STATUS_LABELS[status] : '';
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      this.state.set(await firstValueFrom(this.api.getOnboarding()));
    } catch (error) {
      this.error.set(error as ApiErrorView);
    } finally {
      this.loading.set(false);
    }
  }
}
```

Nada de lo anterior se ha ejecutado ni compilado. Los pasos para comprobarlo están en la sección 10 de `frontend_spec.md`.