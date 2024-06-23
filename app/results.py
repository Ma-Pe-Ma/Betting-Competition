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
from flask_babel import gettext

bp = Blueprint('results', __name__, '''url_prefix="/results"''')

@bp.route('/results', methods=['GET'])
@sign_in_required()
def prev_bets():
    player_query_string = text('SELECT username FROM bet_user ORDER BY UPPER(username) ASC')
    player_result = get_db().session.execute(player_query_string)
    players = player_result.fetchall()

    date_query_string = text('SELECT date(match.datetime) AS date FROM match WHERE unixepoch(match.datetime) < unixepoch(:now) GROUP BY date(match.datetime) ORDER BY date(match.datetime) DESC')
    date_result = get_db().session.execute(date_query_string, {'now' : time_handler.get_now_time_string()})
    dates = date_result.fetchall()

    return render_template('/results/results.html', players=players, dates=dates)

@bp.route('/results/user', methods=['GET'])
@sign_in_required()
def prev_bets_by_user():
    username : str = request.args.get('name')

    if username is None:
        return '', gettext('The username has not been specified.')

    query_string = score_calculator.match_evaluation_query_string.text

    query_string +=  """SELECT match.id, tr1.translation AS team1, tr2.translation AS team2, match.goal1 AS rgoal1, match.goal2 AS rgoal2, match.odd1, match.oddX, match.odd2,
                            match_prize.goal1 AS bgoal1, match_prize.goal2 AS bgoal2, COALESCE(match_prize.bonus * match_prize.bet, 0) AS bonus, COALESCE(match_prize.multiplier * match_prize.bet, 0) AS prize, COALESCE(match_prize.bet, 0) AS bet,
                            COALESCE((match_prize.bonus + match_prize.multiplier - 1) * match_prize.bet, 0) AS diff, COALESCE(match_prize.success, 0) AS success, 
                            (strftime('%w', match.local_datetime) + 6) % 7 AS weekday, date(match.local_datetime) AS date, strftime('%H:%M', match.local_datetime) AS time, match.datetime
                        FROM (SELECT match.*, time_converter(match.datetime, 'utc', :tz) AS local_datetime FROM match) AS match 
                        LEFT JOIN match_prize ON match_prize.id = match.id AND match_prize.username = :u 
                        LEFT JOIN team_translation AS tr1 ON tr1.name=match.team1 AND tr1.language = :l 
                        LEFT JOIN team_translation AS tr2 ON tr2.name=match.team2 AND tr2.language = :l 
                        WHERE unixepoch(match.datetime) <= unixepoch(:now) 
                        ORDER BY datetime"""

    query_string =  '''
    WITH results AS (SELECT *,
            COALESCE(:starting_amount + (CASE WHEN datetime(datetime) > :group_evaluation_time THEN :group_bonus ELSE 0 END) + SUM(diff) OVER (ROWS BETWEEN UNBOUNDED PRECEDING AND 0 PRECEDING), :starting_amount) AS balance,
            SUM(success) OVER (PARTITION BY 1) AS sum_success
        FROM (''' + query_string + '''))

    SELECT *,
        (SELECT :starting_amount + SUM(diff) + :group_bonus FROM results WHERE datetime(datetime) < datetime(:group_evaluation_time)) AS after_group
    FROM results
    '''

    group_and_tournament_bet_credit = score_calculator.get_group_and_tournament_bet_amount(username)
    group_bonus = sum(group['prize'] for group in group_calculator.get_group_bet_dict_for_user(username=username).values())
    hit_map = current_app.config['BONUS_MULTIPLIERS']
    tournament_bet_dict = group_calculator.get_tournament_bet_dict_for_user(username=username)
    group_evaluation_date = time_handler.parse_datetime_string(current_app.config['DEADLINE_TIMES']['group_evaluation']).date().strftime('%Y-%m-%d')

    match_list_query_parameters = {
        'now' : time_handler.get_now_time_string(),
        'group_evaluation_time' : current_app.config['DEADLINE_TIMES']['group_evaluation'],
        'starting_amount' : current_app.config['BET_VALUES']['starting_bet_amount'] - group_and_tournament_bet_credit,
        'group_bonus' : group_bonus,
        'bullseye' : hit_map['bullseye'], 'difference' : hit_map['difference'],
        'u' : username, 'l' : g.user['language'], 'tz' : g.user['timezone']
    }

    query_string = text(query_string)
    matches = get_db().session.execute(query_string, match_list_query_parameters)
    match_result = matches.fetchall()

    days = {}
    for m in match_result:
        if m.date not in days:
            days[m.date] = {'number' : len(days) + 1, 'date' : m.date, 'weekday' : m.weekday, 'matches' : []}

        match_dict = m._asdict()
        del match_dict['date']
        del match_dict['weekday']
        
        days[m.date]['matches'].append(match_dict)

    extra_data = {
        'start_amount' : current_app.config['BET_VALUES']['starting_bet_amount'],
        'group_and_tournament_bet_credit' : group_and_tournament_bet_credit,
        'group_bonus' : group_bonus,
        'balance_after_group' : match_result[-1].after_group if len(match_result) > 0 else None,
        'current_balance' : match_result[-1].balance + tournament_bet_dict['prize'] if len(match_result) > 0 else current_app.config['BET_VALUES']['starting_bet_amount'] - group_and_tournament_bet_credit,
        'success_rate' : (match_result[0].sum_success / len(match_result)) * 100 if len(match_result) > 0 else 0
    }

    return render_template('/results/results-user.html', days=days, group_evaluation_date=group_evaluation_date, tournament_bet=tournament_bet_dict, extra_data=extra_data)

@bp.route('/results/match', methods=['GET'])
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
                            WHERE unixepoch(match.datetime) < unixepoch(:now) {date_filter}
                            ORDER BY datetime ASC, UPPER(bet_user.username)'''
    
    date_filter = 'AND date(match.datetime) = :date' if date is not '' else ''
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

    return render_template('/results/results-date.html', dates=date_map)
