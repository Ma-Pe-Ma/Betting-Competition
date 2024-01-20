from flask import g
from flask import current_app

from sqlalchemy import text
from typing import Dict, List

from app.db import get_db

# get's user's tournament bet, or create default if it does not exist
def get_tournament_bet_dict_for_user(username : str, language = None) -> dict:
    language = language if language else g.user['language']

    query_string = text("WITH t_bet_with_result AS ("
                        "SELECT tournament_bet.username, COALESCE(tournament_bet.bet, 0) AS bet, tournament_bet.result AS result, tournament_bet.success AS success, tournament_bet.team, "
                        "CASE tournament_bet.result WHEN 0 THEN team.top1 WHEN 1 THEN team.top2 WHEN 2 THEN team.top4 WHEN 3 THEN team.top16 ELSE 0 END AS multiplier "
                        "FROM tournament_bet "
                        "LEFT JOIN team ON team.name = tournament_bet.team "
                        "WHERE username=:username) "
                        
                        ", default_team AS ("
                        "SELECT team.name, tr.translation FROM team LEFT JOIN team_translation AS tr ON tr.name = team.name AND language = :l LIMIT 1"
                        ")"
                        
                        "SELECT bet_user.username, COALESCE(t_bet_with_result.team, default_team.name) AS team, COALESCE(t_bet_with_result.bet, 0) AS bet, "
                        "COALESCE(t_bet_with_result.result, 0) AS result, t_bet_with_result.success AS success, "
                        "COALESCE(tr.translation, default_team.translation) as local_name, "
                        "CASE t_bet_with_result.success WHEN 1 THEN (COALESCE(t_bet_with_result.bet, 0) * (t_bet_with_result.multiplier - 1)) ELSE 0 END AS prize, "
                        "(COALESCE(t_bet_with_result.bet, 0) * (t_bet_with_result.multiplier - 1)) AS expected_prize, "
                        "COALESCE(t_bet_with_result.multiplier, 0) AS multiplier "
                        "FROM bet_user "
                        "LEFT JOIN t_bet_with_result ON t_bet_with_result.username = :username "
                        "LEFT JOIN team ON team.name = t_bet_with_result.team "
                        "LEFT JOIN team_translation AS tr ON tr.name = t_bet_with_result.team AND tr.language = :l "
                        "CROSS JOIN (SELECT * FROM default_team LIMIT 1) AS default_team "
                        "WHERE bet_user.username = :username")

    result = get_db().session.execute(query_string, {'username' : username, 'l' : language})

    return result.fetchone()._asdict()

# get group object which contains both the results and both the user bets (used in every 3 contexts)
def get_group_bet_dict_for_user(username : str, language = None):
    language = language if language else g.user['language']
    
    query_string = text("WITH team_bet_with_group_id AS ( "
                        "SELECT team_bet.team, team.group_id, (team.position = team_bet.position) AS hit, team_bet.position AS bposition, tr.translation AS local_name, team_bet.username "
                        "FROM team_bet "
                        "LEFT JOIN team ON team.name = team_bet.team "
                        "LEFT JOIN team_translation AS tr ON tr.name = team_bet.team AND tr.language = :language "
                        "WHERE team_bet.username = :username "
                        ") "
                        ", group_hit AS ( "
                        "SELECT team.group_id, COALESCE(SUM(team_bet_with_group_id.hit), 0) AS hit_number, COALESCE(group_bet.bet, 0) AS bet, "
                        "CASE SUM(team_bet_with_group_id.hit) WHEN 1 THEN :h1 WHEN 2 THEN :h2 WHEN 4 THEN :h4 ELSE 0 END AS multiplier "
                        "FROM TEAM "
                        "LEFT JOIN team_bet_with_group_id ON team_bet_with_group_id.team = team.name " # AND team_bet_with_group_id.username = :username "
                        "LEFT JOIN group_bet ON group_bet.group_ID = team.group_id AND group_bet.username = :username "
                        "GROUP BY team.group_id "
                        ") "
                        "SELECT team.position, team.top1, team.top2, team.top4, team.top16, team.group_id, tr.translation AS rlocal_name, COALESCE(team_bet_with_group_id.local_name, tr.translation) AS local_name, team_bet_with_group_id.hit, group_hit.hit_number, "
                        "team.name AS rname, team_bet_with_group_id.bposition AS bposition, COALESCE(team_bet_with_group_id.team, team.name) as name, "
                        "group_hit.bet, COALESCE(group_hit.multiplier * group_hit.bet, 0) AS prize, ((group_hit.multiplier - 1) * group_hit.bet) AS credit_diff, group_hit.multiplier "
                        "FROM team "
                        "LEFT JOIN group_hit ON group_hit.group_id=team.group_id "
                        "LEFT JOIN team_translation AS tr ON tr.name = team.name AND tr.language = :language "
                        "LEFT JOIN team_bet_with_group_id ON (team_bet_with_group_id.bposition = team.position) AND team_bet_with_group_id.group_id = team.group_id "#AND team_bet.username = :username "
                        "ORDER BY team_bet_with_group_id.group_id, team_bet_with_group_id.bposition "
                        )

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