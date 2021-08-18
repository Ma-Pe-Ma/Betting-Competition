from datetime import date, datetime, timezone, timedelta
from os import name
from dateutil import tz
from collections import namedtuple
from app.db import get_db

ResultValue = namedtuple("ResultValue", "actual, bet, bonus_multiplier")

# times in UTC
#the start time of the first match
group_deadline_time = "2021-07-25 18:00"
#the day when the last group match is played
group_evaluation_date = "2020-08-02"

local_zone = tz.gettz('Europe/Budapest')

day_names = ["hétfő", "kedd", "szerda", "csütörtök", "péntek", "szombat", "vasárnap"]
bullseye_multiplier = 4
difference_multiplier = 1

starting_bet_amount = 2000
max_group_bet_value = 50

hit_map = [0, 1, 2, 3, 4]

def get_group_bet_amount(user_name):
    total_bet = 0

    final_bet = get_db().execute("SELECT bet FROM final_bet WHERE username = ?", (user_name,)).fetchone()

    if final_bet is not None:
        total_bet += final_bet["bet"]
    else:
        return 0

    for group_bet in get_db().execute("SELECT bet FROM group_bet WHERE username =?", (user_name,)).fetchall():
        total_bet += group_bet["bet"]
    
    return total_bet

def sort_groups(group):
    return group.ID

def sort_teams(team):
    return team.position

def get_group_win_amount(user_name):
    win_amount = 0

    groups = []

    result_teams = get_db().execute("SELECT name, position, group_id FROM team")

    Group = namedtuple("Group", "ID, bet, result_order, bet_order")
    Team = namedtuple("Team", "name, position")

    for team in result_teams:
        group_of_team = None

        for group in groups:
            if group.ID == team["group_id"]:
                group_of_team = group
                break

        team_bet = get_db().execute("SELECT team, position FROM team_bet WHERE username=? AND team=?", (user_name, team["name"])).fetchone()

        if team["position"] is None:
            return None

        if team_bet is None:
            return 0

        if group_of_team == None:
            group_bet = get_db().execute("SELECT bet FROM group_bet WHERE username=? AND group_ID=?",(user_name, team["group_id"])).fetchone()

            group_of_team = Group(ID=team["group_id"], result_order=[], bet_order=[], bet=group_bet["bet"])
            groups.append(group_of_team)

        group_of_team.bet_order.append(Team(name=team_bet["team"], position=team_bet["position"]))
        group_of_team.result_order.append(Team(name=team["name"], position=team["position"]))

    for group in groups:
        group.result_order.sort(key=sort_teams)
        group.bet_order.sort(key=sort_teams)

        multiplier = 0

        for i in range(0,len(group.result_order)):
            if group.result_order[i].name == group.bet_order[i].name:
                multiplier += 1

        win_amount += hit_map[multiplier] * group.bet

    return win_amount

def sorting_date(day):
    return datetime.strptime(day.date, "%Y-%m-%d")

def sorting_time(match):
    return datetime.strptime(match.time, "%H:%M")

def sign(x):
    if x > 0:
        return 1
    if x == 0:
        return 0
    if x < 0:
        return -1

def prize_result(result1, result2, goal1, goal2):
    actual = None
    bet = None
    bonus_multiplier = 0

    actual = sign(result1 - result2)
    bet = sign(goal1 - goal2)

    if actual == bet:
        if result1 == result2:
            if result1 == goal1:
                bonus_multiplier = bullseye_multiplier
        else:
            if goal1 == result1 and goal2 == result2:
                bonus_multiplier = bullseye_multiplier
            elif goal1 - goal2 == result1 - result2:
                bonus_multiplier = difference_multiplier

    return ResultValue(actual=actual, bet=bet, bonus_multiplier=bonus_multiplier)