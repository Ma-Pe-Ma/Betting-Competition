import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { GameConfigurationService } from '../../../service/game-configuration-service';
import { DecimalPipe } from '@angular/common';
import { environment } from '../../../../environments/environment';
import { ResultNamePipe } from '../../../pipes/result-name-pipe';
import { FormsModule } from '@angular/forms';
import { tap, catchError, forkJoin, of} from 'rxjs';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { CdkDrag, CdkDragDrop, CdkDropList, moveItemInArray} from '@angular/cdk/drag-drop';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { OddModal } from '../../modals/odd-modal/odd-modal';

@Component({
  selector: 'app-group-before',
  imports: [DecimalPipe, ResultNamePipe, FormsModule, NgbDropdownModule, CdkDropList, CdkDrag, NgbAlertModule],
  templateUrl: './group-before.html'
})
export class GroupBefore {
  betValues: BetValues | null = null;
  groupHitMap: GroupHitMap | null = null;

  playerInput: GroupResponse | null = null;
  tournamentOdds: TournamentOdds[] | null = [];

  alerts: Alert[] = []

  constructor(private http: HttpClient, private gameConfigurationService: GameConfigurationService, private modalService: NgbModal) {
    let gameConfiguration = this.gameConfigurationService.getGameConfiguration();

    this.betValues = gameConfiguration?.betValues;
    this.groupHitMap = gameConfiguration?.groupHitMap;

    let groupStatusPath = environment.locations.group.get;
    let tournamentOddPath = environment.locations.group.tournament;
    
    forkJoin({
      group: this.http.get<GroupResponse>(groupStatusPath).pipe(
        catchError(err => {
          console.error('Error fetching group results:', err);
            return of(null);
        })
      ),
      tournamentOdds: this.http.get<TournamentOdds[]>(tournamentOddPath).pipe(
        catchError(err => {
          console.error('Error fetching player results:', err);
          return of(null);
        })
      )
    }).subscribe({
      next: ({ group, tournamentOdds }) => {
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
      error: (err) => {
        console.error('Unexpected error:', err);
      }
    });
  }

  teamSelected(team: string) {
    this.playerInput!.tournament!.team! = team;

    for (let tournamentOdd of this.tournamentOdds ?? []) {
      if (tournamentOdd.team == team) {
        this.playerInput!.tournament!.local_name! = tournamentOdd.team_tr;
      }
    }
  }

  resultSelected(result: number) {
    this.playerInput!.tournament!.result! = result;
  }

  getCurrentTournamentOdd(): number {
    for (let tournamentOdd of this.tournamentOdds ?? []) {
      if (tournamentOdd.team == this.playerInput!.tournament!.team!) {
          return tournamentOdd.odds[this.playerInput!.tournament!.result!];
      }
    }

    return 0
  }

  calculatePrize() {
    return this.playerInput?.tournament.bet! * this.getCurrentTournamentOdd();
  }

  drop(event: CdkDragDrop<string[]>, teams: Team[]) {
    moveItemInArray(teams, event.previousIndex, event.currentIndex);
  }

  postGroups() {
    let groupPostPath = environment.locations.group.set;

    this.http.post<Alert>(groupPostPath, this.playerInput).pipe(
      tap(alert => {
        this.alerts.push(alert);
      }),
      catchError(err => {
        console.error('Error fetching group results:', err);
          return of(null);
      })
    ).subscribe();
  }

  calculateRemainingCredit() {
    return (this.betValues?.starting_bet_amount ?? 0) - (this.playerInput?.groups ?? []).reduce((sum, item) => sum +item.bet, 0) - (this.playerInput?.tournament?.bet ?? 0);
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}

  showOddModal() {
    const modalRef = this.modalService.open(OddModal);
    let oddModal: OddModal = modalRef.componentInstance;
    oddModal.odds = this.tournamentOdds ?? [];
  }
}
