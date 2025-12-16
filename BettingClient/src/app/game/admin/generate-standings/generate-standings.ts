import { Component } from '@angular/core';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { HttpDataHandler } from '../../../service/http-data-handler';
import { paths } from '../../../paths';

@Component({
  selector: 'app-generate-standings',
  imports: [NgbAlertModule],
  templateUrl: './generate-standings.html'
})
export class GenerateStandings {
  emails: string = "";
  standings: string = "";

  alerts: Alert[] = []

  constructor(private httpDataHandler: HttpDataHandler) {

  }

  sendStandingsImmediately() {
    let sendImmediatelyPath = paths.admin.standings.sendImmediately;

    this.httpDataHandler.getData<Alert>(sendImmediatelyPath).subscribe(value => {
        this.alerts.push(value as Alert);
    });
  }

  getStandings() {
    let standingsGetPath = paths.admin.standings.get;
  
    this.httpDataHandler.getData<{emails: string, standings: string}>(standingsGetPath).subscribe(value => {
      if (value && (value as any).message) {
        this.alerts.push(value as Alert);
      }
      else {
        let v = value as {emails: string, standings: string};
        this.emails = v.emails;
        this.standings = v.standings;
      }
    });
  }

  close(alert: Alert) {
    this.alerts.splice(this.alerts.indexOf(alert), 1);
  }
}
