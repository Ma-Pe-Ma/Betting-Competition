import { HttpClient, HttpParams, HttpErrorResponse } from '@angular/common/http';
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { tap } from 'rxjs';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { NgbAlert } from '@ng-bootstrap/ng-bootstrap';
import { LocalDatePipe } from '../../../pipes/local-date-pipe';
import { AuthService } from '../../../service/auth-service';
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

  constructor(private http: HttpClient, public activeModal: NgbActiveModal, private authService: AuthService) {
    this.authService.getUser$.subscribe(user => {
        this.user = user;
    });
  }

  fetchMatchData(matchID: number) {
    const params = new HttpParams().set('matchID', matchID);
    let path = this.admin ? paths.admin.match.get : paths.match;

    this.http.get<Match>(path, { params: params})
      .subscribe({
        next: (value: Match) => {
          this.match = value as Match;
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({'type': 'danger', 'message': err.error}) 
        }
      });
  }

  postMatchData(matchID: number) {
    const params = new HttpParams().set('matchID', matchID);

    let path = this.admin ? paths.admin.match.set : paths.match;
    this.http.post(path, this.match, { params: params, responseType: 'text' })
      .subscribe({
        next: (message: string) => {
          this.betPosted.emit(true);
          this.alerts.push({'type': 'success', 'message': message}); 

          setTimeout(() => {
            this.activeModal.close();
          }, 1500);
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
