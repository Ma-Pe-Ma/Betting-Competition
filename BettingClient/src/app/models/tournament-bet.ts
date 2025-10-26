interface TournamentBet {
  bet: number,
  expected_prize: number
  local_name: string
  multiplier: number
  prize: number
  result: number
  success: number
  team: string
  username: string
}

interface TournamentOdds {
  team: string
  team_tr: string
  odds: number[]
}