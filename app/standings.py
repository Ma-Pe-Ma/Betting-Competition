from flask import Blueprint
from flask import g
from flask import render_template

from copy import copy
from datetime import datetime, timedelta
from dateutil import tz
from collections import namedtuple

from app.db import get_db
from app.auth import login_required

from app.configuration import configuration

from app.tools.score_calculator import get_group_win_amount, get_group_and_final_bet_amount, get_daily_points_by_current_time
from app.tools.group_calculator import get_final_bet

bp = Blueprint('standings', __name__, '''url_prefix="/standings"''')

Player = namedtuple('Player', 'nick, days')
Day = namedtuple('Day', 'year, month, day, point')
CurrentPlayerStanding = namedtuple('CurrentPlayerStanding', 'name, point, previous_point, position_diff')

def create_standings():
    deadline_times = configuration.deadline_times

    players = []

    current_player_standings = []

    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))

    #create unique time objects
    group_deadline_time_object = datetime.strptime(deadline_times.group_bet, '%Y-%m-%d %H:%M')
    two_days_before_deadline = group_deadline_time_object - timedelta(days=2)
    one_day_before_deadline = group_deadline_time_object - timedelta(days=1)
    group_evaluation_time_object = datetime.strptime(deadline_times.group_evaluation, '%Y-%m-%d %H:%M')

    #iterate through users
    cursor = get_db().cursor()
    cursor.execute('SELECT username FROM bet_user', ())

    for player in cursor.fetchall():
        user_name = player['username']
        # TODO eliminate this?
        language = configuration.supported_languages[0]

        # find group bet/win amount
        group_bet_amount = get_group_and_final_bet_amount(user_name)
        group_winning_amount = get_group_win_amount(user_name)

        days = []

        #two days before starting show start amount, same for everyone
        amount = configuration.bet_values.starting_bet_amount
        days.append(Day(year=two_days_before_deadline.year, month=two_days_before_deadline.month-1, day=two_days_before_deadline.day, point=amount))        

        #one day before starting show startin minus group+final betting amount
        amount -= group_bet_amount
        days.append(Day(year=one_day_before_deadline.year, month=one_day_before_deadline.month-1, day=one_day_before_deadline.day, point=amount))

        prev_date = group_deadline_time_object
        prev_amount = amount

        #generate in/out points per day for user
        day_prefabs = get_daily_points_by_current_time(user_name)

        # iterate thorugh the days to
        for day_prefab in day_prefabs:
            # calculate the daily point difference
            daily_point = 0
            for point in day_prefab.points:
                daily_point += point

            day_date = datetime.strptime(day_prefab.date, "%Y-%m-%d")

            # if there's a break between matchdays fill the days during break with the last matchdays result
            while (True):
                prev_date += timedelta(days=1)

                if prev_date.date() < day_date.date():
                    days.append(Day(year=prev_date.year, month=prev_date.month-1, day=prev_date.day, point=prev_amount))
                else:
                    break

            # add the examined day to the chart
            amount += daily_point
            '''days.append(Day(year=day_date.year, month=day_date.month-1, day=day_date.day, point=amount))

            # if the current day is the group evaulation day add a new (fake) day which shows the group bet point win amounts,
            if day_date.date() == group_evaluation_time_object.date() and utc_now > group_evaluation_time_object.replace(tzinfo=tz.gettz('UTC')):
                amount += group_winning_amount
                fake_day = day_date + timedelta(days=1)
                days.append(Day(year=fake_day.year, month=fake_day.month-1, day=fake_day.day, point=amount))
                prev_date = fake_day
            else:
                prev_date = day_date'''

            if day_date.date() == group_evaluation_time_object.date() and utc_now > group_evaluation_time_object.replace(tzinfo=tz.gettz('UTC')):
                amount += group_winning_amount

            days.append(Day(year=day_date.year, month=day_date.month-1, day=day_date.day, point=amount))
            
            prev_date = day_date
            prev_amount = amount

        final_bet_object = get_final_bet(user_name=user_name, language=language)

        # if there's a final result then display it on a new day
        if final_bet_object is not None and final_bet_object.success is not None:
            if final_bet_object.success == 1:
                amount += final_bet_object.betting_amount * final_bet_object.multiplier
            elif final_bet_object.success == 2:
                pass
            
            day_after_finnish = prev_date + timedelta(days=1)
            days.append(Day(year=day_after_finnish.year, month=day_after_finnish.month-1, day=day_after_finnish.day, point=amount))

        #add the last/current player point to seperate list which will be used in a list-chart
        current_player_standings.append(CurrentPlayerStanding(name=user_name, point=days[-1].point, previous_point=days[-2].point, position_diff=-1))

        day_prefabs.clear()

        players.append(Player(nick=user_name, days=days))

    #order the current player standings by the points
    current_player_standings.sort(key=lambda player_standing : player_standing.point, reverse=True)

    #create previous day's standings
    previous_player_standings = copy(current_player_standings)
    previous_player_standings.sort(key=lambda prev_player_standing : prev_player_standing.previous_point, reverse=True)

    modified_current_player_standings = []

    for current_position, current_player_standing in enumerate(current_player_standings):
        position_diff = -1

        for previous_position, previous_player_standing in enumerate(previous_player_standings):
            if previous_player_standing.name == current_player_standing.name:
                position_diff = - (current_position - previous_position)
                break

        modified_current_player_standings.append(current_player_standing._replace(position_diff=position_diff))

    previous_player_standings.clear()
    current_player_standings.clear()

    return (players, modified_current_player_standings)

@bp.route('/standings', methods=('GET',))
@login_required
def standings():
    standings = create_standings()
    return render_template('/standings.html', players=standings[0], standings=standings[1])