import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environment';
import { UserEditor } from '../user-editor/user-editor';
import { Reminder } from '../reminder/reminder';
import { GameConfigurationService } from '../../service/game-configuration-service';
import { take } from 'rxjs';
import { MarkdownComponent, provideMarkdown } from 'ngx-markdown';
import { AuthService } from '../../service/auth-service';

@Component({
  selector: 'app-register',
  imports: [UserEditor, Reminder, FormsModule, NgbAlertModule, MarkdownComponent],
  templateUrl: './register.html',
  providers: [provideMarkdown()]
})
export class Register {
  userData: UserData = {reminder: 0, summary: 0, language: 'en'};
  alerts: Alert[] = []

  registerMessage: string = "";
  registerClosed: boolean = true;

  constructor(private http: HttpClient, private router: Router, private gameConfigurationService: GameConfigurationService, private authService: AuthService) {
    let gameConfig = this.gameConfigurationService.getGameConfiguration();

    if (gameConfig.deadlineTimes.group_evaluation > gameConfigurationService.getCurrentTime()) {
        let registerMessagePath = environment.locations.auth.registerMessage;
        this.http.get<{introduction: string}>(registerMessagePath).subscribe(message => this.registerMessage = message.introduction);
        this.registerClosed = false;
    }
  }

  register() {
    let location = environment.locations.auth.register;
    this.http.post<Alert>(location, this.userData, {observe: 'response'}).subscribe((response: HttpResponse<Alert>) => {
      let newAlert: Alert = response.body!;

      this.alerts.push(newAlert);

      if (newAlert.type === 'success') {
        this.authService.signIn();
        this.authService.getUser$.pipe(take(1)).subscribe(user => {
          setTimeout(() => {
            this.router.navigate(['/']);
          }, 1000);
        });    
      }
    });
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
	}

  onLanguageSelected(languageKey: string) {
    this.userData.language = languageKey;
  }
}
