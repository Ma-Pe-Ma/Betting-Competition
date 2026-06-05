import { Component } from '@angular/core';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { HttpClient, HttpErrorResponse} from '@angular/common/http';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { ResultNamePipe } from '../../../pipes/result-name-pipe';
import { paths } from '../../../paths';

const RESULTNAME_MAP: Record<number, string> = {
  0: $localize`:@@undetermined:Undetermined`,
  1: $localize`:@@successful:Successful`,
  2: $localize`:@@failed:Failed`,
};

@Component({
  selector: 'app-tournament-result',
  imports: [NgbAlertModule, NgbDropdownModule, ResultNamePipe],
  templateUrl: './tournament-result.html'
})
export class TournamentResult {
  alerts: Alert[] = []
  tournamentBets: TournamentBet[] = []

  constructor(private http: HttpClient) {
    let tournamentGetPath = paths.admin.tournamentBet.get;
    
    this.http.get<TournamentBet[]>(tournamentGetPath)
      .subscribe({
        next: (tournamentBets: TournamentBet[]) => {
          this.tournamentBets = tournamentBets;
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({type: 'danger', message: err.message});
        }
      });
  }

  postTournamentBets() {
    let tournamentSetPath = paths.admin.tournamentBet.set;

    this.http.post(tournamentSetPath, this.tournamentBets, {responseType: 'text'})
      .subscribe({
        next: (message: string) => {
          this.alerts.push({type: 'success', message: message}); 
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({type: 'danger', message: err.error}); 
        }
      });
  }

  selectSuccess(bet: TournamentBet, success: number) {
    bet.success = success;
  }

  getSuccessName(success: number) {
    return RESULTNAME_MAP[success];
  }

  close(alert: Alert) {
    this.alerts.splice(this.alerts.indexOf(alert), 1);
  }
}
