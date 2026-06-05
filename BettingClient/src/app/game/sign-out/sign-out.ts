import { Component } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from '../../service/auth-service';
import { paths } from '../../paths';

@Component({
  selector: 'app-sign-out',
  imports: [],
  templateUrl: './sign-out.html'
})
export class SignOut {
  constructor(private http: HttpClient, private authService: AuthService, private router: Router) {
    let path = paths.auth.signOut;
    this.http.get(path, {responseType: 'text'})
      .subscribe({
        next: (message: string) => {
          this.authService.fetchAuthStatus().subscribe({
            next: () => {
              setTimeout(() => {
                this.router.navigate(['/auth/sign-in']);
              }, 1000);    
            },
            error: (err: HttpErrorResponse) => {

            }
          });
        },
        error: (err: HttpErrorResponse) => {

        }
      });
  }
}
