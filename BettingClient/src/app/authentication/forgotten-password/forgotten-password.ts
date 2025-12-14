import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-forgotten-password',
  imports: [NgbAlertModule, FormsModule],
  templateUrl: './forgotten-password.html'
})
export class ForgottenPassword {
  alerts: Alert[] = []
  
  email: string = '';

  constructor(private http: HttpClient) {

  }

  requestNewPassword(): void {
    let location = environment.locations.auth.forgottenPassword;
    this.http.post<Alert>(location, {email: this.email}).subscribe(response => {
      this.alerts.push(response);
    });
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
