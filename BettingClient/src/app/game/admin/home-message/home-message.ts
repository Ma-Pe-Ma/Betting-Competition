import { Component } from '@angular/core';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { FormsModule } from '@angular/forms';
import { HttpDataHandler } from '../../../service/http-data-handler';
import { paths } from '../../../paths';

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

  constructor(private httpDataHandler: HttpDataHandler) {
    let getHomeMessagePath = paths.admin.homeMessage.get;
    
    this.httpDataHandler.getData<HomeMessageContainer[]>(getHomeMessagePath).subscribe(value => {
      if (value && (value as any).message) {
        this.alerts.push(value as Alert);
      }
      else {
        this.homeMessages = value as HomeMessageContainer[];
      }
    });
  }

  postMessages() {
    let setHomeMessagePath = paths.admin.homeMessage.set;  

    this.httpDataHandler.postData(setHomeMessagePath, this.homeMessages).subscribe(value => {
        this.alerts.push(value); 
    });
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
