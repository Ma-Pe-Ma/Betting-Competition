import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';
import { AuthService } from '../../service/auth-service';
import { take } from 'rxjs';

@Component({
  selector: 'app-sign-out',
  imports: [],
  templateUrl: './sign-out.html'
})
export class SignOut {
  constructor(private http: HttpClient, private authService: AuthService, private router: Router) {
    let path = environment.serverAddress + environment.locations.auth.signOut;
    this.http.get<Alert>(path, {observe: 'response'}).pipe(take(1)).subscribe(res => {
      if (res.status === 200) {
        let newAlert: Alert = res.body!;
        if (newAlert.type === 'success') {
          this.authService.signOut();        
          this.authService.getUser$.pipe(take(1)).subscribe(user => {
            setTimeout(() => {
              this.router.navigate(['/auth/sign-in']);
            }, 1000);    
          });    
        } 
      }
    });
  }
}
