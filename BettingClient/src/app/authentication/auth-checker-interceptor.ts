import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { tap, catchError } from 'rxjs/operators';
import { Observable, throwError, EMPTY } from 'rxjs';
import { Router } from '@angular/router';
import { inject } from '@angular/core';
import { environment } from '../../environments/environment';
import { AuthService } from '../service/auth-service';

export const authCheckerInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const authService = inject(AuthService);
  //console.log('Outgoing HTTP request', req);

  if (req.url.startsWith(environment.serverAddress)) {
      const cloned = req.clone({ withCredentials: true });
      return next(cloned).pipe(
      catchError((error: HttpErrorResponse) => {
          if (error.status === 401) {
            // Redirect to login page
            console.log("Error user is not signed in...");
            authService.signOut();
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

  return next(req);
};
