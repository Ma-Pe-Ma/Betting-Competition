import { Component } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { GameConfigurationService } from '../../../service/game-configuration-service';
import { DecimalPipe } from '@angular/common';
import { ResultNamePipe } from '../../../pipes/result-name-pipe';
import { FormsModule } from '@angular/forms';
import { forkJoin, finalize } from 'rxjs';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { CdkDrag, CdkDragDrop, CdkDropList, moveItemInArray} from '@angular/cdk/drag-drop';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { OddModal } from '../../modals/odd-modal/odd-modal';
import { paths } from '../../../paths';
import { ClampDirective } from '../../../../shared/directives/clamp.directive';

@Component({
  selector: 'app-group-before',
  imports: [ClampDirective, DecimalPipe, ResultNamePipe, FormsModule, NgbAlertModule, NgbDropdownModule, CdkDropList, CdkDrag],
  templateUrl: './group-before.html'
})
export class GroupBefore {
  betValues: BetValues | null = null;
  groupHitMap: GroupHitMap | null = null;

  playerInput: GroupResponse | null = null;
  tournamentOdds: TournamentOdds[] | null = [];

  alerts: Alert[] = []
  disabled = false;

  constructor(private http: HttpClient, private gameConfigurationService: GameConfigurationService, private modalService: NgbModal) {
    let gameConfiguration = this.gameConfigurationService.getGameConfiguration();

    this.betValues = gameConfiguration?.betValues;
    this.groupHitMap = gameConfiguration?.groupHitMap;

    let groupStatusPath = paths.group.get;
    let tournamentOddPath = paths.group.tournament;
    
    forkJoin({
      group: this.http.get<GroupResponse>(groupStatusPath),
      tournamentOdds: this.http.get<TournamentOdds[]>(tournamentOddPath)
    }).subscribe({
      next: ({ group, tournamentOdds }: { group: GroupResponse; tournamentOdds: TournamentOdds[] }) => {
        this.playerInput = group;
        this.tournamentOdds = tournamentOdds;

        if (this.playerInput?.tournament.team == undefined && tournamentOdds!.length > 0) {
          this.playerInput!.tournament.team = tournamentOdds![0].team;
          this.playerInput!.tournament.local_name! = tournamentOdds![0].team_tr;
        }

        if (this.playerInput?.tournament.result == undefined) {
          this.playerInput!.tournament.result = 0;
        }
      },
      error: (err: HttpErrorResponse) => {
        this.alerts.push({type: 'danger', message: err.error});
        console.error('Unexpected error:', err);
      }
    });
  }

  teamSelected(team: string) {
    this.playerInput!.tournament!.team! = team;
    this.playerInput!.tournament!.local_name! = this.tournamentOdds?.find(t => t.team == team)?.team_tr ?? ' - ';
  }

  resultSelected(result: number) {
    this.playerInput!.tournament!.result! = result;
  }

  getCurrentTournamentOdd(): number {
    const match = this.tournamentOdds?.find(odd => odd.team === this.playerInput!.tournament!.team!);
    return match?.odds[this.playerInput!.tournament!.result!] ?? 0;
  }

  calculatePrize() {
    return this.playerInput?.tournament.bet! * this.getCurrentTournamentOdd();
  }

  drop(event: CdkDragDrop<string[]>, teams: Team[]) {
    moveItemInArray(teams, event.previousIndex, event.currentIndex);
  }

  postGroups() {
    this.disabled = true;
    let groupPostPath = paths.group.set;

    this.http.post(groupPostPath, this.playerInput, { responseType: 'text' })
      .pipe( finalize(() => {this.disabled = false;}))
      .subscribe({
        next: (message: string) => {
          this.alerts.push({'type': 'success', 'message': message}); 
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({'type': 'danger', 'message': err.error})
        }
      });
  }

  calculateRemainingCredit() {
    return (this.betValues?.starting_bet_amount ?? 0) - (this.playerInput?.groups ?? [])
          .reduce((sum, item) => sum + item.bet, 0) - (this.playerInput?.tournament?.bet ?? 0);
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}

  showOddModal() {
    const modalRef = this.modalService.open(OddModal);
    let oddModal: OddModal = modalRef.componentInstance;
    oddModal.odds = this.tournamentOdds ?? [];
  }
  get teamName(): string {
    return this.playerInput?.tournament?.local_name ?? $localize`:@@chooseTeam:Select Team`;
  }
}
