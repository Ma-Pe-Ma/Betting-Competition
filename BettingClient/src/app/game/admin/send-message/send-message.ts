import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { HttpDataHandler } from '../../../service/http-data-handler';
import { paths } from '../../../paths';

@Component({
  selector: 'app-send-message',
  imports: [FormsModule, NgbAlertModule],
  templateUrl: './send-message.html'
})
export class SendMessage {
  subject: string = ""
  message: string = ""

  alerts: Alert[] = []

  constructor(private httpDataHandler: HttpDataHandler) {

  }

  sendMessage() {
    let notificationPath = paths.admin.sendNotification;    

    this.httpDataHandler.postData(notificationPath, {subject: this.subject, message: this.message}).subscribe(value => {
        this.alerts.push(value); 
    });
  }

  close(alert: Alert) {
    this.alerts.splice(this.alerts.indexOf(alert), 1);
  }
}
