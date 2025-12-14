import { Component } from '@angular/core';
import { Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { GameConfigurationService } from '../../service/game-configuration-service';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-user-editor',
  imports: [FormsModule, NgbDropdownModule],
  templateUrl: './user-editor.html'
})
export class UserEditor {
  @Input() userData: UserData = {};
  @Input() disabledAfterRegister: boolean = false;
  @Input() currentLanguage: string = 'en';

  gameConfiguration: GameConfiguration;

  constructor(private gameConfigurationService: GameConfigurationService) {
    this.gameConfiguration = this.gameConfigurationService.getGameConfiguration();
  }

  getLanguageNameByKey(key: string) {
    let currentIndex: number = 0;

    for (const [index, language] of (this.gameConfiguration?.serverConfiguration.languages ?? []).entries()) {
      if (language.key == this.currentLanguage) {
        currentIndex = index;
      }
    }

    for (let language of this.gameConfiguration?.serverConfiguration.languages ?? []) {
      if (language.key == key) {
        return language.tr[currentIndex];
      }
    }      

    return this.gameConfiguration?.serverConfiguration.languages?.[0].tr[currentIndex];
  }
}
