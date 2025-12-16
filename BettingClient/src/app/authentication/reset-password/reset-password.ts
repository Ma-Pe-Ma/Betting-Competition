import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../service/auth-service';
import { Router, ActivatedRoute } from '@angular/router';
import { GameConfigurationService } from '../../service/game-configuration-service';
import { paths } from '../../paths';

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

  constructor(private http: HttpClient, private authService: AuthService, private router: Router, private route: ActivatedRoute, private gameConfigurationService: GameConfigurationService) {}

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
    let resetPath = paths.auth.resetPassword;
    this.http.post<Alert>(resetPath, {email:this.email, key: this.key, password1: this.password1, password2: this.password2, })
    .subscribe(response => {
      this.alerts.push(response);

      if (response.type === 'success') {
        this.authService.signIn().subscribe(user => {
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
