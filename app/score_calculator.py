from datetime import date, datetime, timezone, timedelta
from dateutil import tz
from collections import namedtuple

ResultValue = namedtuple("ResultValue", "actual, bet, bonus_multiplier")

group_evaulation_date = "2021-08-02"

local_zone = tz.gettz('Europe/Budapest')

day_names = ["hétfő", "kedd", "szerda", "csütörtök", "péntek", "szombat", "vasárnap"]
bullseye_multiplier = 4
difference_multiplier = 1

starting_bet_amount = 2000
max_group_bet_value = 50

hit_map = [0, 1, 2, 3, 4]

def get_group_bet_amount(user_name):


    return 400


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