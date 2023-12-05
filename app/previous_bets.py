from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
from app.db import get_db
from app.auth import login_required

from datetime import datetime
from dateutil import tz

from app.tools.score_calculator import get_group_and_final_bet_amount, get_group_win_amount, get_group_object_for_user
from app.tools.score_calculator import get_bet_result_for_match
from app.tools.group_calculator import get_tournament_bet
from app.tools import time_determiner

from app.configuration import configuration

from sqlalchemy import text

bp = Blueprint('previous', __name__, '''url_prefix="/previous"''')

@bp.route('/previous-bets', methods=('GET',))
@login_required
def prev_bets():
    username : str = request.args.get('name')

    # download users's previous bets which will be inserted into the webpage
    if username is not None:
        days : list = []

        query_string = text("SELECT match.time, match.goal1 AS rgoal1, match.goal2 AS rgoal2, match_bet.goal1 AS bgoal1, match_bet.goal2 AS bgoal2, COALESCE(match_bet.bet, 0) AS bet, tr1.translation AS team1, tr2.translation AS team2 "
                            "FROM match "
                            "LEFT JOIN match_bet ON match_bet.match_id = match.id AND match_bet.username = :u "
                            "LEFT JOIN team_translation AS tr1 ON tr1.name=match.team1 AND tr1.language = :l "
                            "LEFT JOIN team_translation AS tr2 ON tr2.name=match.team2 AND tr2.language = :l "
                            "WHERE unixepoch(match.time) < unixepoch(:now)")
        result = get_db().session.execute(query_string, {'now' : time_determiner.get_now_time_string(), 'l' : g.user['language'], 'u' : g.user['username']})

        utc_now = time_determiner.get_now_time_object()

        # iterate through matches which has already been played (more precisely started)
        for match_and_bet_parameters in result.fetchall():
            # calculating local timeparameters
            match_time = datetime.strptime(match_and_bet_parameters.time, '%Y-%m-%d %H:%M').replace(tzinfo=tz.gettz('UTC'))
            match_time_local : datetime = match_time.astimezone(g.user['tz'])
            match_date_string : str = match_time_local.strftime('%Y-%m-%d')
            match_time_string : str = match_time_local.strftime('%H:%M')            

            # convert db match data to dict for template
            match_dict : dict = match_and_bet_parameters._asdict()
            match_dict['time'] = match_time_string

            get_bet_result_for_match(match_dict)            

            # find match_day it does not exist create it
            match_day = None

            for day in days:
                if day['date'] == match_date_string:
                    match_day = day

            if match_day is None:
                match_day = { 'date' : match_date_string, 'dayID' : match_time_local.weekday(), 'matches' : []}
                days.append(match_day) 

            match_day['matches'].append(match_dict)

        # order days by date
        days.sort(key=lambda day : datetime.strptime(day['date'], "%Y-%m-%d"))
        
        group_evaluation_time_object : datetime = time_determiner.parse_datetime_string(configuration.deadline_times.group_evaluation) 

        start_amount = configuration.bet_values.starting_bet_amount - get_group_and_final_bet_amount(username)
        amount_at_end_of_match : int = start_amount    
        balance_after_group : int = 0
        number_of_match_bets : int = 0
        number_of_successful_bets : int = 0

        group_object = get_group_object_for_user(username)
        group_bonus : int = get_group_win_amount(group_object)

        for i, day in enumerate(days):
            day['number'] = i + 1
            day['matches'].sort(key=lambda match : datetime.strptime(match['time'], '%H:%M'))

            # calculate balance after match
            for match in day['matches']:
                if match['bet_outcome'] is not None:
                    if match['match_outcome'] is not None: 
                        number_of_match_bets += 1

                        if match['match_outcome'] == match['bet_outcome']:
                            number_of_successful_bets += 1
                            amount_at_end_of_match -= match['bet']
                            amount_at_end_of_match += match['prize'] + match['bonus']

                match['balance'] = amount_at_end_of_match

            day_date_object = datetime.strptime(day['date'], '%Y-%m-%d')

            #if checked day is group evaulation date than add group win amount at end
            if utc_now > group_evaluation_time_object and day_date_object.date() == group_evaluation_time_object.date():
                amount_at_end_of_match += group_bonus
                balance_after_group = amount_at_end_of_match  

        group_evaluation_date = group_evaluation_time_object.date().strftime('%Y-%m-%d')

        tournament_bet_dict : dict = get_tournament_bet(username=username)

        # if there's a final result then display it on a new day
        if tournament_bet_dict is not None and tournament_bet_dict['success'] is not None:
            if tournament_bet_dict['success'] == 1:
                amount_at_end_of_match += tournament_bet_dict['bet'] * tournament_bet_dict['multiplier']
                    
        finishing_balance = amount_at_end_of_match

        if number_of_match_bets == 0:
            success_rate = 0        
        else:
            success_rate = number_of_successful_bets / number_of_match_bets

        return render_template('/previous-bet/previous-day-match.html', days=days, group_evaluation_date=group_evaluation_date, start_amount=start_amount, group_bonus=group_bonus, balance_after_group=balance_after_group, final_bet=tournament_bet_dict, finishing_balance = finishing_balance, success_rate=success_rate)

    # if no user name provided send down the username list and render the base page
    query_string = text('SELECT username FROM bet_user WHERE NOT username=\'RESULT\' ORDER BY username ASC')
    result = get_db().session.execute(query_string)
    players = result.fetchall()

    return render_template('/previous-bet/previous-bets.html', players=players)