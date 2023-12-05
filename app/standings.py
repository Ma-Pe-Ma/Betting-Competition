from flask import Blueprint
from flask import g
from flask import render_template

from copy import copy
from datetime import datetime, timedelta
from dateutil import tz

from app.db import get_db
from app.auth import login_required

from app.configuration import configuration

from app.tools.score_calculator import get_group_win_amount, get_group_and_final_bet_amount, get_daily_points_by_current_time, get_group_object_for_user
from app.tools.group_calculator import get_tournament_bet
from app.tools import time_determiner

from sqlalchemy import text

bp = Blueprint('standings', __name__, '''url_prefix="/standings"''')

def create_standings(language = None):
    if language is None:
        language = g.user['language']

    deadline_times = configuration.deadline_times

    players = []
    current_player_standings = []

    utc_now = time_determiner.get_now_time_object()

    #create unique time objects
    group_deadline_time_object : datetime = time_determiner.parse_datetime_string(deadline_times.register)
    two_days_before_deadline = group_deadline_time_object - timedelta(days=2)
    one_day_before_deadline = group_deadline_time_object - timedelta(days=1)
    group_evaluation_time_object : datetime = time_determiner.parse_datetime_string(deadline_times.group_evaluation)

    #iterate through users
    query_string = text('SELECT username FROM bet_user')
    result = get_db().session.execute(query_string)

    for player in result.fetchall():
        username = player.username
        
        # find group bet/win amount
        group_bet_amount = get_group_and_final_bet_amount(username)
        group_object = get_group_object_for_user(username, language=language)
        group_winning_amount = get_group_win_amount(group_object)

        days = []

        #two days before starting show start amount, same for everyone
        amount = configuration.bet_values.starting_bet_amount
        days.append({'year' : two_days_before_deadline.year, 'month' : two_days_before_deadline.month-1, 'day' : two_days_before_deadline.day, 'point' : amount})

        #one day before starting show startin minus group+final betting amount
        amount -= group_bet_amount
        days.append({'year' : one_day_before_deadline.year, 'month' : one_day_before_deadline.month-1, 'day' : one_day_before_deadline.day, 'point' : amount})

        prev_date = group_deadline_time_object
        prev_amount = amount

        #generate in/out points per day for user
        raw_days = get_daily_points_by_current_time(username)

        # iterate thorugh the days to
        for raw_day in raw_days:
            # calculate the daily point difference
            daily_point = 0
            for point in raw_day['points']:
                daily_point += point

            day_date = datetime.strptime(raw_day['date'], "%Y-%m-%d")

            # if there's a break between matchdays fill the days during break with the last matchdays result
            while True:
                prev_date += timedelta(days=1)

                if prev_date.date() < day_date.date():
                    days.append({'year' : prev_date.year, 'month' : prev_date.month-1, 'day' : prev_date.day, 'point' : prev_amount})
                else:
                    break

            # add the examined day to the chart
            amount += daily_point
            '''days.append({'year' : day_date.year, 'month' : day_date.month -1 , 'day' : day_date.day, 'point' : amount})

            # if the current day is the group evaulation day add a new (fake) day which shows the group bet point win amounts,
            if day_date.date() == group_evaluation_time_object.date() and utc_now > group_evaluation_time_object.replace(tzinfo=tz.gettz('UTC')):
                amount += group_winning_amount
                fake_day = day_date + timedelta(days=1)
                days.append({'year' : fake_day.year, 'month' : fake_day.month - 1, 'day' : fake_day.day, 'point' : amount})
                prev_date = fake_day
            else:
                prev_date = day_date'''

            if day_date.date() == group_evaluation_time_object.date() and utc_now > group_evaluation_time_object.replace(tzinfo=tz.gettz('UTC')):
                amount += group_winning_amount

            days.append({'year' : day_date.year, 'month' : day_date.month - 1, 'day' : day_date.day, 'point' : amount})
            
            prev_date = day_date
            prev_amount = amount

        tournament_bet_dict = get_tournament_bet(username=username, language=language)

        # if there's a final result then display it on a new day
        if tournament_bet_dict is not None and tournament_bet_dict['success'] is not None:
            if tournament_bet_dict['success'] == 1:
                amount += tournament_bet_dict['prize']
            elif tournament_bet_dict['success'] == 2:
                pass
            
            day_after_finnish = prev_date + timedelta(days=1)
            days.append({'year' : day_after_finnish.year, 'month' : day_after_finnish.month - 1, 'day' : day_after_finnish.day, 'point' :amount})

        #add the last/current player point to seperate list which will be used in a list-chart
        current_player_standings.append({'name' : username, 'point' : days[-1]['point'], 'previous_point' : days[-2]['point'], 'position_diff' : -1})

        raw_days.clear()

        players.append({'nick' : username, 'days' : days})

    #order the current player standings by the points
    current_player_standings.sort(key=lambda player_standing : player_standing['point'], reverse=True)

    #create previous day's standings
    previous_player_standings = copy(current_player_standings)
    previous_player_standings.sort(key=lambda prev_player_standing : prev_player_standing['previous_point'], reverse=True)

    for current_position, current_player_standing in enumerate(current_player_standings):
        position_diff = -1

        for previous_position, previous_player_standing in enumerate(previous_player_standings):
            if previous_player_standing['name'] == current_player_standing['name']:
                position_diff = - (current_position - previous_position)
                break

        current_player_standing['position_diff'] = position_diff

    previous_player_standings.clear()

    return (players, current_player_standings)

@bp.route('/standings', methods=('GET',))
@login_required
def standings():
    standings = create_standings()
    return render_template('/standings.html', players=standings[0], standings=standings[1])