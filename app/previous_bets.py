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

@bp.route('/previous-bets', methods=['GET'])
@sign_in_required()
def prev_bets():
    player_query_string = text('SELECT username FROM bet_user ORDER BY UPPER(username) ASC')
    player_result = get_db().session.execute(player_query_string)
    players = player_result.fetchall()

    date_query_string = text('SELECT date(match.datetime) AS date FROM match WHERE unixepoch(match.datetime) < unixepoch(:now) GROUP BY date(match.datetime) ORDER BY date(match.datetime) DESC')
    date_result = get_db().session.execute(date_query_string, {'now' : time_handler.get_now_time_string()})
    dates = date_result.fetchall()

    return render_template('/previous-bet/previous-bets.html', players=players, dates=dates)

@bp.route('/previous-bets/user', methods=['GET'])
@sign_in_required()
def prev_bets_by_user():
    username : str = request.args.get('name')

    # download users's previous bets which will be inserted into the webpage
    if username is None:
        return '', 400
    
    days : list = []

    match_list_query_string = score_calculator.match_evaluation_query_string.text + \
                        """SELECT match.id, match.goal1 AS rgoal1, match.goal2 AS rgoal2, match_prize.goal1 AS bgoal1, match_prize.goal2 AS bgoal2, match.odd1, match.odd2, match.oddX, match.round, 
                            COALESCE(match_prize.bonus * match_prize.bet, 0) AS bonus, COALESCE(match_prize.multiplier * match_prize.bet, 0) AS prize, COALESCE(match_prize.bet, 0) AS bet, tr1.translation AS team1, tr2.translation AS team2, 
                            COALESCE(match_prize.bonus * match_prize.bet + match_prize.multiplier * match_prize.bet - match_prize.bet, 0) AS credit_diff, COALESCE(match_prize.success, 0) AS success, 
                            (strftime('%w', match.local_datetime) + 6) % 7 AS weekday, date(match.local_datetime) AS date, strftime('%H:%M', match.local_datetime) AS time
                        FROM (SELECT match.*, time_converter(match.datetime, 'utc', :tz) AS local_datetime FROM match) AS match 
                        LEFT JOIN match_prize ON match_prize.id = match.id AND match_prize.username = :u 
                        LEFT JOIN team_translation AS tr1 ON tr1.name=match.team1 AND tr1.language = :l 
                        LEFT JOIN team_translation AS tr2 ON tr2.name=match.team2 AND tr2.language = :l 
                        WHERE unixepoch(match.datetime) {r} unixepoch(:group_evaluation_time) AND unixepoch(match.datetime) <= unixepoch(:now) 
                        ORDER BY datetime"""

    hit_map = current_app.config['BONUS_MULTIPLIERS']
    match_list_query_parameters = {'now' : time_handler.get_now_time_string(), 'group_evaluation_time' : current_app.config['DEADLINE_TIMES']['group_evaluation'], 'l' : g.user['language'], 'tz' : g.user['timezone'], 'u' : username, 'bullseye' : hit_map['bullseye'], 'difference' : hit_map['difference']}

    def add_to_days(match_rows):
        for match_row in match_rows:
            match_dict = match_row._asdict()

            if match_dict['date'] not in days:
                days[match_dict['date']] = {'number' : len(days) + 1, 'date' : match_dict['date'], 'weekday' : match_dict['weekday'], 'matches' : []}

            del match_dict['weekday']

            if match_row.bet > 0:
                nonlocal number_of_match_bets
                nonlocal number_of_successful_bets

                number_of_match_bets = number_of_match_bets + 1
                number_of_successful_bets += match_row.success

            nonlocal amount_at_end_of_match
            amount_at_end_of_match += match_dict['credit_diff']
            match_dict['balance'] = amount_at_end_of_match

            days[match_dict['date']]['matches'].append(match_dict)

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
    group_evaluation_time_object : datetime.datetime = time_handler.parse_datetime_string(current_app.config['DEADLINE_TIMES']['group_evaluation'])
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

    success_rate = (number_of_successful_bets / number_of_match_bets if number_of_match_bets > 0 else 0) * 100

    extra_data = {
        'start_amount' : start_amount,
        'group_and_tournament_bet_credit' : group_and_tournament_bet_credit,
        'group_bonus' : group_bonus,
        'balance_after_group' : balance_after_group,
        'current_balance' : amount_at_end_of_match,
        'success_rate' : success_rate
    }

    group_evaluation_date = group_evaluation_time_object.date().strftime('%Y-%m-%d')

    return render_template('/previous-bet/previous-user.html', days=days, group_evaluation_date=group_evaluation_date, tournament_bet=tournament_bet_dict, extra_data=extra_data)

@bp.route('/previous-bets/match', methods=['GET'])
@sign_in_required()
def prev_bets_by_match():
    date = request.args.get('date')

    match_query_string = score_calculator.match_evaluation_query_string.text \
                        + '''SELECT tr1.translation AS tr1, tr2.translation AS tr2, match.id AS id, tr3.translation AS round, match.goal1 AS rgoal1, match.goal2 AS rgoal2, 
                                match_prize.bonus * match_prize.bet AS bonus, match_prize.multiplier * match_prize.bet AS prize, match_prize.bet AS bet, 
                                (match_prize.bonus * match_prize.bet + match_prize.multiplier * match_prize.bet - match_prize.bet) AS credit_diff, match_prize.success, 
                                bet_user.username AS username, match_prize.goal1 AS bgoal1, match_prize.goal2 AS bgoal2, 
                                match.odd1, match.odd2, match.oddX, date(match.datetime) AS date 
                            FROM match 
                            RIGHT JOIN bet_user 
                            LEFT JOIN match_prize ON match_prize.id = match.id AND match_prize.username = bet_user.username 
                            LEFT JOIN team_translation AS tr1 ON tr1.name = match.team1 AND tr1.language = :l 
                            LEFT JOIN team_translation AS tr2 ON tr2.name = match.team2 AND tr2.language = :l 
                            LEFT JOIN team_translation AS tr3 ON tr3.name = match.round AND tr3.language = :l 
                            WHERE {date_filter} unixepoch(match.datetime) < unixepoch(:now)
                            ORDER BY datetime ASC, UPPER(bet_user.username)'''
    
    date_filter = 'date(match.datetime) = :date AND' if date is not '' else ''
    match_query_string = text(match_query_string.format(date_filter=date_filter))
    
    hit_map = current_app.config['BONUS_MULTIPLIERS']
    match_result = get_db().session.execute(match_query_string, {'date' : date, 'now' : time_handler.get_now_time_string(), 'l' : g.user['language'], 'bullseye' : hit_map['bullseye'], 'difference' : hit_map['difference']})
    matches = match_result.fetchall()

    keys = ['date', 'odd1', 'oddX', 'odd2', 'round', 'tr1', 'tr2', 'rgoal1', 'rgoal2', 'id']

    date_map = {}
    for match in matches:
        match_dict = match._asdict()

        if match.date not in date_map:
            date_map[match.date] = {}

        if match.id not in date_map[match.date]:
            date_map[match.date][match.id] = {'players' : [], 'success' : 0}
            for key in keys:
                date_map[match.date][match.id][key] = match_dict[key]
        
        for key in keys:
            del match_dict[key]

        date_map[match.date][match.id]['success'] += match_dict['success'] if match_dict['success'] is not None else 0
        date_map[match.date][match.id]['players'].append(match_dict)

    return render_template('/previous-bet/previous-date.html', dates=date_map)
