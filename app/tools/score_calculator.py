from os import name
from app.db import get_db
from flask import g

from datetime import datetime
from dateutil import tz

from app.configuration import configuration
from app.tools import time_determiner
from app.tools.group_calculator import get_group_object

from sqlalchemy import text

# this method returns the sum of group bets and the final bet of a user
def get_group_and_final_bet_amount(username : str) -> int:
    total_bet : int = 0

    # get the final bet
    query_string = text('SELECT bet FROM final_bet WHERE username = :username')
    result = get_db().session.execute(query_string, {'username' : username})
    final_bet = result.fetchone()

    if final_bet is not None:
        total_bet += final_bet.bet
    else:
        return 0

    # get the group bets and add them
    query_string = text('SELECT bet FROM group_bet WHERE username = :username')
    result = get_db().session.execute(query_string, {'username' : username})

    for group_bet in result.fetchall():
        total_bet += group_bet.bet
    
    return total_bet

def get_group_win_amount(group_object) -> int:
    win_amount : int = 0
    
    utc_now = time_determiner.get_now_time_object()
    group_evaluation_time_object = time_determiner.parse_datetime_string(configuration.deadline_times.group_evaluation)

    if utc_now > group_evaluation_time_object:
        for group in group_object:
            win_amount += group.bet_property.multiplier * group.bet_property.amount

    return win_amount

# simple mathematical sign function used by prize result
def sign(x):
    if x > 0:
        return 1
    if x == 0:
        return 0
    if x < 0:
        return -1
   
# get the actual outcome information of a match_bet
def get_bet_result_for_match(match, match_bet) -> dict:
    bet_outcome = sign(match_bet.goal1 - match_bet.goal2)
    match_outcome = None
    odd = 0
    bonus_multiplier = 0

    if match.goal1 is not None:
        # this values tell the result of the match if > 0 then team1 won, if < 0 then team2 won, if = 0 it's draw
        match_outcome = sign(match.goal1 - match.goal2)        
        bonus_multiplier : int = 0
        odd : int = 0

        if match_outcome == bet_outcome:
            if match.goal1 == match.goal2:
                if match.goal1 == match_bet.goal1:
                    bonus_multiplier = configuration.bonus_multipliers.bullseye
            else:
                if match.goal1 == match_bet.goal1 and match.goal2 == match_bet.goal2:
                    bonus_multiplier = configuration.bonus_multipliers.bullseye
                elif match_bet.goal1 - match_bet.goal2 == match.goal1 - match.goal2:
                    bonus_multiplier = configuration.bonus_multipliers.difference

            if match_outcome == 1:
                odd = match.odd1
            elif match_outcome == -1:
                odd = match.odd2
            else:
                odd = match.oddX

    bet_result_dict = {
        'match_outcome' : match_outcome,
        'bet_outcome' : bet_outcome,
        'bet' : match_bet.bet,
        'prize' : match_bet.bet * odd,
        'bonus' : match_bet.bet * bonus_multiplier,
        'goal1' : match_bet.goal1,
        'goal2' : match_bet.goal2
    }

    return bet_result_dict

def get_daily_points_by_current_time(username) -> list:
    days = []

    query_string = text('SELECT * FROM match WHERE unixepoch(time) < unixepoch(\'now\')')
    result = get_db().session.execute(query_string)

    # get matches which has been started by current time
    for match in result.fetchall():
        if match.goal1 is None or match.goal2 is None:
            continue

        match_time_utc = datetime.strptime(match.time, '%Y-%m-%d %H:%M')
        match_time_utc = match_time_utc.replace(tzinfo=tz.gettz('UTC'))

        match_time_local = match_time_utc.astimezone(g.user['tz'])   

        match_date = match_time_local.strftime('%Y-%m-%d')
        match_time = match_time_local.strftime('%H:%M')        

        query_string = text('SELECT * FROM match_bet WHERE (username = :username AND match_id = :match_id)')
        result = get_db().session.execute(query_string, {'username' : username, 'match_id' : match.id})
        match_bet = result.fetchone()

        prize : int = 0
        bet_amount : int = 0

        if match_bet is not None:
            bet_result_for_match = get_bet_result_for_match(match, match_bet)
            prize = bet_result_for_match['prize'] + bet_result_for_match['bonus']
            bet_amount = match_bet.bet
        
        # find match day if it does not exist create it
        match_day : dict = None

        for day in days:
            if day['date'] == match_date:
                match_day = day

        if match_day is None:
            match_day = {'date' : match_date, 'points' :[]}
            days.append(match_day) 

        # add prize and subtract bet
        match_day['points'].append(prize)
        match_day['points'].append(-1 * bet_amount)

    days.sort(key=lambda day : datetime.strptime(day['date'], '%Y-%m-%d'))

    return days

# get player's current balance 
def get_current_points_by_player(username) -> int:
    amount : int = configuration.bet_values.starting_bet_amount
    # substract group and final bet amount
    amount -= get_group_and_final_bet_amount(username)

    # add daily point income (win) + outcome (bet)
    for point_by_day in get_daily_points_by_current_time(username):
        for point in point_by_day['points']:
            amount += point

    group_object = get_group_object(username)
    amount += get_group_win_amount(group_object)

    return amount