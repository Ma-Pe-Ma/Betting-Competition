import { Routes } from '@angular/router';
import { authGuard } from './service/auth-guard';

export const routes: Routes = [
    {
        path: '',
        loadComponent: () => import('./game/game').then(m => m.Game),
        loadChildren: ()=> import('./game/game.routes').then(m => m.routes),
        canActivate: [authGuard],
        canActivateChild: [authGuard],
        data: { role: 0}

    },
    {
        path: 'auth',
        loadComponent: () => import('./authentication/authentication').then(m => m.Authentication),
        loadChildren: () => import('./authentication/authentication.routes').then(m => m.routes),
        canActivate: [authGuard],
        canActivateChild: [authGuard],
        data: { role: null}
    },
    {
        path: '**', 
        redirectTo: '/',
        pathMatch: 'full'
    }
];
