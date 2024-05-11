from flask import g
from flask import current_app

from sqlalchemy import text
from typing import Dict, List

from app.tools.db_handler import get_db

# get's user's tournament bet, or create default if it does not exist
def get_tournament_bet_dict_for_user(username : str, language = None) -> dict:
    language = language if language else g.user['language']

    query_string = text("SELECT t_bet.*, "
	                        "CASE t_bet.success WHEN 1 THEN COALESCE(t_bet.bet, 0) * (t_bet.multiplier - 1) ELSE 0 END AS prize, "
	                        "COALESCE(t_bet.bet, 0) * (t_bet.multiplier - 1) AS expected_prize "
                        "FROM bet_user "
                        "LEFT JOIN ("
	                        "SELECT tournament_bet.*, COALESCE(tournament_bet.bet, 0) AS bet, tr.translation AS local_name, "
		                        "CASE tournament_bet.result WHEN 0 THEN team.top1 WHEN 1 THEN team.top2 WHEN 2 THEN team.top4 WHEN 3 THEN team.top16 ELSE 0 END AS multiplier "
	                        "FROM tournament_bet "
	                        "LEFT JOIN team ON team.name = tournament_bet.team "
	                        "LEFT JOIN team_translation AS tr ON tr.name = tournament_bet.team AND tr.language = :l "
                        ") AS t_bet ON t_bet.username = bet_user.username "
                        "WHERE bet_user.username = :username")

    result = get_db().session.execute(query_string, {'username' : username, 'l' : language}).fetchone()

    return result._asdict()

# get group object which contains both the results and both the user bets (used in every 3 contexts)
def get_group_bet_dict_for_user(username : str, language = None):
    language = language if language else g.user['language']
    
    query_string = text("SELECT ts2.*, COALESCE(ts2.multiplier * ts2.bet, 0) AS prize, (ts2.multiplier - 1) * ts2.bet AS credit_diff "
                        "FROM ("
                            "SELECT ts1.*, CASE ts1.hit_number WHEN 1 THEN 1 WHEN 2 THEN 2 WHEN 4 THEN 4 ELSE 0 END AS multiplier "
                            "FROM (SELECT team.*, (team.name = tb.team) AS hit, tr1.translation AS local_name, COALESCE(group_bet.bet, 0) AS bet, "
                                "COALESCE(tb.team, team.name) AS bname, COALESCE(tr2.translation, tr1.translation) AS blocal_name, "
                                "SUM(team.name = tb.team) OVER (PARTITION BY team.group_id) AS hit_number "
                                "FROM team "
                                "LEFT JOIN ( "
                                    "SELECT team_bet.position, team.group_id, team_bet.team "
                                    "FROM team_bet "
                                    "LEFT JOIN team ON team_bet.team = team.name "
                                    "WHERE team_bet.username = :username "
                                ") AS tb ON tb.position = team.position AND tb.group_id = team.group_id "
                                "LEFT JOIN group_bet ON group_bet.group_id = team.group_id AND group_bet.username = :username "
                                "LEFT JOIN team_translation AS tr1 ON tr1.name = team.name AND tr1.language = :language "
                                "LEFT JOIN team_translation AS tr2 ON tr2.name = tb.team AND tr2.language = :language "
                                "ORDER BY team.group_id, team.position "
                            ") AS ts1 "
                        ") AS ts2")

    group_bet_hit_map = current_app.config['GROUP_BET_HIT_MAP']

    result = get_db().session.execute(query_string, {'username' : username, 'language' : language, 'h1' : group_bet_hit_map[1], 'h2' : group_bet_hit_map[2], 'h4' : group_bet_hit_map[4]})
    team_rows = result.fetchall()

    groups = {}
    for team_row in team_rows:
        if team_row.group_id not in groups:
            groups[team_row.group_id] = {'hit_number' : team_row.hit_number, 'bet' : team_row.bet, 'prize' : team_row.prize, 'credit_diff' : team_row.credit_diff, 'teams' : [], 'multiplier' : team_row.multiplier}
        
        team_dict = team_row._asdict()
        del team_dict['hit_number']
        del team_dict['bet']
        del team_dict['prize']
        del team_dict['multiplier']

        groups[team_row.group_id]['teams'].append(team_dict)

    return groups