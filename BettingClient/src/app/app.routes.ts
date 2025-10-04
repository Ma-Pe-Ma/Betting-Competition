import { Routes } from '@angular/router';
import { Game } from './game/game';

export const routes: Routes = [
    {
        path: '',
        component: Game
        //loadChildren: () => import('./game/game').then(m => m.Game)
    },
    {
        path: 'auth',
        loadChildren: () => import('./authentication/authentication').then(m => m.Authentication)
    }    
];
