import { Component } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import { tap, catchError } from 'rxjs';
import { LocalDatePipe } from '../../../pipes/local-date-pipe';
import { AuthService } from '../../../service/auth-service';
import { MatchModal } from '../../modals/match-modal/match-modal';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-admin-match',
  imports: [DecimalPipe, LocalDatePipe],
  templateUrl: './admin-match.html'
})
export class AdminMatch {
  matches: Match[] = []
  timeZone: string = "";

  user: User|null = null;

  constructor(private http: HttpClient, private authService: AuthService,  private modalService: NgbModal) {
    this.authService.getUser$.subscribe(user => {
      this.user = user;
    });

    this.fetchMatches();
  }

  fetchMatches() {
    let adminMatchPath = environment.serverAddress + environment.locations.admin.match.list;

    this.http.get<Match[]>(adminMatchPath).pipe(
      tap(data => {
        this.matches = data;
      }),
      catchError(err => {
        console.error('Error fetching group results:', err);
        return [];
      })
    ).subscribe();
  }

  modifyMatch(matchID: number) {
    const modalRef = this.modalService.open(MatchModal);
    let matchModal: MatchModal = modalRef.componentInstance;
    matchModal.admin = true;
    matchModal.fetchMatchData(matchID);

    matchModal.betPosted.subscribe((posted: boolean) => {
      this.fetchMatches();
    });
  }

  fetchFromFixture() {
    let updateMatchPath = environment.serverAddress + environment.locations.admin.match.update;

    this.http.get<Alert>(updateMatchPath).pipe(
      tap(data => {
        
      }),
      catchError(err => {
        console.error('Error updating matches:', err);
        return [];
      })
    ).subscribe();
  }
}
