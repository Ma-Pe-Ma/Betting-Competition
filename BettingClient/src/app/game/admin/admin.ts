import { Component } from '@angular/core';
import { NgbAccordionModule } from '@ng-bootstrap/ng-bootstrap';
import { AdminMatch } from './admin-match/admin-match';
import { HomeMessage } from './home-message/home-message';
import { SendMessage } from './send-message/send-message';
import { GenerateStandings } from './generate-standings/generate-standings';
import { GroupOrder } from './group-order/group-order';
import { TournamentResult } from './tournament-result/tournament-result';
import { TeamData } from './team-data/team-data';
import { Maintenance } from './maintenance/maintenance';
import { PasswordReset } from './password-reset/password-reset';

@Component({
  selector: 'app-admin',
  imports: [NgbAccordionModule, AdminMatch, HomeMessage, SendMessage, GenerateStandings, GroupOrder, TournamentResult, TeamData, Maintenance, PasswordReset],
  templateUrl: './admin.html'
})
export class Admin {
  
}
