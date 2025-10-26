import { HttpClient } from '@angular/common/http';
import { Component } from '@angular/core';
import { environment } from '../../../../environments/environment';
import { AuthService } from '../../../service/auth-service';
import { tap, catchError } from 'rxjs';
import { DropdownSelector } from '../../dropdown-selector/dropdown-selector';
import { GameConfigurationService } from '../../../service/game-configuration-service';
import { ResultNamePipe } from '../../../pipes/result-name-pipe';
import { NgClass } from '@angular/common';
import { GroupState } from '../../../models/group-state';

@Component({
  selector: 'app-group-after',
  imports: [DropdownSelector, ResultNamePipe, NgClass],
  templateUrl: './group-after.html'
})
export class GroupAfter {
  GroupState = GroupState;  
  groupState: GroupState | null = null;

  playerListLocation: string = environment.serverAddress + environment.locations.results.playerNames;
  players: Map<string, GroupResponse> = new Map();
  currentPlayer: GroupResponse | null = null;
  currentPlayerName: string = "";
  betValues: BetValues | null = null;

  totalBet: number = 0;
  totalWin?: number = undefined;

  constructor(private http: HttpClient, private authService: AuthService, private gameConfigurationService: GameConfigurationService) {
    let betValues$ = gameConfigurationService.getBetValues();
    betValues$.then(betValues => {
      this.betValues = betValues;
    }); 

    let groupState$ = gameConfigurationService.getGroupState();
    groupState$.then(groupState => {
      this.groupState = groupState;
    })
  }

  ngOnInit() {
    this.authService.getUser$.subscribe(user => {
      this.currentPlayerName = user!.username!;
    });
  }

  receiveSelectedPlayer(playerName: string) {
    if (this.players.has(playerName)) {
      this.setCurrentPlayer(this.players.get(playerName)!)
    }
    else {
      this.currentPlayer = null;

      let groupStatusPath = environment.serverAddress + environment.locations.group.get;
      const params = { name: playerName };
      this.http.get<GroupResponse>(groupStatusPath, {params}).pipe(
        tap(data => {
          this.players.set(playerName, data);
          this.setCurrentPlayer(data)
        }),
        catchError(err => {
          console.error('Error fetching group results:', err);
          return [];
        })
      ).subscribe();
    }
  }

  setCurrentPlayer(newPlayer: GroupResponse) {
      this.currentPlayer = newPlayer;
      this.totalBet = newPlayer.groups.reduce((sum, item) => sum + item.bet, 0) + newPlayer.tournament.bet;
      this.totalWin = newPlayer.groups.reduce((sum, item) => sum + item.prize, 0)
  }
}
