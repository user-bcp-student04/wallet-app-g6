// src/app/core/owner.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { SessionService } from './session.service';

export const ownerGuard: CanActivateFn = () => {
  const session = inject(SessionService);
  return session.isIdentified() ? true : inject(Router).createUrlTree(['/identificar']);
};
