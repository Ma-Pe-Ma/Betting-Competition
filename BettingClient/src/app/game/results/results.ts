import { Component } from '@angular/core';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { PlayerResults } from "./player-results/player-results";
import { MatchResults } from "./match-results/match-results";

@Component({
  selector: 'app-results',
  imports: [NgbNavModule, MatchResults, PlayerResults],
  templateUrl: './results.html',
})
export class Results {
  active = 1;
}
