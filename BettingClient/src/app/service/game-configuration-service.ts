import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, filter, tap, catchError, EMPTY} from 'rxjs';
import { firstValueFrom } from 'rxjs';
import { GroupState } from '../models/group-state';
import { MainState } from '../models/main-state';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class GameConfigurationService {
  gameConfiguration$: BehaviorSubject<GameConfiguration | null > = new BehaviorSubject<GameConfiguration | null >(null);

  constructor(private http: HttpClient) {}

  getGameConfiguration$(): Observable<GameConfiguration | null> {
    if (this.gameConfiguration$.value === null) {
      this.fetchGameData();
    }

    return this.gameConfiguration$.asObservable();
  }

  private fetchGameData() {
    let configPath = environment.serverAddress + environment.locations.gameConfiguration;

    this.http.get<GameConfiguration>(configPath, {observe: 'response'}).pipe(
      tap(res => {
        if (res.status === 200) {
          let processedBody = res.body!

          this.gameConfiguration$.next({
            betValues: processedBody.betValues,
            deadlineTimes: {              
              register: new Date(processedBody.deadlineTimes.register),
              group_evaluation: new Date(processedBody.deadlineTimes.group_evaluation),
              tournament_end: new Date(processedBody.deadlineTimes.tournament_end)
            },
            serverConfiguration: processedBody.serverConfiguration,
            groupHitMap: processedBody.groupHitMap
          });
        }
        else {
          this.gameConfiguration$.next(null);
        }
      }),
      catchError(err => {
        console.error('Error fetching config: ', err);
        return EMPTY
      })
    ).subscribe();  
  }

  async getGroupState(): Promise<GroupState | null> {
    let gameData: GameConfiguration = await firstValueFrom(
      this.getGameConfiguration$().pipe(
        filter((v): v is GameConfiguration => v !== null)
      )
    );

    let currentTime = this.getCurrentTime().getTime();

    if (currentTime < gameData.deadlineTimes.register.getTime()) {
      return Promise.resolve(GroupState.NOT_STARTED);
    }
    else if (gameData.deadlineTimes.register.getTime() <= currentTime && currentTime < gameData.deadlineTimes.group_evaluation.getTime()) {
      return Promise.resolve(GroupState.IN_PROGRESS);
    }
    else if (gameData.deadlineTimes.group_evaluation.getTime() <= currentTime) {
      return Promise.resolve(GroupState.EVALUATED);
    }

    return Promise.resolve(null);
  }

  async getMainState(): Promise<MainState | null> {
    let gameData: GameConfiguration = await firstValueFrom(
      this.getGameConfiguration$().pipe(
        filter((v): v is GameConfiguration => v !== null)
      )
    );

    let currentTime = this.getCurrentTime().getTime();   

    if (currentTime < gameData.deadlineTimes.tournament_end.getTime()) {
      return Promise.resolve(MainState.GAME);
    }
    else if (gameData.deadlineTimes.tournament_end.getTime() <= currentTime) {
      return Promise.resolve(MainState.STATISTICS);
    }

    return Promise.resolve(null);
  }

  async getBetValues(): Promise<BetValues | null> {
     let gameData: GameConfiguration = await firstValueFrom(
      this.getGameConfiguration$().pipe(
        filter((v): v is GameConfiguration => v !== null)
      )
    );

    return Promise.resolve(gameData.betValues);
  }

  getCurrentTime(): Date {
    if (environment.useMockTime) {
      return new Date(environment.mockTime);
    }

    return new Date();
  }
}
