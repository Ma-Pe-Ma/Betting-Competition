import { Component, Input } from '@angular/core';
import { RESULTNAME_MAP, ResultNamePipe } from '../../../pipes/result-name-pipe';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-odd-modal',
  imports: [ResultNamePipe],
  templateUrl: './odd-modal.html'
})
export class OddModal {
  @Input() odds: TournamentOdds[] = []

  constructor(public activeModal: NgbActiveModal) {

  }

  getResultCount() {
    return Array.from({ length: Object.keys(RESULTNAME_MAP).length }, (_, i) => i);
  }
  
}
