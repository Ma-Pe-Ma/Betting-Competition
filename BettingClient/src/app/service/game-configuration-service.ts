import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, catchError, EMPTY} from 'rxjs';
import { GroupState } from '../models/group-state';
import { MainState } from '../models/main-state';
import { environment } from '../../environments/environment';
import { paths } from '../paths';

@Injectable({
  providedIn: 'root'
})
export class GameConfigurationService {
  gameConfiguration!: GameConfiguration;

  constructor(private http: HttpClient) {}

  getGameConfiguration(): GameConfiguration {
    return this.gameConfiguration;
  }

  public fetchGameData(): Observable<any> {
    let configPath = paths.gameConfiguration;

    return this.http.get<GameConfiguration>(configPath, {observe: 'response'}).pipe(
      tap(res => {
        if (res.status === 200) {
          let processedBody = res.body!
          this.gameConfiguration = processedBody;
          this.gameConfiguration.deadlineTimes = {              
            register: new Date(processedBody.deadlineTimes.register),
            group_evaluation: new Date(processedBody.deadlineTimes.group_evaluation),
            tournament_end: new Date(processedBody.deadlineTimes.tournament_end)
          };
        }
      }),
      catchError(err => {
        console.error('Error fetching config: ', err);
        return EMPTY
      })
    )
  }

  getGroupState(): GroupState {
    let currentTime = this.getCurrentTime().getTime();

    if (currentTime < this.gameConfiguration.deadlineTimes.register.getTime()) {
      return GroupState.NOT_STARTED;
    }
    else if (this.gameConfiguration.deadlineTimes.register.getTime() <= currentTime && currentTime < this.gameConfiguration.deadlineTimes.group_evaluation.getTime()) {
      return GroupState.IN_PROGRESS;
    }
    
    return GroupState.EVALUATED;
  }

  getMainState(): MainState {
    let currentTime = this.getCurrentTime().getTime();   

    if (currentTime < this.gameConfiguration.deadlineTimes.tournament_end.getTime()) {
      return MainState.GAME;
    }
    
    return MainState.STATISTICS;
  }

  getBetValues(): BetValues {
    return this.gameConfiguration.betValues;
  }

  getCurrentTime(): Date {
    if (environment.useMockTime) {
      return new Date(environment.mockTime);
    }

    return new Date();
  }
}
