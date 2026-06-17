import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';
import { UserEditor } from '../user-editor/user-editor';
import { Reminder } from '../reminder/reminder';
import { GameConfigurationService } from '../../service/game-configuration-service';
import { MarkdownComponent, provideMarkdown } from 'ngx-markdown';
import { AuthService } from '../../service/auth-service';
import { paths } from '../../paths';

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

  disabled = false;

  constructor(private http: HttpClient, private router: Router, private gameConfigurationService: GameConfigurationService, private authService: AuthService) {
    let gameConfig = this.gameConfigurationService.getGameConfiguration();

    if (gameConfigurationService.getCurrentTime() < gameConfig.deadlineTimes.register) {
      let registerMessagePath = paths.auth.registerMessage;
      this.http.get(registerMessagePath, {responseType: 'text'})
        .subscribe({
          next: (message: string) => {
            this.registerMessage = message
          }
        });
      
      this.registerClosed = false;
    }
  }

  register() {
    this.disabled = true;

    let location = paths.auth.register;
    this.http.post(location, this.userData, {responseType: 'text'})
      .pipe(
        finalize(()=> {this.disabled = false;})
      )
      .subscribe({
        next: (message: string) => {
          this.alerts.push({'type': 'success', 'message': message});
          this.authService.fetchAuthStatus().subscribe({
            next: () => {
              setTimeout(() => {
                this.router.navigate(['/']);
              }, 1000);
            }
          });
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({'type': 'danger', 'message': err.error}) 
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
