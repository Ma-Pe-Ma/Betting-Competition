import { Component } from '@angular/core';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { FormsModule } from '@angular/forms';
import { paths } from '../../../paths';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';

interface HomeMessageContainer {
  id?: number,
  message?: string
}

@Component({
  selector: 'app-home-message',
  imports: [NgbAlertModule, FormsModule],
  templateUrl: './home-message.html'
})
export class HomeMessage {
  homeMessages: HomeMessageContainer[] = []
  alerts: Alert[] = []

  constructor(private http: HttpClient) {
    let getHomeMessagePath = paths.admin.homeMessage.get;
    
    this.http.get<HomeMessageContainer[]>(getHomeMessagePath)
      .subscribe({
        next: (messageContainer: HomeMessageContainer[]) => {
          this.homeMessages = messageContainer;
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({type: 'danger', message: err.error});
        }
      });
  }

  postMessages() {
    let setHomeMessagePath = paths.admin.homeMessage.set;  

    this.http.post(setHomeMessagePath, this.homeMessages, {responseType: 'text'})
      .subscribe({
        next: (message: string) => {
          this.alerts.push({type: 'success', message: message}); 
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({type: 'danger', message: err.error});
        }
      });
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
