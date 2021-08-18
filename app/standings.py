from os import name

from dateutil.tz.tz import datetime_ambiguous
from app import auth
from flask import Blueprint
from flask import redirect
from flask import g
from flask import flash
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from app.db import get_db
from app.auth import login_required

bp = Blueprint("standings", __name__, '''url_prefix="/group"''')

from datetime import datetime
from dateutil import tz
from collections import namedtuple

from app.score_calculator import *

Player = namedtuple("Player", "nick, days")
DayPrefab = namedtuple("DayPrefab", "date, points")
Day = namedtuple("Day", "year, month, day, point")
CurrentState = namedtuple("CurrentState", "name, point")

def current_sort(current_state):
    return current_state.point

def get_prize(match, match_bet):
    prize = 0

    result1 = match["goal1"]
    result2 = match["goal2"]

    odd1 = match["odd1"]
    oddX = match["oddX"]
    odd2 = match["odd2"]

    goal1 = match_bet["goal1"]
    goal2 = match_bet["goal2"]
    bet = match_bet["bet"]

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

    return prize

def get_points_by_day(user_name):
    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))

    day_prefabs = []

    for match in get_db().execute("SELECT * FROM match WHERE DATETIME(time) < ?", (utc_now.strftime("%Y-%m-%d %H:%M"),)):
        match_time = datetime.strptime(match["time"], "%Y-%m-%d %H:%M")
        match_time = match_time.replace(tzinfo=tz.gettz('UTC'))

        match_time_local = match_time.astimezone(local_zone)   

        match_date = match_time_local.strftime("%Y-%m-%d")
        match_time_string = match_time_local.strftime("%H:%M")        

        match_bet = get_db().execute("SELECT * FROM match_bet WHERE (username = ? AND match_id = ? )", (user_name, match["id"])).fetchone()

        prize = 0

        if match_bet is not None:
            prize = get_prize(match, match_bet)
            
        match_day = None

        for day in day_prefabs:
            if day.date == match_date:
                match_day = day

        if match_day is None:
            match_day = DayPrefab(date=match_date, points=[])
            day_prefabs.append(match_day) 

        match_day.points.append(prize)

    day_prefabs.sort(key=sorting_date)

    return day_prefabs

def get_current_points_by_player(user_name):
    amount = starting_bet_amount
    amount -= get_group_bet_amount(user_name)

    for point_by_day in get_points_by_day(user_name):
        for point in point_by_day.points:
            amount += point

    amount += get_group_win_amount(user_name)

    return amount

@bp.route("/standings", methods=("GET", "POST"))
@login_required
def standings():
    players = []

    current_states = []

    for player in get_db().execute("SELECT username FROM user", ()):
        user_name = player["username"]

        group_bet_amount = get_group_bet_amount(user_name)
        group_winning_amount = get_group_win_amount(user_name)

        day_prefabs = get_points_by_day(user_name)

        days = []  
        
        group_deadline_time_object = datetime.strptime(group_deadline_time, "%Y-%m-%d %H:%M")
        two_days_before_deadline = group_deadline_time_object - timedelta(days=2)
        one_day_before_deadline = group_deadline_time_object - timedelta(days=1)

        amount = starting_bet_amount
        days.append(Day(year=two_days_before_deadline.year, month=two_days_before_deadline.month-1, day=two_days_before_deadline.day, point=amount))        
        amount -= group_bet_amount
        days.append(Day(year=one_day_before_deadline.year, month=one_day_before_deadline.month-1, day=one_day_before_deadline.day, point=amount))

        prev_date = group_deadline_time_object
        prev_amount = amount

        for day_prefab in day_prefabs:
            daily_point = 0

            for point in day_prefab.points:
                daily_point += point

            day_date = datetime.strptime(day_prefab.date, "%Y-%m-%d")

            while (True):
                prev_date += timedelta(days=1)

                if prev_date < day_date:
                    days.append(Day(year=prev_date.year, month=prev_date.month-1, day=prev_date.day, point=prev_amount))
                else:
                    break

            amount += daily_point

            days.append(Day(year=day_date.year, month=day_date.month-1, day=day_date.day, point=amount))

            group_evaluation_date_object = datetime.strptime(group_evaluation_date, "%Y-%m-%d")

            if day_prefab.date == group_evaluation_date_object:
                amount += group_winning_amount
                days.append(Day(year=day_date.year, month=day_date.month-1, day=day_date.day + 1, point=amount))
                prev_date = day_date + timedelta(days=1)
            else:
                prev_date = day_date
            
            prev_amount = amount

        current_states.append(CurrentState(name=user_name, point=days[-1].point))

        day_prefabs.clear()

        players.append(Player(nick=user_name, days=days))

    current_states.sort(key=current_sort, reverse=True)

    return render_template("standings.html", username = g.user["username"], admin=g.user["admin"], players=players, current_states=current_states)

#https://canvasjs.com/html5-javascript-line-chart/
#https://stackoverflow.com/questions/35854244/how-can-i-create-a-horizontal-scrolling-chart-js-line-chart-with-a-locked-y-axis