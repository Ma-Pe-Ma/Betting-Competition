import { CanActivateFn } from '@angular/router';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './auth-service';
import { Observable, of } from 'rxjs';
import { filter, take, map } from 'rxjs/operators';

export const authGuard: CanActivateFn = (route, state) : Observable<boolean> => {
  const authService = inject(AuthService);
  const router = inject(Router); 
  
  const requiredRole = route.data['role'];

  return authService.getUser$.pipe(
    filter(userRole => userRole !== null),
    take(1),
    map(userRole => {
      //console.log("User role: " + JSON.stringify(userRole) + ", required role: " + requiredRole + " state.url: " + state.url);

       if (requiredRole == null) {
        if (userRole.role == null) {
          //console.log("Can activate as user is not logged in");
          return true;
        }

        //console.log("User is logged in, redirecting to home");
        router.navigate(['/']);
        return false;
      }

      if (userRole.role != null) {
        if(userRole.role >= requiredRole) {
          //console.log("Can activate as user has the required role");
          return true;
        }
        
        //console.log("User does not have the required role, redirecting to home");
        router.navigate(['/']);
        return false;
      }    

      //console.log("This should not happen, but user is not logged in, redirecting to sign-in");
     
      router.navigate(['/auth/sign-in']);
      return false;
    })
  );
};
