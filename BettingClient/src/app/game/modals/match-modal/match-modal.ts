import { HttpClient, HttpParams, HttpErrorResponse } from '@angular/common/http';
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { of, tap } from 'rxjs';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { NgbAlert } from '@ng-bootstrap/ng-bootstrap';
import { LocalDatePipe } from '../../../pipes/local-date-pipe';
import { AuthService } from '../../../service/auth-service';
import { HttpDataHandler } from '../../../service/http-data-handler';
import { map, catchError } from 'rxjs';
import { paths } from '../../../paths';
import { FormsModule } from '@angular/forms';
import { ClampDirective } from '../../../../shared/directives/clamp.directive';

@Component({
  selector: 'app-match-modal',
  imports: [NgbAlert, LocalDatePipe, FormsModule, ClampDirective],
  templateUrl: './match-modal.html'
})
export class MatchModal {
  @Input() admin: boolean = false;
  @Output() betPosted: EventEmitter<boolean> = new EventEmitter<boolean>();
  match: Match | null = null;

  alerts: Alert[] = []

  user: User|null = null;

  constructor(private httpDataHandler: HttpDataHandler, private http: HttpClient, public activeModal: NgbActiveModal, private authService: AuthService) {
    this.authService.getUser$.subscribe(user => {
        this.user = user;
    });
  }

  fetchMatchData(matchID: number) {
    const params = new HttpParams().set('matchID', matchID);
    let path = this.admin ? paths.admin.match.get : paths.match;

    this.http.get<Match>(path, { params: params, observe: 'response' }).pipe(
      map(response => response.body),
      catchError((err: HttpErrorResponse) => {
        if(err.status == 400) {
          return of(err.error as Alert);
        }

        console.error('Error updating matches:', err);
        return of({message: 'Unknown error: ' +err.error, type: 'danger'} as Alert);
      })
    )
    .subscribe(value => {
      if (value && (value as any).message) {
        this.alerts.push(value as Alert);
      }
      else {
        this.match = value as Match;
      }
    });
  }

  postMatchData(matchID: number) {
    const params = new HttpParams().set('matchID', matchID);
    let path = this.admin ? paths.admin.match.set : paths.match;
    this.http.post<Alert>(path, this.match, { params }).pipe(
      tap(value => {
        this.betPosted.emit(true);
      })
    )
    .subscribe({
      next: (value: Alert) =>{
        this.alerts.push(value); 
      },
      error: (err: HttpErrorResponse) => {
        this.alerts.push({'type': 'danger', 'message': err.error})
      }
    });    
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
