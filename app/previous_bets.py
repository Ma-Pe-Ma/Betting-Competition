from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
from app.db import get_db
from app.auth import login_required

from collections import namedtuple
from datetime import datetime
from dateutil import tz

from app.tools.score_calculator import get_group_and_final_bet_amount, get_group_win_amount
from app.tools.score_calculator import prize_result
from app.tools.group_calculator import get_final_bet

from app.configuration import starting_bet_amount
from app.configuration import local_zone
from app.configuration import group_evaluation_time

bp = Blueprint('previous', __name__, '''url_prefix="/previous"''')

Day = namedtuple('Day', 'number, date, id, matches')
Match = namedtuple('Match', 'ID, type, time, team1, team2, result1, result2, odd1, oddX, odd2, goal1, goal2, bet, prize, bonus, balance, bet_result')

@bp.route('/previous-bets', methods=('GET',))
@login_required
def prev_bets():
    user_name = request.args.get('name')

    # download users's previous bets which will be inserted into the webpage
    if user_name is not None:
        utc_now = datetime.utcnow()
        utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))

        group_evaluation_time_object = datetime.strptime(group_evaluation_time, '%Y-%m-%d %H:%M')

        start_amount = starting_bet_amount - get_group_and_final_bet_amount(user_name)
        group_bonus = get_group_win_amount(user_name)
        balance_after_group = 0

        days = []

        number_of_match_bets = 0
        number_of_successful_bets = 0

        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM match WHERE time::timestamp < %s::timestamp', (utc_now.strftime('%Y-%m-%d %H:%M'),))

        # iterate through matches which has already been played (more precisely started)
        for previous_match in cursor.fetchall():
            #match time in UTC
            match_time = datetime.strptime(previous_match['time'], '%Y-%m-%d %H:%M')
            match_time = match_time.replace(tzinfo=tz.gettz('UTC'))
            
            #match time in local time
            match_time_local = match_time.astimezone(local_zone)   

            match_date = match_time_local.strftime('%Y-%m-%d')
            match_time_string = match_time_local.strftime('%H:%M')

            # get the user's bet for the match 
            cursor0 = get_db().cursor()
            cursor0.execute('SELECT * FROM match_bet WHERE username=%s AND match_id = %s', (user_name, previous_match['id']))
            match_bet = cursor0.fetchone()

            result1 = previous_match['goal1']
            result2 = previous_match['goal2']

            odd1 = previous_match['odd1']
            oddX = previous_match['oddx']
            odd2 = previous_match['odd2']

            goal1 = match_bet['goal1'] if match_bet is not None else ''
            goal2 = match_bet['goal2'] if match_bet is not None else ''
            bet = match_bet['bet'] if match_bet is not None else 0

            bonus = 0
            prize = 0

            bet_result = 0

            if match_bet is not None and result1 is not None:
                number_of_match_bets += 1

                result_value = prize_result(result1, result2, goal1, goal2)

                bet_result = 1

                # determine won credits
                if result_value.actual == result_value.bet:
                    number_of_successful_bets += 1

                    if result_value.actual == 1:
                        prize = bet * odd1
                    elif result_value.actual == -1:
                        prize = bet * odd2
                    else:
                        prize = bet * oddX
                    
                    bonus = bet * result_value.bonus_multiplier

                    bet_result = 2

            cursor1 = get_db().cursor()
            cursor1.execute('SELECT translation FROM team_translation WHERE name=%s AND language=%s', (previous_match['team1'], g.user['language']))
            team1_local = cursor1.fetchone()

            cursor2 = get_db().cursor()
            cursor2.execute('SELECT translation FROM team_translation WHERE name=%s AND language=%s', (previous_match['team2'], g.user['language']))
            team2_local = cursor2.fetchone()

            match_object = Match(previous_match['id'], time = match_time_string, type=previous_match['round'], team1=team1_local['translation'], team2=team2_local['translation'], result1=result1, result2=result2, odd1=odd1, oddX=oddX, odd2=odd2, goal1=goal1, goal2=goal2, bet=bet, prize=prize, bonus=bonus, balance=0, bet_result=bet_result)

            # find match_day it does not exist create it
            match_day = None

            for day in days:
                if day.date == match_date:
                    match_day = day

            if match_day is None:
                match_day = Day(number=0, date=match_date, id=match_time_local.weekday(), matches=[])
                days.append(match_day) 

            match_day.matches.append(match_object)

        # order days by date
        days.sort(key=lambda day : datetime.strptime(day.date, "%Y-%m-%d"))
        amount = start_amount

        modified_days = []

        for i, day in enumerate(days):
            day.matches.sort(key=lambda match : datetime.strptime(match.time, '%H:%M'))

            modifed_matches = []

            # calculate balance after match
            for match in day.matches:
                amount -= int(match.bet)
                amount += match.prize + match.bonus
                modifed_matches.append(match._replace(balance=amount))
        
            day.matches.clear()
            modified_days.append(day._replace(number = i + 1, matches = modifed_matches))

            day_date_object = datetime.strptime(day.date, '%Y-%m-%d')

            #if checked day is group evaulation date than add group win amount at end
            if utc_now > group_evaluation_time_object and day_date_object.date() == group_evaluation_time_object.date():
                amount += group_bonus
                balance_after_group = amount

        days.clear()     

        group_evaluation_date = group_evaluation_time_object.date().strftime('%Y-%m-%d')

        final_bet_object = get_final_bet(user_name=user_name, language=g.user['language'])

        # if there's a final result then display it on a new day
        if final_bet_object is not None and final_bet_object.success is not None:
            if final_bet_object.success == 1:
                amount += final_bet_object.betting_amount * final_bet_object.multiplier
                    
        finishing_balance = amount

        if number_of_match_bets == 0:
            success_rate = 0        
        else:
            success_rate = number_of_successful_bets / number_of_match_bets

        return render_template(g.user['language'] + '/previous-bet/previous-day-match.html', days=modified_days, group_evaluation_date=group_evaluation_date, start_amount=start_amount, group_bonus=group_bonus, balance_after_group=balance_after_group, final_bet=final_bet_object, finishing_balance = finishing_balance, success_rate=success_rate)

    # if no user name provided send down the username list and render the base page
    cursor = get_db().cursor()
    cursor.execute('SELECT username FROM bet_user WHERE NOT username=\'RESULT\' ORDER BY username ASC', ())
    players = cursor.fetchall()

    return render_template(g.user['language'] + '/previous-bet/previous-bets.html', players=players)