import { Injectable } from '@angular/core';
import { SwPush } from '@angular/service-worker';
import { HttpClient } from '@angular/common/http';
import { GameConfigurationService } from '../service/game-configuration-service';
import { paths } from '../paths';

@Injectable({
  providedIn: 'root'
})
export class PushNotificationService {
  
  constructor(private gameConfigurationService: GameConfigurationService, private swPush: SwPush, private http: HttpClient) {}

  subscribeToPush() {
    let gameConfiguration = this.gameConfigurationService.getGameConfiguration();
    
    this.swPush.subscription.subscribe(subscription => {
      if (!subscription) {
        this.swPush.requestSubscription({
          serverPublicKey: gameConfiguration?.serverConfiguration.pushKey!
        })
        .then(subscription => {
          let pushPath = paths.push;
          this.http.post(pushPath, subscription)
            .subscribe(response => {
              console.log("Successfuly sent subscription to server...")
            })
        })
      }
    });
  }
}
