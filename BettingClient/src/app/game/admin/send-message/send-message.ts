import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { finalize } from 'rxjs';
import { paths } from '../../../paths';

@Component({
  selector: 'app-send-message',
  imports: [FormsModule, NgbAlertModule],
  templateUrl: './send-message.html'
})
export class SendMessage {
  subject: string = ""
  message: string = ""
  disabled = false;

  alerts: Alert[] = []

  constructor(private http: HttpClient) {}

  sendMessage() {
    this.disabled = true;
    let notificationPath = paths.admin.sendNotification;    

    this.http.post(notificationPath, {subject: this.subject, message: this.message}, {responseType: 'text'})
      .pipe(finalize( () => {this.disabled = false;}))
      .subscribe({
        next: (message: string) => {
          this.alerts.push({type: 'success', message: message }); 
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({type: 'danger', message: err.error }); 
        }
    });
  }

  close(alert: Alert) {
    this.alerts.splice(this.alerts.indexOf(alert), 1);
  }
}
