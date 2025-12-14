import { ApplicationConfig, inject, provideBrowserGlobalErrorListeners, provideZoneChangeDetection, provideAppInitializer, isDevMode } from '@angular/core';
import { provideServiceWorker } from '@angular/service-worker';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { firstValueFrom, forkJoin } from 'rxjs';

import { routes } from './app.routes';
import { authCheckerInterceptor } from './authentication/auth-checker-interceptor';
import { ClientConfigService } from './service/client-config-service';
import { GameConfigurationService } from './service/game-configuration-service';
import { AuthService } from './service/auth-service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideAppInitializer(async () => {
      const clientConfig = inject(ClientConfigService);
      const authService = inject(AuthService);
      const gameConfig = inject(GameConfigurationService);

      await firstValueFrom(clientConfig.loadConfig());      
      await firstValueFrom(
        forkJoin([
          authService.fetchAuthStatus(),
          gameConfig.fetchGameData()
        ])
      );
    }),
    provideBrowserGlobalErrorListeners(),
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authCheckerInterceptor])),
    provideServiceWorker('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerWhenStable:30000'
    })
  ]
};
