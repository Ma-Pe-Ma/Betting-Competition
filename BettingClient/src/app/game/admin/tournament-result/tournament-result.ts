import { Component } from '@angular/core';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { HttpClient} from '@angular/common/http';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { HttpDataHandler } from '../../../service/http-data-handler';
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

  constructor(private http: HttpClient, private httpDataHandler: HttpDataHandler) {
    let tournamentGetPath = paths.admin.tournamentBet.get;
    
    this.httpDataHandler.getData<TournamentBet[]>(tournamentGetPath).subscribe(value => {
      if (value && (value as any).message) {
        this.alerts.push(value as Alert);
      }
      else {
        this.tournamentBets = value as TournamentBet[];
      }
    });
  }

  postTournamentBets() {
    let tournamentSetPath = paths.admin.tournamentBet.set;

    this.httpDataHandler.postData(tournamentSetPath, this.tournamentBets).subscribe(value => {
        this.alerts.push(value); 
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
