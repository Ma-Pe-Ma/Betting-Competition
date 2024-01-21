from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
from flask import current_app

from app.tools.db_handler import get_db
from app.auth import sign_in_required

from app.tools import score_calculator
from app.tools import group_calculator
from app.tools import time_handler

from sqlalchemy import text
import datetime

bp = Blueprint('previous', __name__, '''url_prefix="/previous"''')

@bp.route('/previous-bets', methods=('GET',))
@sign_in_required
def prev_bets():
    username : str = request.args.get('name')

    # download users's previous bets which will be inserted into the webpage
    if username is not None:
        days : list = []

        match_list_query_string = score_calculator.match_evaluation_query_string.text + \
                            """SELECT match.id, match.goal1 AS rgoal1, match.goal2 AS rgoal2, match_bet.goal1 AS bgoal1, match_bet.goal2 AS bgoal2, match.odd1, match.odd2, match.oddX, match.round, 
                            match_prize.bonus * match_prize.bet AS bonus, match_prize.multiplier * match_prize.bet AS prize, match_prize.bet AS bet, tr1.translation AS team1, tr2.translation AS team2, 
                            (match_prize.bonus * match_prize.bet + match_prize.multiplier * match_prize.bet - match_prize.bet) AS credit_diff, match_prize.success, 
                            date(match.datetime || :timezone) AS date, strftime('%H:%M', match.datetime || :timezone) AS time, (strftime('%w', match.datetime) + 6) % 7 AS weekday 
                            FROM match 
                            LEFT JOIN match_prize ON match_prize.id = match.id 
                            LEFT JOIN match_bet ON match_bet.match_id = match.id AND match_bet.username = :u 
                            LEFT JOIN team_translation AS tr1 ON tr1.name=match.team1 AND tr1.language = :l 
                            LEFT JOIN team_translation AS tr2 ON tr2.name=match.team2 AND tr2.language = :l 
                            WHERE unixepoch(match.datetime) {r} unixepoch(:group_evaluation_time) AND unixepoch(match.datetime) < unixepoch(:now) 
                            ORDER BY date, datetime"""

        match_list_query_parameters = {'now' : time_handler.get_now_time_string(), 'group_evaluation_time' : current_app.config['DEADLINE_TIMES']['group_evaluation'], 'l' : g.user['language'], 'u' : username, 'timezone' : g.user['timezone'], 'bullseye' : current_app.config['BONUS_MULTIPLIERS']['bullseye'], 'difference' : current_app.config['BONUS_MULTIPLIERS']['difference']}

        def add_to_days(match_rows):
            for match_row in match_rows:
                if match_row.date not in days:
                    days[match_row.date] = {'number' : len(days) + 1, 'date' : match_row.date, 'weekday' : match_row.weekday, 'matches' : []}

                match_dict = match_row._asdict()
                del match_dict['weekday']
                del match_dict['date']

                if match_row.bet > 0:
                    nonlocal number_of_match_bets
                    nonlocal number_of_successful_bets

                    number_of_match_bets =+ 1
                    number_of_successful_bets += match_row.success

                nonlocal amount_at_end_of_match
                amount_at_end_of_match += match_dict['credit_diff']
                match_dict['balance'] = amount_at_end_of_match

                days[match_row.date]['matches'].append(match_dict)

        start_amount = current_app.config['BET_VALUES']['starting_bet_amount']
        group_and_tournament_bet_credit = score_calculator.get_group_and_tournament_bet_amount(username)
        amount_at_end_of_match : int = start_amount - group_and_tournament_bet_credit
        number_of_match_bets : int = 0
        number_of_successful_bets : int = 0

        days = {}        

        # add the group stage matches
        query_string = text(match_list_query_string.format(r='<'))
        group_matches = get_db().session.execute(query_string, match_list_query_parameters)
        add_to_days(group_matches.fetchall())

        # add the group stage bonus
        group_bonus = 0
        group_evaluation_time_object : datetime = time_handler.parse_datetime_string(current_app.config['DEADLINE_TIMES']['group_evaluation'])
        if time_handler.get_now_time_object() > group_evaluation_time_object:
            group_bonus : int = sum(group['prize'] for group in group_calculator.get_group_bet_dict_for_user(username=username).values())
            amount_at_end_of_match += group_bonus

        balance_after_group = amount_at_end_of_match

        # add the knockout stage results
        query_string = text(match_list_query_string.format(r='>'))
        knockout_matches = get_db().session.execute(query_string, match_list_query_parameters)
        add_to_days(knockout_matches)

        # add the tournament bet results
        tournament_bet_dict : dict = group_calculator.get_tournament_bet_dict_for_user(username=username)
        amount_at_end_of_match += tournament_bet_dict['prize']

        success_rate = number_of_successful_bets / number_of_match_bets if number_of_match_bets > 0 else 0

        extra_data = {
            'start_amount' : start_amount,
            'group_and_tournament_bet_credit' : group_and_tournament_bet_credit,
            'group_bonus' : group_bonus,
            'balance_after_group' : balance_after_group,
            'current_balance' : amount_at_end_of_match,
            'success_rate' : success_rate
        }

        group_evaluation_date = group_evaluation_time_object.date().strftime('%Y-%m-%d')

        return render_template('/previous-bet/previous-day-match.html', days=days, group_evaluation_date=group_evaluation_date, tournament_bet=tournament_bet_dict, extra_data=extra_data)

    # if no user name provided send down the username list and render the base page
    query_string = text('SELECT username FROM bet_user ORDER BY username ASC')
    result = get_db().session.execute(query_string)
    players = result.fetchall()

    return render_template('/previous-bet/previous-bets.html', players=players)