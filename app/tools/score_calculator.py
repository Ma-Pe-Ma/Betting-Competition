from os import name
from app.db import get_db
from flask import g

from datetime import datetime
from dateutil import tz

from app.configuration import configuration
from app.tools import time_determiner
from app.tools.group_calculator import get_group_object_for_user

from sqlalchemy import text

from typing import Dict, List

# this method returns the sum of group bets and the final bet of a user
def get_group_and_final_bet_amount(username : str) -> int:
    query_string = text("SELECT (SUM(group_bet.bet) + final_bet.bet) AS total_bet "
                        "FROM group_bet "
                        "LEFT JOIN final_bet ON final_bet.username = :username "
                        "WHERE group_bet.username = :username "
                        "GROUP BY group_bet.username")
    result = get_db().session.execute(query_string, {'username' : username})

    return result.fetchone()._asdict()['total_bet']

def get_group_win_amount(group_object) -> int:
    win_amount : int = 0
    
    utc_now = time_determiner.get_now_time_object()
    group_evaluation_time_object = time_determiner.parse_datetime_string(configuration.deadline_times.group_evaluation)

    if utc_now > group_evaluation_time_object:
        for group in group_object:
            win_amount += group.bet_property.multiplier * group.bet_property.amount

    return win_amount

# simple mathematical sign function used by prize result
def sign(x : int|float) -> int:
    if x > 0:
        return 1
    if x == 0:
        return 0
    if x < 0:
        return -1

# TODO eliminate this ugly method with proper SQL query!
def get_bet_result_for_match(mb_parameters):
    if mb_parameters['rgoal1'] is None or mb_parameters['rgoal2'] is None:
        mb_parameters['match_outcome'] = None
    else:
        mb_parameters['match_outcome'] = sign(mb_parameters['rgoal1'] - mb_parameters['rgoal2'])

    if mb_parameters['bgoal1'] is None or mb_parameters['bgoal2'] is None:
        mb_parameters['bet_outcome'] = None
    else:
        mb_parameters['bet_outcome'] = sign(mb_parameters['bgoal1'] - mb_parameters['bgoal2'])

    bonus_multiplier : int = 0
    odd : int = 0

    if mb_parameters['match_outcome'] is not None and mb_parameters['bet_outcome'] is not None:
        if mb_parameters['match_outcome'] == mb_parameters['bet_outcome']:
            if mb_parameters['rgoal1'] == mb_parameters['rgoal2']:
                if mb_parameters['rgoal1'] == mb_parameters['bgoal1']:
                    bonus_multiplier = configuration.bonus_multipliers.bullseye
            else:
                if mb_parameters['rgoal1'] == mb_parameters['bgoal1'] and mb_parameters['rgoal2'] == mb_parameters['bgoal2']:
                    bonus_multiplier = configuration.bonus_multipliers.bullseye
                elif mb_parameters['bgoal1'] - mb_parameters['bgoal2'] == mb_parameters['rgoal1'] - mb_parameters['rgoal2']:
                    bonus_multiplier = configuration.bonus_multipliers.difference

            if mb_parameters['match_outcome'] == 1:
                odd = mb_parameters['odd1']
            elif mb_parameters['match_outcome'] == -1:
                odd = mb_parameters['odd2']
            else:
                odd = mb_parameters['oddX']

    mb_parameters['bonus'] = mb_parameters['bet'] * bonus_multiplier
    mb_parameters['prize'] = mb_parameters['bet'] * odd

def get_daily_points_by_current_time(username : str) -> List[Dict[str, str|List[int]]]:
    utc_now_string : str = time_determiner.get_now_time_string()

    query_string = text("SELECT match.goal1 AS rgoal1, match.goal2 AS rgoal2, match_bet.goal1 AS bgoal1, match_bet.goal2 AS bgoal2, COALESCE(match_bet.bet, 0) AS bet, "
                        "date(match.time || :timezone) AS date, time(match.time || :timezone) AS time "
                        "FROM match "
                        "LEFT JOIN match_bet ON match_bet.match_id = match.id AND match_bet.username = :u "
                        "WHERE unixepoch(time) < unixepoch(:now) "
                        "ORDER BY date")
    result = get_db().session.execute(query_string, {'now' : utc_now_string, 'u' : username, 'timezone' : g.user['tz_offset'] })

    days : Dict[str, List[int]] = {}

    # get matches which has been started by current time
    for match_and_bet_parameters in result.fetchall():
        if match_and_bet_parameters.rgoal1 is None or match_and_bet_parameters.rgoal2 is None:
            continue

        match_bet_dict = match_and_bet_parameters._asdict()
        get_bet_result_for_match(match_bet_dict)

        credit_change = match_bet_dict['prize'] + match_bet_dict['bonus'] - match_bet_dict['bet']

        if match_and_bet_parameters['date'] not in days:
            days[match_and_bet_parameters['date']] = [credit_change]
        else:
            days[match_and_bet_parameters['date']].append(credit_change)

    return days

# get player's current balance 
def get_current_points_by_player(username) -> int:
    amount : int = configuration.bet_values.starting_bet_amount
    # substract group and final bet amount
    amount -= get_group_and_final_bet_amount(username)

    point_by_day : Dict[str, str|List[int]]

    # add daily point income (win) + outcome (bet)
    for point_by_day in get_daily_points_by_current_time(username):
        for point in point_by_day['points']:
            amount += point

    group_object = get_group_object_for_user(username)
    amount += get_group_win_amount(group_object)

    return amount