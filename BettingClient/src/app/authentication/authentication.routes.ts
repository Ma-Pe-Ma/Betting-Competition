import { Routes } from '@angular/router';

export const routes: Routes = [
    {
        path: 'sign-in',
        loadComponent: () => import('./sign-in/sign-in').then(m => m.SignIn),
        title: $localize`:@@signIn:Sign in`
    },
    {
        path: 'register',
        loadComponent: () => import('./register/register').then(m => m.Register),
        title: $localize`:@@register:Register`
    },
    {
        path: 'forgotten-password',
        loadComponent: () => import('./forgotten-password/forgotten-password').then(m => m.ForgottenPassword),
        title: $localize`:@@forgottenPassword:Forgotten password`
    },
    {
        path: 'reset-password',
        loadComponent: () => import('./reset-password/reset-password').then(m => m.ResetPassword),
        title: $localize`:@@resetPassword:Reset password`
    },
]