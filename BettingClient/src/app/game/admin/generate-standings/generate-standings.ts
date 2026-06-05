import { Component } from '@angular/core';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { paths } from '../../../paths';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-generate-standings',
  imports: [NgbAlertModule],
  templateUrl: './generate-standings.html'
})
export class GenerateStandings {
  emails: string = "";
  standings: string = "";

  alerts: Alert[] = []

  constructor(private http: HttpClient) {

  }

  sendStandingsImmediately() {
    let sendImmediatelyPath = paths.admin.standings.sendImmediately;

    this.http.get(sendImmediatelyPath, {responseType: 'text'})
      .subscribe({
        next: (message: string) => {
          this.alerts.push({type: 'success', message: message})
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({type: 'danger', message: err.error})
        }
      });
  }

  getStandings() {
    let standingsGetPath = paths.admin.standings.get;
  
    type StandingsData = {emails: string, standings: string};

    this.http.get<StandingsData>(standingsGetPath)
      .subscribe({
        next: (standingsData: StandingsData ) => {
          this.emails = standingsData.emails;
          this.standings = standingsData.standings;
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
