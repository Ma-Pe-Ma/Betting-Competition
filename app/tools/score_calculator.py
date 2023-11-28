from os import name
from collections import namedtuple
from app.db import get_db

from datetime import datetime, timezone
from dateutil import tz

from app.configuration import configuration
from app.tools.group_calculator import get_group_object

DayPrefab = namedtuple('DayPrefab', 'date, points')
ResultValue = namedtuple('ResultValue', 'actual, bet, bonus_multiplier')

# multiplier when the user guessed the correct result
bullseye_multiplier = 4

# multiplier when the user guessed the correct goal difference but not the correct result (draw does not count)
difference_multiplier = 1

# this method returns the sum of group bets and the final bet of a user
def get_group_and_final_bet_amount(user_name):
    total_bet = 0

    # get the final bet
    cursor = get_db().cursor()
    cursor.execute('SELECT bet FROM final_bet WHERE username = %s', (user_name,))
    final_bet = cursor.fetchone()

    if final_bet is not None:
        total_bet += final_bet['bet']
    else:
        return 0

    # get the group bets and add them
    cursor1 = get_db().cursor()
    cursor1.execute('SELECT bet FROM group_bet WHERE username = %s', (user_name,))

    for group_bet in cursor1.fetchall():
        total_bet += group_bet['bet']
    
    return total_bet

def get_group_win_amount2(group_object):
    win_amount = 0
    
    for group in group_object:
        win_amount += group.bet_property.multiplier * group.bet_property.amount

    return win_amount

# this method returns how much credit the user has won from (only!) the group betting
def get_group_win_amount(user_name):
    win_amount = 0

    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))

    group_evaluation_time_object = datetime.strptime(configuration.deadline_times.group_evaluation, '%Y-%m-%d %H:%M')
    group_evaluation_time_object = group_evaluation_time_object.replace(tzinfo=tz.gettz('UTC'))

    if utc_now > group_evaluation_time_object:
        for group in get_group_object(user_name=user_name):
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

# method to determine result and bonus
def prize_result(result1, result2, goal1, goal2):
    actual = None
    bet = None
    bonus_multiplier = 0

    # this values tell the result of the match if >0 then team1 won, if <0 then team2 won, if =0 it's draw
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

# get the actual prize from the match
def get_match_prize(match, match_bet):
    prize = 0

    result1 = match['goal1']
    result2 = match['goal2']

    odd1 = match['odd1']
    oddX = match['oddx']
    odd2 = match["odd2"]

    goal1 = match_bet['goal1']
    goal2 = match_bet['goal2']
    bet = match_bet['bet']

    if result1 is not None :
        result_value = prize_result(result1, result2, goal1, goal2)

        if result_value.actual == result_value.bet:
            if result_value.actual == 1:
                prize = bet * odd1
            elif result_value.actual == -1:
                prize = bet * odd2
            else:
                prize = bet * oddX
            
            prize += bet * result_value.bonus_multiplier
    else:
        pass
        #prize = None

    return prize

def get_daily_points_by_current_time(user_name):
    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))
    local_zone =  tz.gettz(configuration.local_zone)

    day_prefabs = []

    cursor = get_db().cursor()
    cursor.execute('SELECT * FROM match WHERE time::timestamp < %s::timestamp', (utc_now.strftime('%Y-%m-%d %H:%M'),))

    # get matches which has been started by current time
    for match in cursor.fetchall():
        if match['goal1'] is None or match['goal2'] is None:
            continue

        match_time_utc = datetime.strptime(match['time'], '%Y-%m-%d %H:%M')
        match_time_utc = match_time_utc.replace(tzinfo=tz.gettz('UTC'))

        match_time_local = match_time_utc.astimezone(local_zone)   

        match_date = match_time_local.strftime('%Y-%m-%d')
        match_time = match_time_local.strftime('%H:%M')        

        cursor2 = get_db().cursor()
        cursor2.execute('SELECT * FROM match_bet WHERE (username = %s AND match_id = %s)', (user_name, match['id']))
        match_bet = cursor2.fetchone()

        prize = 0
        bet_amount = 0

        if match_bet is not None:
            prize = get_match_prize(match, match_bet)
            bet_amount = match_bet['bet']
        
        # find match day if it does not exist create it
        match_day = None

        for day in day_prefabs:
            if day.date == match_date:
                match_day = day

        if match_day is None:
            match_day = DayPrefab(date=match_date, points=[])
            day_prefabs.append(match_day) 

        # add prize and subtract bet
        match_day.points.append(prize)
        match_day.points.append(-1 * bet_amount)

    day_prefabs.sort(key=lambda day : datetime.strptime(day.date, '%Y-%m-%d'))
    return day_prefabs

# get player's current balance 
def get_current_points_by_player(user_name):
    amount = configuration.bet_values.starting_bet_amount
    # substract group and final bet amount
    amount -= get_group_and_final_bet_amount(user_name)

    # add daily point income (win) + outcome (bet)
    for point_by_day in get_daily_points_by_current_time(user_name):
        for point in point_by_day.points:
            amount += point

    amount += get_group_win_amount(user_name)

    return amount