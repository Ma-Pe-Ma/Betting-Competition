import { Component } from '@angular/core';
import { environment } from '../../../../environments/environment';
import { DropdownSelector } from '../../dropdown-selector/dropdown-selector';
import { HttpClient } from '@angular/common/http';
import { tap, catchError } from 'rxjs/operators';
import { DecimalPipe } from '@angular/common';

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
  dateListLocation: string = environment.locations.results.dates;
  dateMap: Map<string, MatchContainer[]> = new Map<string, MatchContainer[]>(); 
  currentDate: MatchContainer[] | null = null;

  constructor(private http: HttpClient) {}

  receiveSelectedDate(date: string) {
    if (this.dateMap.has(date)) {
        this.currentDate = this.dateMap.get(date)!;
      }
    else {
      this.currentDate = null;
      let path = environment.locations.results.dateResults;
      const params = { date: date };

      this.http.get<MatchContainer[]>(path, {params}).pipe(
        tap(data => {
          this.dateMap.set(date, data);
          this.currentDate = data;
        }),
        catchError(err => {
          console.error('Error fetching player results:', err);
          return [];
        })
      ).subscribe();
    } 
  }
}
