import { Component } from '@angular/core';
import { GameConfigurationService } from '../../service/game-configuration-service';
import { GroupState } from '../../models/group-state';
import { AsyncPipe } from '@angular/common';
import { GroupBefore } from './group-before/group-before';
import { GroupAfter } from './group-after/group-after';

@Component({
  selector: 'app-group-bet',
  imports: [AsyncPipe, GroupBefore, GroupAfter],
  templateUrl: './group-bet.html'
})
export class GroupBet {
  readonly GroupState = GroupState;
  groupState$: Promise<GroupState | null> | undefined;
  
  constructor(private gameConfigurationService : GameConfigurationService) {
    this.groupState$ = this.gameConfigurationService.getGroupState();
  }  
}
