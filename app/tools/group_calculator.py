from collections import namedtuple
from app.tools.ordering import order_teams, order_groups
from app.db import get_db

FinalBet = namedtuple("FinalBet", "team, hun_name, result, betting_amount, success, multiplier")

#Group = namedtuple("Group", "ID, teams, bet")
GroupContainer = namedtuple("GroupContainer", "ID, teams, bets, bet_property")
Team = namedtuple("Team", "name, hun_name, position, top1, top2, top4, top16")
Bet2 = namedtuple("Bet2", "team, hun_name, position")
BetProperty = namedtuple("BetProperty", "amount, win, hit_number, multiplier")

# map used to declare win amount multiplier for group 
hit_map = [0, 0, 2, 0, 4]

# get's user's final bet, or create default if it does not exist
def get_final_bet(user_name):
    final_bet = get_db().execute("SELECT team, bet, result, success FROM final_bet WHERE username = ?", (user_name,)).fetchone()

    if final_bet != None:
        final_team = get_db().execute("SELECT name, hun_name, top1, top2, top4, top16 FROM team WHERE name=?", (final_bet["team"],)).fetchone()
        bet = final_bet["bet"]
        result = final_bet["result"]
        success = final_bet["success"]

        if result == 0:
            multiplier = final_team["top1"]
        if result == 1:
            multiplier = final_team["top2"]
        if result == 2:
            multiplier = final_team["top4"]
        if result == 3:
            multiplier = final_team["top16"]
    else:
        bet = 0
        final_team = get_db().execute("SELECT * FROM team", ()).fetchone()
        result = 0
        success = None
        multiplier = 0

    print("result_ " + str(result))

    return FinalBet(team=final_team["name"], hun_name=final_team["hun_name"], result=result, betting_amount=bet, success=success, multiplier=multiplier)


# get group object which contains both the results and both the user bets (used in every 3 contexts)
def get_group_object(user_name):
    teams = get_db().execute("SELECT name, hun_name, group_id, top1, top2, top4, top16, position FROM team", ()).fetchall()

    group_containers = []

    # create an array of groups which hold the team properties from the team table
    for team in teams:
        group_of_team = None

        bet_property = BetProperty(amount=0, win=0, hit_number=0, multiplier=0)

        for group_container in group_containers:
            if group_container.ID == team["group_id"]:
                group_of_team = group_container
                break

        if group_of_team == None:
            group_of_team = GroupContainer(ID=team["group_id"], teams=[], bets=[], bet_property=bet_property)
            group_containers.append(group_of_team)
        
        group_of_team.teams.append(Team(name=team["name"], hun_name=team["hun_name"], position=team["position"], top1=team["top1"], top2=team["top2"], top4=team["top4"], top16=team["top16"]))

    #order the teams in the groups
    for group in group_containers:
        group.teams.sort(key=order_teams)

    # read out the order for teams from user bets
    user_team_bets = get_db().execute("SELECT team_bet.team, team_bet.position, team.group_id, team.hun_name FROM team_bet INNER JOIN team ON team_bet.team=team.name WHERE username =?", (user_name,)).fetchall()
    if user_team_bets is not None:
        for user_team_bet in user_team_bets:
            for group_container in group_containers:
                if group_container.ID == user_team_bet["group_id"]:
                    group_container.bets.append(Bet2(team=user_team_bet["team"], hun_name=user_team_bet["hun_name"], position=user_team_bet["position"]))
                    break      
        
        for j, group in enumerate(group_containers):
            group.bets.sort(key=order_teams)

            hit_number = 0

            for i, team in enumerate(group.bets):
                if group.teams[i].name == group.bets[i].team:
                    hit_number += 1

            new_bet_property = BetProperty(amount=0, win=0, hit_number=hit_number, multiplier=hit_map[hit_number])

            group_containers[j] = group._replace(bet_property=new_bet_property)

    # read out the group bet and add to existing object
    user_group_bets = get_db().execute("SELECT group_id, bet FROM group_bet WHERE username=?", (user_name,)).fetchall()
    if user_group_bets is not None:
        for i, group_container in enumerate(group_containers):
            for user_group_bet in user_group_bets:
                if user_group_bet["group_id"] == group_container.ID:
                    win_amount = user_group_bet["bet"] * group_container.bet_property.multiplier
                    new_bet_property = BetProperty(amount=user_group_bet["bet"], win=win_amount, hit_number=group_container.bet_property.hit_number, multiplier=group_container.bet_property.multiplier)

                    group_containers[i] = group_container._replace(bet_property=new_bet_property)
                    break

    group_containers.sort(key=order_groups)
    return group_containers