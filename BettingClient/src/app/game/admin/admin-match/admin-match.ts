import { Component } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { LocalDatePipe } from '../../../pipes/local-date-pipe';
import { AuthService } from '../../../service/auth-service';
import { MatchModal } from '../../modals/match-modal/match-modal';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { paths } from '../../../paths';

@Component({
  selector: 'app-admin-match',
  imports: [CommonModule, DecimalPipe, LocalDatePipe],
  templateUrl: './admin-match.html'
})
export class AdminMatch {
  matches: Match[] = []
  timeZone: string = "";

  user: User;

  constructor(private http: HttpClient, private authService: AuthService,  private modalService: NgbModal) {
    this.user = this.authService.getUser();
    this.fetchMatches();
  }

  fetchMatches() {
    let adminMatchPath = paths.admin.match.list;

    this.http.get<Match[]>(adminMatchPath)
      .subscribe({
        next: (matches: Match[]) => {
          this.matches = matches;
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error fetching group results:', err);
        }
      });
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
    let updateMatchPath = paths.admin.match.update;

    this.http.get(updateMatchPath, {responseType: 'text'})
      .subscribe({
        next: (message: string) => {
          console.error('Succesfully fetched matches:', message);
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error updating matches:', err.error);
        }
      });
  }
}
