import { Component } from '@angular/core';
import { environment } from '../../../../environments/environment';
import { forkJoin } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { DecimalPipe } from '@angular/common';
import { DayNamePipe } from '../../../pipes/day-name-pipe';
import { NgTemplateOutlet } from '@angular/common';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { MatchModal } from '../../modals/match-modal/match-modal';

@Component({
  selector: 'app-betting',
  imports: [DecimalPipe, DayNamePipe, NgTemplateOutlet],
  templateUrl: './betting.html'
})
export class Betting {
  currentBalance: number = 0;
  days: Day[] = [];

  constructor(private http: HttpClient, private modalService: NgbModal) {
    this.fetchMetchData();
  }

  fetchMetchData() {
    let r1 = this.http.get<Day[]>(environment.serverAddress + environment.locations.main.matches);
    let r2 = this.http.get<{credit: number}>(environment.serverAddress + environment.locations.main.credit);

    forkJoin([r1, r2]).subscribe({
      next: ([days, credit] : [Day[], {credit: number}]) => {
        this.days = days;
        this.currentBalance = credit.credit;
      },
      error: (err) => {
        console.error('Error fetching data: ', err);
      }
    });
  }

  makeBet(matchID: number) {
    const modalRef = this.modalService.open(MatchModal);
    let matchModal: MatchModal = modalRef.componentInstance;
    matchModal.fetchMatchData(matchID);

    matchModal.betPosted.subscribe((posted: boolean) => {
      this.fetchMetchData();
    });
  }
}
