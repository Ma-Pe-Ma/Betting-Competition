import { HttpClient, HttpParams, HttpErrorResponse } from '@angular/common/http';
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { BehaviorSubject, of, tap } from 'rxjs';
import { AsyncPipe } from '@angular/common';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../../environments/environment';
import { NgbAlert } from '@ng-bootstrap/ng-bootstrap';
import { LocalDatePipe } from '../../../pipes/local-date-pipe';
import { AuthService } from '../../../service/auth-service';
import { HttpDataHandler } from '../../../service/http-data-handler';
import { map, catchError } from 'rxjs';

@Component({
  selector: 'app-match-modal',
  imports: [AsyncPipe, NgbAlert, LocalDatePipe],
  templateUrl: './match-modal.html'
})
export class MatchModal {
  @Input() admin: boolean = false;
  @Output() betPosted: EventEmitter<boolean> = new EventEmitter<boolean>();
  match$: BehaviorSubject<Match | null> = new BehaviorSubject<Match | null>(null);

  alerts: Alert[] = []

  user: User|null = null;

  constructor(private httpDataHandler: HttpDataHandler, private http: HttpClient, public activeModal: NgbActiveModal, private authService: AuthService) {
    this.authService.getUser$.subscribe(user => {
        this.user = user;
    });
  }

  updateMatchField<K extends keyof Match>(key: K, value: Match[K]) {
    const current = this.match$.getValue();
    this.match$.next({ ...current, [key]: value });
  }

  fetchMatchData(matchID: number) {
    const params = new HttpParams().set('matchID', matchID);
    let path = this.admin ? environment.locations.admin.match.get : environment.locations.match;

    this.http.get<Match>(path, { params, observe: 'response' }).pipe(
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
        this.match$?.next(value as Match);
      }
    });
  }

  postMatchData(matchID: number) {
    const params = new HttpParams().set('matchID', matchID);
    let path = this.admin ? environment.locations.admin.match.set : environment.locations.match;
    this.http.post<Alert>(path, this.match$.value, { params }).pipe(
      tap(value => {
        this.betPosted.emit(true);
      }),
      catchError((err: HttpErrorResponse) => {
        console.error('Error updating match: ', err);
        return of({message: 'Unknown error: ' +err.error, type: 'danger'} as Alert);
      })
    )
    .subscribe(value => {
      this.alerts.push(value as Alert); 
    });    
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}
}
