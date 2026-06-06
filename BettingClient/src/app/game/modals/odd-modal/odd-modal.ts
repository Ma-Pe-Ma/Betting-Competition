import { Component, Input } from '@angular/core';
import { RESULTNAME_MAP, ResultNamePipe } from '../../../pipes/result-name-pipe';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

type SortOrder = 'asc' | 'desc';

@Component({
  selector: 'app-odd-modal',
  imports: [ResultNamePipe],
  templateUrl: './odd-modal.html'
})
export class OddModal {
  @Input() odds: TournamentOdds[] = []

  currentField: number|null = 0;
  currentOrder: SortOrder = 'asc';

  constructor(public activeModal: NgbActiveModal) {}

  setSort(field: number|null) {
    if (this.currentField === field) {
      this.currentOrder = this.currentOrder === 'asc' ? 'desc' : 'asc';
    } else {
      this.currentField = field;
      this.currentOrder = 'asc';
    }
  }

  get sortedOdds(): TournamentOdds[] {
    if (!this.odds) return [];

    if (this.currentField == null) {
      return [...this.odds].sort((a: TournamentOdds, b: TournamentOdds) => {
        let teamA = a.team_tr;
        let teamB = b.team_tr;

        return this.currentOrder === 'asc' 
          ? teamA.localeCompare(teamB) 
          : teamB.localeCompare(teamA);
      });
    }

    return [...this.odds].sort((a: TournamentOdds, b: TournamentOdds) => {
      let valueA = a.odds[this.currentField!];
      let valueB = b.odds[this.currentField!];

      if (valueA < valueB) return this.currentOrder === 'asc' ? -1 : 1;
      if (valueA > valueB) return this.currentOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }

  getResultCount() {
    return Array.from({ length: Object.keys(RESULTNAME_MAP).length }, (_, i) => i);
  }
}
