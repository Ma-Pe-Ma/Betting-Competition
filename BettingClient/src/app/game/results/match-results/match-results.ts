import { Component } from '@angular/core';
import { DropdownSelector } from '../../dropdown-selector/dropdown-selector';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { DecimalPipe } from '@angular/common';
import { paths } from '../../../paths';

interface PlayerBet {
  username?: string,
  bgoal1?: number,
  bgoal2?: number,
  bet?: number,
  bonus?: number,
  prize?: number,
  credit_diff?: number,
  success?: number
} 

interface MatchContainer {
  success?: number,
  players?: PlayerBet[]
  match?: Match
}

@Component({
  selector: 'app-match-results',
  imports: [DropdownSelector, DecimalPipe],
  templateUrl: './match-results.html'
})
export class MatchResults {
  dateListLocation: string = paths.results.dates;
  dateMap: Map<string, MatchContainer[]> = new Map<string, MatchContainer[]>(); 
  currentDate: MatchContainer[] | null = null;

  constructor(private http: HttpClient) {}

  receiveSelectedDate(date: string) {
    if (this.dateMap.has(date)) {
        this.currentDate = this.dateMap.get(date)!;
      }
    else {
      this.currentDate = null;
      let path = paths.results.dateResults;
      const params = { date: date };

      this.http.get<MatchContainer[]>(path, {params: params})
        .subscribe({
          next: (matchContainer: MatchContainer[]) => {
            this.dateMap.set(date, matchContainer);
            this.currentDate = matchContainer;
          },
          error: (err: HttpErrorResponse) => {

          }
        });
    } 
  }
}
