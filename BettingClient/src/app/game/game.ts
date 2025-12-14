import { Component } from '@angular/core';
import { RouterOutlet, RouterModule, Router, NavigationEnd, Routes} from '@angular/router';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { routes as gameRoutes } from './game.routes';
import { AuthService } from '../service/auth-service';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { MarkdownComponent, provideMarkdown } from 'ngx-markdown';
import { PushNotificationService } from '../service/push-notification-service';

@Component({
  selector: 'app-game',
  imports: [RouterOutlet, RouterModule, NgbDropdownModule, NgbAlertModule, MarkdownComponent],
  standalone: true,
  templateUrl: './game.html',
  providers: [provideMarkdown()]
})
export class Game {
  ribbonRoutes = ['', 'results', 'standings', 'group-bet', 'chat', 'admin'];
  routes: Routes = [];
  currentLocation = "";
  alerts: Alert[] = [];
  user: User;

  constructor(private router: Router, private auth: AuthService, private pushNotificationService: PushNotificationService) {
    this.user = this.auth.getUser();

    for (let r of gameRoutes) {
      if (!this.ribbonRoutes.includes(r.path!)) {
        continue;
      }
      
      if ((this.user.role ?? 0) < (r.data?.['role'] ?? 0)) {
        continue;     
      }

      this.routes.push(r);
    }

    this.alerts = this.user.messages ?? [];

    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        this.currentLocation = event.url[0] === '/' ? event.url.slice(1) : event.url;
      }
    });
  }

  ngOnInit() {
    this.pushNotificationService.subscribeToPush();
  }

  close(alert: Alert) {
		this.alerts.splice(this.alerts.indexOf(alert), 1);
  }
}
