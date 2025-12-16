import { Component } from '@angular/core';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { take } from 'rxjs';
import { AuthService } from '../../service/auth-service';
import { GameConfigurationService } from '../../service/game-configuration-service';
import { paths } from '../../paths';

@Component({
  selector: 'app-sign-in',
  imports: [RouterModule, FormsModule, NgbAlertModule],
  templateUrl: './sign-in.html'
})
export class SignIn {
  userData: UserData = {keepSignedIn: true}
  
  alerts: Alert[] = []

  constructor(private router: Router, private http: HttpClient, private authService: AuthService, private gameConfigurationService: GameConfigurationService) {}

  signIn() {
    let location = paths.auth.signIn;
    this.http.post<Alert>(location, this.userData, {observe: 'response'}).pipe(take(1)).subscribe((response: HttpResponse<Alert>) => {      
      if (response.status === 200) {
        let newAlert: Alert = response.body!;

        this.alerts.push(newAlert);

        if (newAlert.type === 'success') {
          this.authService.signIn().subscribe(response => {
            setTimeout(() => {
              this.router.navigate(['/']);
            }, 1000);
          });    
        }
      }
    });
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
