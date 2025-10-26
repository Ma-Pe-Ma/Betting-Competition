interface Group {
    bet: number
    credit_diff: number
    hit_number: number
    id: string
    multiplier: number
    prize: number
    teams: Team[]
}

interface Team {
    name: string
    name_tr: string
    bet_name: string
    bet_name_tr: string
    hit: number
    position: number
}