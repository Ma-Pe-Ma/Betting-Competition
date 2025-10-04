import { Component } from '@angular/core';
import { RouterOutlet, RouterModule } from '@angular/router';

interface NavElement {
  route: string,
  title: string,
  admin: boolean
}

@Component({
  selector: 'app-game',
  imports: [RouterOutlet, RouterModule],
  standalone: true,
  templateUrl: './game.html',
  styleUrl: './game.scss'
})
export class Game {

  emailHash: string = ""; //config['IDENT_URL'].format(email_hash=g.user['email_hash'])
  username: string = "MPM"; //"{{g.user['username']}}
  admin: boolean = true;

  currentLocation = "/";

  navigationAddresses: NavElement[] = [
    {
      route: '/',
      title: $localize`:betting:Betting`,
      admin: false
    },
    {
      route: '/results',
      title: $localize`:results:Results`,
      admin: false
    },
    {
      route: '/standings',
      title: $localize`:standings:Standings`,
      admin: false
    },
    {
      route: '/group-bet',
      title: $localize`:group_bet:Group bet`,
      admin: false
    },
    {
      route: '/chat',
      title: $localize`:chat:Chat`,
      admin: false
    },
    {
      route: '/admin',
      title: $localize`:admin:Admin`,
      admin: false
    },
  ]
}
