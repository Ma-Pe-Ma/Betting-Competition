import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { paths } from '../../../paths';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-send-message',
  imports: [FormsModule, NgbAlertModule],
  templateUrl: './send-message.html'
})
export class SendMessage {
  subject: string = ""
  message: string = ""

  alerts: Alert[] = []

  constructor(private http: HttpClient) {}

  sendMessage() {
    let notificationPath = paths.admin.sendNotification;    

    this.http.post(notificationPath, {subject: this.subject, message: this.message}, {responseType: 'text'})
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
