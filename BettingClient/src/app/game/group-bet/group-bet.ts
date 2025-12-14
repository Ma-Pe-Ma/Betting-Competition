import { Component } from '@angular/core';
import { GameConfigurationService } from '../../service/game-configuration-service';
import { GroupState } from '../../models/group-state';
import { GroupBefore } from './group-before/group-before';
import { GroupAfter } from './group-after/group-after';

@Component({
  selector: 'app-group-bet',
  imports: [GroupBefore, GroupAfter],
  templateUrl: './group-bet.html'
})
export class GroupBet {
  readonly GroupState = GroupState;
  groupState: GroupState;
  
  constructor(private gameConfigurationService : GameConfigurationService) {
    this.groupState = this.gameConfigurationService.getGroupState();
  }  
}
