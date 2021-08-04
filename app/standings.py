from os import name
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

@bp.route("/standings", methods=("GET", "POST"))
@login_required
def standings():
    players = []

    for player in get_db().execute("SELECT username FROM user", ()):
        user_name = player["username"]

        utc_now = datetime.utcnow()
        utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))

        day_prefabs = []

        group_bet_amount = 300
        group_winning_amount = 1100

        for match in get_db().execute("SELECT * FROM match WHERE DATETIME(time) < ?", (utc_now.strftime("%Y-%m-%d %H:%M"),)):
            match_time = datetime.strptime(match["time"], "%Y-%m-%d %H:%M")
            match_time.replace(tzinfo=tz.gettz('UTC'))

            match_time_local = match_time.astimezone(local_zone)   

            match_date = match_time_local.strftime("%Y-%m-%d")
            match_time_string = match_time_local.strftime("%H:%M")        

            match_bet = get_db().execute("SELECT * FROM match_bet WHERE (username = ? AND match_id = ? )", (user_name, match["id"])).fetchone()

            prize = 0

            if match_bet is not None:
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

            match_day = None

            for day in day_prefabs:
                if day.date == match_date:
                    match_day = day

            if match_day is None:
                match_day = DayPrefab(date=match_date, points=[])
                day_prefabs.append(match_day) 

            match_day.points.append(prize)

        days = []

        day_prefabs.sort(key=sorting_date)

        amount = starting_bet_amount
        days.append(Day(year=2021, month=7-1, day=29, point=amount))

        amount -= group_bet_amount

        days.append(Day(year=2021, month=7-1, day=30, point=amount))

        prev_date = datetime(2021,7,30)
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

            if day_prefab.date == group_evaulation_date:
                amount += group_winning_amount
                days.append(Day(year=day_date.year, month=day_date.month-1, day=day_date.day + 1, point=amount))
                prev_date = day_date + timedelta(days=1)
            else:
                prev_date = day_date
            
            prev_amount = amount

        day_prefabs.clear()

        players.append(Player(nick=user_name, days=days))

    return render_template("standings.html", username = g.user["username"], admin=g.user["admin"], players=players)

#https://canvasjs.com/html5-javascript-line-chart/
#https://stackoverflow.com/questions/35854244/how-can-i-create-a-horizontal-scrolling-chart-js-line-chart-with-a-locked-y-axis