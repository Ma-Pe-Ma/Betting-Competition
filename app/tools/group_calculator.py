from flask import g
from sqlalchemy import text

from app.db import get_db
from app.configuration import configuration

# get's user's final bet, or create default if it does not exist
def get_tournament_bet(username : str, language : str) -> dict:
    query_string = text('SELECT team, bet, result, success FROM final_bet WHERE username=:username')
    result = get_db().session.execute(query_string, {'username' : username})
    final_bet = result.fetchone()

    if final_bet is not None:
        query_string = text('SELECT name, top1, top2, top4, top16 FROM team WHERE name=:teamname')
        result = get_db().session.execute(query_string, {'teamname' : final_bet.team})
        final_team = result.fetchone()

        bet = final_bet.bet
        result = final_bet.result
        success = None if final_bet.success == '' else final_bet.success

        if result == 0:
            multiplier = final_team.top1
        if result == 1:
            multiplier = final_team.top2
        if result == 2:
            multiplier = final_team.top4
        if result == 3:
            multiplier = final_team.top16
    else:
        bet : int = 0
        query_string = text('SELECT * FROM team')
        result = get_db().session.execute(query_string)
        final_team = result.fetchone()
        result = 0
        success = None
        multiplier = 0    

    query_string = text('SELECT translation FROM team_translation WHERE name=:name AND language=:language')
    result = get_db().session.execute(query_string, {'name' : final_team.name, 'language' : language})
    local_name = result.fetchone()

    return {'team' : final_team.name, 'local_name' : local_name.translation, 'result' : result, 'betting_amount' : bet, 'success' : success, 'multiplier' : multiplier}

# get group object which contains both the results and both the user bets (used in every 3 contexts)
def get_group_object(username : str):
    query_string = text('SELECT name, group_id, top1, top2, top4, top16, position FROM team')
    result0 = get_db().session.execute(query_string)
    teams = result0.fetchall()

    group_containers = []

    # create an array of groups which hold the team properties from the team table
    for team in teams:
        group_of_team = None

        bet_property = {'amount' : 0, 'win' : 0, 'hit_number' : 0, 'multiplier' : 0}

        for group_container in group_containers:
            if group_container['ID'] == team.group_id:
                group_of_team = group_container
                break

        if group_of_team == None:
            group_of_team = {'ID' : team.group_id, 'teams' : [], 'bets' : [], 'bet_property' : bet_property}
            group_containers.append(group_of_team)
        
        query_string = text('SELECT translation FROM team_translation WHERE name=:teamname AND language=:language')
        result1 = get_db().session.execute(query_string, {'teamname' : team.name, 'language' : g.user['language']})
        local_name = result1.fetchone()

        team_dict : dict = team._asdict()
        team_dict['local_name'] = local_name.translation

        group_of_team['teams'].append(team_dict)

    #order the teams in the groups
    for group_container in group_containers:
        group_container['teams'].sort(key=lambda team : team['position'])

    # read out the order for teams from user bets
    query_string = text('SELECT team_bet.team, team_bet.position, team.group_id FROM team_bet INNER JOIN team ON team_bet.team=team.name WHERE username=:username')
    result0 = get_db().session.execute(query_string, {'username' : username})
    
    for user_team_bet in result0.fetchall():
        for group_container in group_containers:
            if group_container['ID'] == user_team_bet.group_id:
                query_string = text('SELECT translation FROM team_translation WHERE name=:team AND language=:language')
                result1 = get_db().session.execute(query_string, {'team' : user_team_bet.team, 'language' :  g.user['language']})
                local_name = result1.fetchone()

                group_container['bets'].append({'team' : user_team_bet.team, 'local_name' : local_name.translation, 'position' : user_team_bet.position})
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