interface Match {
    date?: string,
    time?: string,
    datetime?: string,
    weekDay?: number,
    team1?: string,
    team2?: string,
    id?: number,
    active?: boolean,
    odd1?: number,
    oddX?: number,
    odd2?: number,
    goal1?: number,
    goal2?: number,
    max_bet?: number,
    bet?: number,
    bgoal1?: number,
    bgoal2?: number,
    bonus?: number,
    prize?: number,
    diff?: number,
    success?: number,
    balance?: number,
    sum_success?: number,
    round?: string
}

interface Day {
    date: string,
    number: number,
    weekday: number,
    matches: Match[]
}