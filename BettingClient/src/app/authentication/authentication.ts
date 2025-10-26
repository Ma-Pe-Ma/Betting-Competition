import { Component } from '@angular/core';
import { RouterOutlet, ActivatedRoute, Router, NavigationEnd, RouterLink } from '@angular/router';

@Component({
  selector: 'app-authentication',
  imports: [RouterOutlet, RouterLink],
  templateUrl: './authentication.html',
  styleUrl: './authentication.scss'
})
export class Authentication {

  constructor(private route: ActivatedRoute, private router: Router) {
    this.router.events.subscribe(event => {
      
    });
  }

}
