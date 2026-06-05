import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DecimalPipe } from '@angular/common';
import { LocalDatePipe } from '../../../pipes/local-date-pipe';
import { AuthService } from '../../../service/auth-service';
import { paths } from '../../../paths';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';

interface PlayerStatistics {
  username?: string,
  bullseye_count?: number,
  hit_count?: number,
  bet_count?: number,
  success_ratio?: number,
  bullseye_ratio?: number,
  max_win_streak_length?: number,
  max_loose_streak_length?: number,
  max_bonus_streak_length?: number,
  max_win_streak_global?: number,
  max_loose_streak_global?: number,
  max_bonus_streak_global?: number,
  bullseye_count_global?: number,
  hit_count_global?: number,
  success_ratio_global?: number,
  bullseye_ratio_global?: number,
  total_bet_count?: number,
  total_hit_count?: number,
  total_bullseye_count?: number
}

interface MatchStatistics {
  id?: number
  datetime?: string
  team1?: string
  team2?: string
  bet_count?: number
  diff_by?: number
  normalized_diff_by?: number
  total_bet?: number
  normalized_total_bet?: number
  credit_ratio?: number
  hit_count?: number
  hit_ratio?: number
  max_flag?: number
  min_flag?: number
  normalized_max_flag?: number
  normalized_min_flag?: number
  total_max_flag?: number
  total_min_flag?: number
  normalized_total_max_flag?: number
  normalized_total_min_flag?: number
  credit_ratio_max_flag?: number
  credit_ratio_min_flag?: number
  max_hit_count_flag?: number
  min_hit_count_flag?: number
  max_hit_ratio_flag?: number
  min_hit_ratio_flag?: number
}

@Component({
  selector: 'app-statistics',
  imports: [DecimalPipe, LocalDatePipe, CommonModule],
  templateUrl: './statistics.html'
})
export class Statistics {
  alerts: Alert[] = []
  user: User;

  playerStatistics: PlayerStatistics[] = [];
  matchStatistics: MatchStatistics [] = [];

  constructor(private http: HttpClient, private authService: AuthService) {
    let path = paths.main.statistics;
    this.user = this.authService.getUser();
   
    type DashboardData = {
      players: PlayerStatistics[];
      matches: MatchStatistics[];
    };

    http.get<DashboardData>(path)
      .subscribe({
        next: (value: DashboardData) => {
          this.playerStatistics = value.players;        
          this.matchStatistics = value.matches;
        },
        error: (err: HttpErrorResponse) => {
          this.alerts.push({type: 'danger', message: err.error});
        }
      });
  }
}
