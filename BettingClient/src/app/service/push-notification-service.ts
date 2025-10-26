import { Injectable } from '@angular/core';
import { filter } from 'rxjs';
import { SwPush } from '@angular/service-worker';
import { HttpClient } from '@angular/common/http';
import { GameConfigurationService } from '../service/game-configuration-service';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class PushNotificationService {
  
  constructor(private gameConfigurationService: GameConfigurationService, private swPush: SwPush, private http: HttpClient) {

  }

  subscribeToPush() {
    this.gameConfigurationService.getGameConfiguration$()
    .pipe(
      filter((value): value is GameConfiguration => value !== null) 
    )
    .subscribe(gameConfiguration => {
      console.log("?SUBS?")
      this.swPush.subscription.subscribe(subscription => {
        if (!subscription) {
          this.swPush.requestSubscription({
            serverPublicKey: gameConfiguration?.serverConfiguration.pushKey!
          })
          .then(subscription => {
            let pushPath = environment.serverAddress + environment.locations.push;
            this.http.post(pushPath, subscription).subscribe(response => {
              console.log("Sucessfuly sent subscription to server:...")
            })
          })
        }
      });
    });
  }
}
