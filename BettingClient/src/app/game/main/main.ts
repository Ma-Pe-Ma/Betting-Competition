import { Component } from '@angular/core';
import { GameConfigurationService } from '../../service/game-configuration-service';
import { MainState } from '../../models/main-state';
import { Betting } from './betting/betting';
import { Statistics } from './statistics/statistics';

@Component({
  selector: 'app-main',
  imports: [Betting, Statistics],
  templateUrl: './main.html',
  standalone: true
})
export class Main {
  MainState = MainState;  
  mainState: MainState | null = null;

  constructor(private gameConfigurationService : GameConfigurationService) {
    let mainState$ = this.gameConfigurationService.getMainState();
    mainState$.then(mainState =>{
      this.mainState = mainState;
    });
  }    
}
