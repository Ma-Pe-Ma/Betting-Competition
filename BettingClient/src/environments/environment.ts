import { B } from "@angular/cdk/keycodes";

export const environment = {
    serverAddress: 'http://localhost:5000/',
    locations : {
        gameConfiguration: 'game-configuration',
        auth: {
            forgottenPassword: 'forgotten-password',
            resetPassword: 'reset-password',
            register: 'register',
            signIn: 'sign-in',
            signOut: 'sign-out',
            status: 'status',
            registerMessage: 'register-message',
            profile: {
                get: 'profile-get',
                set: 'profile-set'
            }
        },
        main: {
            matches: 'matches',
            credit: 'credit',
            statistics: 'statistics'
        },        
        match: 'match',
        results: {
            playerNames: 'players',
            dates: 'dates',
            playerResults: 'results/user',
            dateResults: 'results/match'
        },
        standings: 'standings',
        group: {
            get: 'group-status',
            set: 'group-bet',
            tournament: 'tournament-bet'
        },
        chat: {
            get: 'chat',
            set: 'chat-add'
        },
        admin: {
            match: {
                list: 'admin/matches',
                get: 'admin/match-get',
                set: 'admin/match-set',
                update: 'admin/match-update'
            },
            group: {
                get: 'admin/group-get',
                set: 'admin/group-set'
            },
            tournamentBet: {
                get: 'admin/tournament-bet-get',
                set: 'admin/tournament-bet-set'
            },
            homeMessage: {
                get: '/admin/message-get',
                set: '/admin/message-set'
            },
            sendNotification: '/admin/send-notification',
            standings:{
                get: '/admin/standings',
                sendImmediately: '/admin/standings-notification',                
            },
            resetKeys: '/admin/reset-keys',
            maintenance: {
                dbUpload: '/admin/database'
            },
            teamData: '/admin/team-data'
        },
        push: '/notification/subscribe'
    },
    useMockTime: false,
    mockTime: ''
};
