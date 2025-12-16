import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { DayNamePipe } from '../../../pipes/day-name-pipe';
import { DecimalPipe, DatePipe } from '@angular/common';
import { GameConfigurationService } from '../../../service/game-configuration-service';
import { AuthService } from '../../../service/auth-service';
import { tap, catchError } from 'rxjs';
import { paths } from '../../../paths';
import { DropdownSelector } from '../../dropdown-selector/dropdown-selector';

interface ExtraData {
  startAmount?: number,
  groupAndTournamentBetCredit?: number,
  groupBonus?: number
  balanceAfterGroup?: number,
  currentBalance?: number,
  successRate?: number
}

interface PlayerData {
  days? : Day[],
  extraData?: ExtraData
  tournamentBet?: TournamentBet
}

@Component({
  selector: 'app-player-results',
  imports: [DayNamePipe, DecimalPipe, DatePipe, DropdownSelector],
  templateUrl: './player-results.html'
})
export class PlayerResults {
  playerListLocation: string = paths.results.playerNames;
  gameData: GameConfiguration;

  playerResults: Map<string, PlayerData> = new Map<string, PlayerData>(); 
  currentPlayer: PlayerData | null = null;
  currentPlayerName: string = "";

  constructor(private http: HttpClient, gameConfigurationService: GameConfigurationService, private authService: AuthService) {
    this.gameData = gameConfigurationService.getGameConfiguration();
  } 

  ngOnInit() {
    this.authService.getUser$.subscribe(user => {
      this.currentPlayerName = user!.username!;
    });
  }

  receiveSelectedPlayer(playerName: string) {
    if (this.playerResults.has(playerName)) {
      this.currentPlayer = this.playerResults.get(playerName)!;
    }
    else {
      this.currentPlayer = null;
      let path = paths.results.playerResults;
      const params = { name: playerName };

      this.http.get<PlayerData>(path, {params}).pipe(
        tap(data => {
          this.playerResults.set(playerName, data);
          this.currentPlayer = data;
        }),
        catchError(err => {
          console.error('Error fetching player results:', err);
          return [];
        })
      ).subscribe();
    } 
  }
}
