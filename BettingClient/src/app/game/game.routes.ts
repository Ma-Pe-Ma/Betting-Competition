import { Routes } from '@angular/router';

export const routes: Routes = [
    {
        path: '',
        loadComponent: () => import('./main/main').then(m => m.Main),
        title: $localize`:betting:Betting`,
        canActivate: [() => import('../service/auth-guard').then(m => m.authGuard)],
        canActivateChild: [() => import('../service/auth-guard').then(m => m.authGuard)],
        data: { role: 0 }
    },
    {
        path: 'results',
        loadComponent: () => import('./results/results').then(m => m.Results),
        title: $localize`:results:Results`,
        canActivate: [() => import('../service/auth-guard').then(m => m.authGuard)],
        canActivateChild: [() => import('../service/auth-guard').then(m => m.authGuard)],
        data: { role: 0 }
    },
    {
        path: 'standings',
        loadComponent: () => import('./standings/standings').then(m => m.Standings),
        title: $localize`:standings:Standings`,
        canActivate: [() => import('../service/auth-guard').then(m => m.authGuard)],
        canActivateChild: [() => import('../service/auth-guard').then(m => m.authGuard)],
        data: { role: 0 }
    },
    {
        path: 'group-bet',
        loadComponent: () => import('./group-bet/group-bet').then(m => m.GroupBet),
        title: $localize`:group_bet:Group bet`,
        canActivate: [() => import('../service/auth-guard').then(m => m.authGuard)],
        canActivateChild: [() => import('../service/auth-guard').then(m => m.authGuard)],
        data: { role: 0 }
    },
    {
        path: 'chat',
        loadComponent: () => import('./chat/chat').then(m => m.Chat),
        title: $localize`:chat:Chat`,
        canActivate: [() => import('../service/auth-guard').then(m => m.authGuard)],
        canActivateChild: [() => import('../service/auth-guard').then(m => m.authGuard)],
        data: { role: 0 }
    },
    {
        path: 'admin',
        loadComponent: () => import('./admin/admin').then(m => m.Admin),
        title: $localize`:admin:Admin`,
        canActivate: [() => import('../service/auth-guard').then(m => m.authGuard)],
        canActivateChild: [() => import('../service/auth-guard').then(m => m.authGuard)],
        data: { role: 1 }
    },
    {
        path: 'profile',
        loadComponent: () => import('./profile/profile').then(m => m.Profile),
        title: $localize`:betting:Profile`,
        canActivate: [() => import('../service/auth-guard').then(m => m.authGuard)],
        data: { role: 0 }
    },
    {
        path: 'sign-out',
        loadComponent: () => import('./sign-out/sign-out').then(m => m.SignOut),
        title: $localize`:betting:Sign-out`,
        canActivate: [() => import('../service/auth-guard').then(m => m.authGuard)],
        data: { role: 0 }
    }
];
