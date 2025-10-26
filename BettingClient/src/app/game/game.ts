import { Component } from '@angular/core';
import { RouterOutlet, RouterModule, ActivatedRoute, Router, NavigationEnd, Routes} from '@angular/router';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { routes as gameRoutes } from './game.routes';
import { AuthService } from '../service/auth-service';
import { Observable, tap, take } from 'rxjs';
import { AsyncPipe } from '@angular/common';
import { NgbAlertModule } from '@ng-bootstrap/ng-bootstrap';
import { MarkdownComponent, provideMarkdown } from 'ngx-markdown';
import { PushNotificationService } from '../service/push-notification-service';

@Component({
  selector: 'app-game',
  imports: [RouterOutlet, RouterModule, NgbDropdownModule, AsyncPipe, NgbAlertModule, MarkdownComponent],
  standalone: true,
  templateUrl: './game.html',
  providers: [provideMarkdown()]
})
export class Game {
  ribbonRoutes = ['', 'results', 'standings', 'group-bet', 'chat', 'admin'];
  routes: Routes = [];
  currentLocation = "";
  alerts: Alert[] = []

  user$: Observable<User | null>  = new Observable<User | null>();

  constructor(private router: Router, private auth: AuthService, private pushNotificationService: PushNotificationService) {
    this.user$ = auth.getUser$

    this.user$.pipe(
      take(1),
      tap(user => {
        for (let r of gameRoutes) {
          if (!this.ribbonRoutes.includes(r.path!)) {
            continue;
          }
          
          if ((user?.role ?? 0) < (r.data?.['role'] ?? 0)) {
            continue;     
          }

          this.routes.push(r);
        }

        this.alerts = user?.messages ?? [];
      })
    ).subscribe();

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
