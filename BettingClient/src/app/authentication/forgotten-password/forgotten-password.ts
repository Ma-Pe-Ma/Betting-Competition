import { Component } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { FormsModule } from '@angular/forms';
import { paths } from '../../paths';

@Component({
  selector: 'app-forgotten-password',
  imports: [NgbAlertModule, FormsModule],
  templateUrl: './forgotten-password.html'
})
export class ForgottenPassword {
  alerts: Alert[] = []
  
  email: string = '';

  constructor(private http: HttpClient) {}

  requestNewPassword(): void {
    let location = paths.auth.forgottenPassword;
    this.http.post(location, {email: this.email}, {responseType: 'text'})
      .subscribe({
        next: (response: string) => {
          this.alerts.push({'type': 'success', 'message': response});
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({'type': 'danger', 'message': err.error});
        }
      });
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
