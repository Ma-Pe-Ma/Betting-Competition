from flask import g
from sqlalchemy import text
from typing import Dict, List

from app.db import get_db
from app.configuration import configuration

# get's user's final bet, or create default if it does not exist
def get_tournament_bet(username : str, language = None) -> dict:
    if language is None:
        language = g.user['language']

    query_string = text("WITH prize_enum AS ("
                        "SELECT final_bet.username, "
                        "CASE final_bet.result WHEN 0 THEN team.top1 WHEN 1 THEN team.top2 WHEN 2 THEN team.top4 WHEN 3 THEN team.top16 ELSE 1 END AS multiplier "
                        "FROM final_bet "
                        "LEFT JOIN team ON team.name = final_bet.team "
                        "WHERE username=:username) "

                        "SELECT final_bet.team, COALESCE(final_bet.bet, 0) AS bet, final_bet.result, final_bet.success, tr.translation AS local_name, "
                        "CASE final_bet.success WHEN 1 THEN (bet * (prize_enum.multiplier - 1)) ELSE 0 END AS prize, prize_enum.multiplier "
                        "FROM final_bet "
                        "LEFT JOIN prize_enum ON prize_enum.username = :username "
                        "LEFT JOIN team ON team.name = final_bet.team "
                        "LEFT JOIN team_translation AS tr ON tr.name = final_bet.team AND tr.language = :l "
                        "WHERE final_bet.username=:username")
    result = get_db().session.execute(query_string, {'username' : username, 'l' : language})

    return result.fetchone()._asdict()

# TODO rewrite this ugly method with proper SQL query!
# get group object which contains both the results and both the user bets (used in every 3 contexts)
def get_group_object_for_user(username : str, language = None):
    if language is None:
        language = g.user['language']

    query_string = text("SELECT team.*, tr.translation AS local_name "
                        "FROM team "
                        "INNER JOIN team_translation AS tr ON tr.name = team.name "
                        "ORDER BY team.group_id, team.position")
    result0 = get_db().session.execute(query_string)
    teams = result0.fetchall()

    group_containers = []
    groups = {}

    # create an array of groups which hold the team properties from the team table
    for team in teams:
        group_of_team = None

        bet_property : Dict[str, int] = {'amount' : 0, 'win' : 0, 'hit_number' : 0, 'multiplier' : 0}

        for group_container in group_containers:
            if group_container['ID'] == team.group_id:
                group_of_team = group_container
                break

        if group_of_team == None:
            group_of_team = {'ID' : team.group_id, 'teams' : [], 'bets' : [], 'bet_result' : bet_property}
            group_containers.append(group_of_team)

        group_of_team['teams'].append(team._asdict())

    #order the teams in the groups
    for group_container in group_containers:
        group_container['teams'].sort(key=lambda team : team['position'])

    # read out the order for teams from user bets
    query_string = text("SELECT team_bet.team, team_bet.position, team.group_id, tr.translation AS local_name "
                        "FROM team_bet " 
                        "INNER JOIN team ON team_bet.team=team.name "
                        "LEFT JOIN team_translation AS tr ON tr.name = team_bet.team AND tr.language = :language "
                        "WHERE username=:username")
    result = get_db().session.execute(query_string, {'username' : username, 'language' : language})
    
    for user_team_bet in result.fetchall():
        for group_container in group_containers:
            if group_container['ID'] == user_team_bet.group_id:
                group_container['bets'].append(user_team_bet._asdict())
                break      
    
    for j, group_container in enumerate(group_containers):
        group_container['bets'].sort(key=lambda team : team['position'])

        hit_number = 0

        for i, team in enumerate(group_container['bets']):
            if group_container['teams'][i]['name'] == group_container['bets'][i]['team']:
                hit_number += 1

        group_container['bet_property'] = {'amount' : 0, 'win' : 0, 'hit_number' : hit_number, 'multiplier' : configuration.group_bet_hit_map[hit_number]}

    # read out the group bet and add to existing object
    query_string = text('SELECT group_id, bet FROM group_bet WHERE username=:username')
    result0 = get_db().session.execute(query_string, {'username' : username})
    user_group_bets = result0.fetchall()
    if user_group_bets is not None:
        for i, group_container in enumerate(group_containers):
            for user_group_bet in user_group_bets:
                if user_group_bet.group_ID == group_container['ID']:
                    win_amount = user_group_bet.bet * group_container['bet_property']['multiplier']
                    group_container['bet_property'] = {'amount' : user_group_bet.bet, 'win' : win_amount, 'hit_number' : group_container['bet_property']['hit_number'], 'multiplier' : group_container['bet_property']['multiplier']}
                    break

    group_containers.sort(key=lambda group : group['ID'])
    return group_containers