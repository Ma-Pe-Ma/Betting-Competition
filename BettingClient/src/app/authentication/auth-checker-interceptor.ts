import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { catchError } from 'rxjs/operators';
import { throwError, EMPTY } from 'rxjs';
import { Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../service/auth-service';
import { ClientConfigService } from '../service/client-config-service';

export const authCheckerInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const clientConfigService = inject(ClientConfigService);
  const authService = inject(AuthService);

  const baseURL = clientConfigService?.clientConfig?.endpoint;
  const withCred = req.clone({ withCredentials: true});

  if (baseURL && !withCred.url.startsWith('http')) {
    const absoluteURL = baseURL + withCred.url;  
    const cloned = withCred.clone({ url: absoluteURL });

    return next(cloned).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401) {
          // Redirect to login page
          console.log("Error user is not signed in...");
          authService.signOut().subscribe();
          router.navigate(['/auth/sign-in']);
          return EMPTY;
        }

        if (error.status === 409) {
          console.log("Error user is signed in...");
          //router.navigate(['/']);
          return EMPTY;
        }

        return throwError(() => error);
      })
    );
  }

  return next(withCred);
};
