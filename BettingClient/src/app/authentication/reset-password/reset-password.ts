import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../service/auth-service';
import { take } from 'rxjs';
import { Router, ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-reset-password',
  imports: [NgbAlertModule, FormsModule],
  templateUrl: './reset-password.html'
})
export class ResetPassword {
  email: string = "";
  key: string = "";
  password1: string = "";
  password2: string = "";

  alerts: Alert[] = []

  constructor(private http: HttpClient, private authService: AuthService, private router: Router, private route: ActivatedRoute) {

  }

  ngOnInit(): void {
    let qEmail = this.route.snapshot.queryParamMap.get('email');
    if (qEmail != null) {
      this.email = qEmail;
    }

    let qKey = this.route.snapshot.queryParamMap.get('key');   
    if (qKey != null) {
      this.key = qKey;
    }    
  }

  resetPassword() {
    let resetPath = environment.serverAddress + environment.locations.auth.resetPassword;
    this.http.post<Alert>(resetPath, {email:this.email, key: this.key, password1: this.password1, password2: this.password2, })
    .subscribe(response => {
      this.alerts.push(response);

      if (response.type === 'success') {
        this.authService.signIn();
        this.authService.getUser$.pipe(take(1)).subscribe(user => {
          setTimeout(() => {
            this.router.navigate(['/']);
          }, 1000);
        });    
      }
    });

  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
