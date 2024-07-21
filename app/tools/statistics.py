from sqlalchemy import text

from app.tools.db_handler import get_db
from app.tools import score_calculator

match_stats = '''
    SELECT matches.id, time_converter(datetime, 'utc', :tz) AS local_datetime, tr1.translation AS team1, tr2.translation AS team2,
        bet_count, diff_by, normalized_diff_by, total_bet, normalized_total_bet, credit_ratio, hit_count, hit_ratio,
        diff_by == max_diff AS max_flag,
        diff_by == min_diff AS min_flag,
        normalized_diff_by == normalized_max_diff AS normalized_max_flag,
        normalized_diff_by == normalized_min_diff AS normalized_min_flag,
        total_bet == max_total_bet AS total_max_flag,
        total_bet == min_total_bet AS total_min_flag,
        normalized_total_bet == normalized_max_total_bet AS normalized_total_max_flag,
        normalized_total_bet == normalized_min_total_bet AS normalized_total_min_flag,
        credit_ratio == max_credit_ratio AS credit_ratio_max_flag,
        credit_ratio == min_credit_ratio AS credit_ratio_min_flag,
        hit_count == max_hit_count AS max_hit_count_flag,
        hit_count == min_hit_count AS min_hit_count_flag,
        hit_ratio == max_hit_ratio AS max_hit_ratio_flag,
        hit_ratio == min_hit_ratio AS min_hit_ratio_flag
    FROM (SELECT *,
            MAX(diff_by) OVER (PARTITION BY 1) AS max_diff,
            MIN(diff_by) OVER (PARTITION BY 1) AS min_diff,
            MAX(normalized_diff_by) OVER (PARTITION BY 1) AS normalized_max_diff,
            MIN(normalized_diff_by) OVER (PARTITION BY 1) AS normalized_min_diff,
            MAX(total_bet) OVER (PARTITION BY 1) AS max_total_bet,
            MIN(total_bet) OVER (PARTITION BY 1) AS min_total_bet,
            MAX(normalized_total_bet) OVER (PARTITION BY 1) AS normalized_max_total_bet,
            MIN(normalized_total_bet) OVER (PARTITION BY 1) AS normalized_min_total_bet,
            MAX(credit_ratio) OVER (PARTITION BY 1) AS max_credit_ratio,
            MIN(credit_ratio) OVER (PARTITION BY 1) AS min_credit_ratio,
            MAX(hit_count) OVER (PARTITION BY 1) AS max_hit_count,
            MIN(hit_count) OVER (PARTITION BY 1) AS min_hit_count,
            MAX(hit_ratio) OVER (PARTITION BY 1) AS max_hit_ratio,
            MIN(hit_ratio) OVER (PARTITION BY 1) AS min_hit_ratio
        FROM (SELECT *,
                SUM(diff) AS diff_by,
                SUM(diff) * :default_max_bet_per_match / max_bet AS normalized_diff_by,
                SUM(bet) AS total_bet,
                SUM(bet) * :default_max_bet_per_match / max_bet AS normalized_total_bet,
                SUM(COALESCE(bet_outcome IS NOT NULL, 0)) AS bet_count,
                SUM(bet_outcome == match_outcome) AS hit_count,
                100 * CAST(SUM(bet_outcome == match_outcome) AS FLOAT) / SUM(COALESCE(bet_outcome IS NOT NULL, 0)) AS hit_ratio,
                CAST(100 * SUM(diff) AS FLOAT) / SUM(bet) AS credit_ratio
            FROM (SELECT *,
                        (COALESCE(multiplier, 0) + COALESCE(bonus, 0) - 1) * COALESCE(bet, 0) AS diff
                    FROM results )
            GROUP BY {group}
        )
    ) AS matches
    LEFT JOIN team_translation AS tr1 ON tr1.name = team1 AND tr1.language = :l
    LEFT JOIN team_translation AS tr2 ON tr2.name = team2 AND tr2.language = :l'''

streak_stats = '''SELECT *,
	MAX(win_streak_length) AS max_win_streak_length,
	MAX(loose_streak_length) AS max_loose_streak_length,
	MAX(bonus_streak_length) AS max_bonus_streak_length
FROM (
	SELECT *,
		COUNT(win_streak_no) OVER (PARTITION BY username, win_streak_no ORDER BY datetime ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS win_streak_length,
		COUNT(loose_streak_no) OVER (PARTITION BY username, loose_streak_no ORDER BY datetime ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS loose_streak_length,
		COUNT(bonus_streak_no) OVER (PARTITION BY username, bonus_streak_no ORDER BY datetime ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS bonus_streak_length
	FROM (
		SELECT *,
			CASE WHEN success THEN SUM(new_streak == 1) OVER (PARTITION BY username ORDER BY datetime ROWS BETWEEN UNBOUNDED PRECEDING  AND CURRENT ROW) ELSE NULL END AS win_streak_no,
			CASE WHEN NOT success THEN SUM(new_streak == 2) OVER (PARTITION BY username ORDER BY datetime ROWS BETWEEN UNBOUNDED PRECEDING  AND CURRENT ROW) ELSE NULL END AS loose_streak_no,
			CASE WHEN bonus = :bullseye THEN SUM(bonus_streak == 1) OVER (PARTITION BY username ORDER BY datetime ROWS BETWEEN UNBOUNDED PRECEDING  AND CURRENT ROW) ELSE NULL END AS bonus_streak_no,
			(100 * CAST(hit_count as float) / bet_count) AS success_ratio,
            (100 * CAST(bullseye_count as float) / bet_count) AS bullseye_ratio
		FROM (SELECT *,
				(COALESCE(multiplier, 0) + COALESCE(bonus, 0) - 1) * COALESCE(bet, 0) AS diff,
				CASE WHEN COALESCE(LAG(COALESCE(results.success, 0)) OVER (PARTITION BY username) != COALESCE(results.success, 0), 1)
					THEN CASE WHEN results.success THEN 1 ELSE 2 END
					ELSE 0 
				END AS new_streak,
				CASE WHEN LAG(COALESCE(results.bonus, 0)) OVER (PARTITION BY username) != COALESCE(results.bonus, 0) AND results.bonus = :bullseye
						THEN 1
						ELSE 0
				END AS bonus_streak,
				SUM(results.bonus == :bullseye) OVER (PARTITION BY username ORDER BY username ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS bullseye_count,
				SUM(COALESCE(results.success, 0)) OVER (PARTITION BY username ORDER BY username ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS hit_count,
				SUM(COALESCE(results.bet_outcome IS NOT NULL, 0)) OVER (PARTITION BY username ORDER BY username ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS bet_count
			FROM results
		)
	)
	ORDER BY username, id
)
GROUP BY username
ORDER BY UPPER(username)
'''

def get_statistics(language, tz):
    parameters = {'bullseye' : 4.0, 'difference' : 1.0, 'default_max_bet_per_match' : 50, 'l' : language, 'tz' : tz}

    streak_query = 'WITH results AS (' + score_calculator.match_evaluation_query_string + '), streaks AS (' + streak_stats + ')' + '''
        SELECT username, bullseye_count, hit_count, bet_count, success_ratio, bullseye_ratio, max_win_streak_length, max_loose_streak_length, max_bonus_streak_length,
        max_win_streak_length = (SELECT MAX(max_win_streak_length) FROM streaks) AS max_win_streak_global,
        max_loose_streak_length = (SELECT MAX(max_loose_streak_length) FROM streaks) AS max_loose_streak_global,
        max_bonus_streak_length = (SELECT MAX(max_bonus_streak_length) FROM streaks) AS max_bonus_streak_global,
        bullseye_count = (SELECT MAX(bullseye_count) FROM streaks) AS bullseye_count_global,
        hit_count = (SELECT MAX(hit_count) FROM streaks) AS hit_count_global,
        success_ratio = (SELECT MAX(success_ratio) FROM streaks) AS success_ratio_global,
        bullseye_ratio = (SELECT MAX(bullseye_ratio) FROM streaks) AS bullseye_ratio_global,
        (SELECT SUM(bet_count) FROM (SELECT streaks.bet_count FROM streaks GROUP BY username)) AS total_bet_count,
        (SELECT SUM(hit_count) FROM (SELECT streaks.hit_count FROM streaks GROUP BY username)) AS total_hit_count,
        (SELECT SUM(bullseye_count) FROM (SELECT streaks.bullseye_count FROM streaks GROUP BY username)) AS total_bullseye_count	
    FROM streaks;
    '''

    streak_query = text(streak_query)
    streak_result = get_db().session.execute(streak_query, parameters)

    match_query = 'WITH results AS (' + score_calculator.match_evaluation_query_string + ')' + match_stats.format(group='id') 
    match_query = text(match_query)
    match_result = get_db().session.execute(match_query, parameters)

    return {'players' : [streak._asdict() for streak in streak_result.fetchall()], 'matches' : [match._asdict() for match in match_result.fetchall()]}
