from flask import Blueprint
from flask import g
from flask import request
from flask import current_app
from flask import session

from app.tools.db_handler import get_db
from app.auth import sign_in_required

from app.tools import score_calculator
from app.tools import time_handler

from sqlalchemy import text
from flask_babel import gettext

bp = Blueprint('results', __name__, '''url_prefix="/results"''')

@bp.route('/results/user', methods=['GET'])
@sign_in_required()
def results_by_user():
    username : str = request.args.get('name')

    if username is None:
        return '', gettext('The username has not been specified.')

    query_string = """SELECT match.id, tr1.translation AS team1, tr2.translation AS team2, match.goal1 AS goal1, match.goal2 AS goal2, match.odd1, match.oddX, match.odd2,
                            match_prize.goal1 AS bgoal1, match_prize.goal2 AS bgoal2, COALESCE(match_prize.bonus * match_prize.bet, 0) AS bonus, COALESCE(match_prize.multiplier * match_prize.bet, 0) AS prize, COALESCE(match_prize.bet, 0) AS bet,
                            COALESCE((match_prize.bonus + match_prize.multiplier - 1) * match_prize.bet, 0) AS diff, COALESCE(match_prize.success, 0) AS success, 
                            (strftime('%w', match.local_datetime) + 6) % 7 AS weekday, date(match.local_datetime) AS date, strftime('%H:%M', match.local_datetime) AS time, match.datetime
                        FROM (SELECT match.*, time_converter(match.datetime, 'utc', :tz) AS local_datetime FROM match) AS match 
                        LEFT JOIN match_prize ON match_prize.id = match.id AND match_prize.username = :u 
                        LEFT JOIN team_translation AS tr1 ON tr1.name=match.team1 AND tr1.language = :l 
                        LEFT JOIN team_translation AS tr2 ON tr2.name=match.team2 AND tr2.language = :l 
                        WHERE unixepoch(match.datetime) <= unixepoch(:now) 
                        ORDER BY match.datetime"""

    query_string =  "WITH match_prize AS (" + score_calculator.match_evaluation_query_string + '''),
    results AS (SELECT *,
            COALESCE(:starting_bet_amount - :group_and_tournament_bet_credit 
              + (CASE WHEN datetime(datetime) > datetime(:group_evaluation) THEN :group_bonus ELSE 0 END)
              + SUM(diff) OVER (ROWS BETWEEN UNBOUNDED PRECEDING AND 0 PRECEDING), :starting_bet_amount) AS balance,
            SUM(success) OVER (PARTITION BY 1) AS sum_success
        FROM (''' + query_string + ''')
    )

    SELECT *,
        (SELECT :starting_bet_amount - :group_and_tournament_bet_credit + :group_bonus + SUM(diff) FROM results WHERE datetime(results.datetime) <= datetime(:group_evaluation)) AS after_group
    FROM results
    '''
    group_and_tournament_bet_credit = score_calculator.get_group_and_tournament_bet_amount(username)
    
    group_bonus = sum(group['prize'] for group in score_calculator.get_group_bet_dict_for_user(username=username)) if time_handler.get_now_time_object() > time_handler.parse_datetime_string(current_app.config['DEADLINE_TIMES']['group_evaluation']) else 0

    match_list_query_parameters = score_calculator.get_daily_point_parameters()

    match_list_query_parameters.update({'now' : time_handler.get_now_time_string_with_seconds(), 'u' : username, 'l' : session['language'], 'tz' : g.user['timezone'], 'group_and_tournament_bet_credit' : group_and_tournament_bet_credit, 'group_bonus' : group_bonus})

    query_string = text(query_string)
    matches = get_db().session.execute(query_string, match_list_query_parameters)
    match_result = matches.fetchall()

    days = []

    for m in match_result:
        current_day = None

        for d in days:
            if d['date'] == m.date:
                current_day = d
                break

        if current_day is None:
            current_day = {'number' : len(days) + 1, 'date' : m.date, 'weekday' : m.weekday, 'matches' : []}
            days.append(current_day)
        
        match_dict = m._asdict()
        del match_dict['date']
        del match_dict['weekday']
        
        current_day['matches'].append(match_dict) 

    tournament_bet_dict = score_calculator.get_tournament_bet_dict_for_user(username=username)

    knockout = time_handler.get_now_time_object() > time_handler.parse_datetime_string(current_app.config['DEADLINE_TIMES']['group_evaluation'])

    # TODO: current balance not working between last group stage match and first knockout match!
    extra_data = {
        'startAmount' : current_app.config['BET_VALUES']['starting_bet_amount'],
        'groupAndTournamentBetCredit' : group_and_tournament_bet_credit,
        'groupBonus' : group_bonus if knockout else None,
        'balanceAfterGroup' : match_result[-1].after_group if len(match_result) > 0 and knockout else None,
        'currentBalance' : match_result[-1].balance + (tournament_bet_dict['prize'] if time_handler.get_now_time_object() > time_handler.parse_datetime_string(current_app.config['DEADLINE_TIMES']['tournament_end']) else 0) if len(match_result) > 0 else current_app.config['BET_VALUES']['starting_bet_amount'] - group_and_tournament_bet_credit,
        'successRate' : (match_result[0].sum_success / len(match_result)) * 100 if len(match_result) > 0 else 0
    }

    return {'days': days, 'extraData': extra_data, 'tournamentBet': tournament_bet_dict}

@bp.route('/results/match', methods=['GET'])
@sign_in_required()
def results_by_match():
    date = request.args.get('date')

    match_query_string = '''WITH match_prize AS (''' + score_calculator.match_evaluation_query_string + ''') SELECT tr1.translation AS team1, tr2.translation AS team2, match.id AS id, tr3.translation AS round, match.goal1 AS goal1, match.goal2 AS goal2, 
                                match_prize.bonus * match_prize.bet AS bonus, match_prize.multiplier * match_prize.bet AS prize, match_prize.bet AS bet, 
                                (match_prize.bonus * match_prize.bet + match_prize.multiplier * match_prize.bet - match_prize.bet) AS credit_diff, match_prize.success, 
                                bet_user.username AS username, match_prize.goal1 AS bgoal1, match_prize.goal2 AS bgoal2, 
                                match.odd1, match.odd2, match.oddX 
                            FROM match 
                            RIGHT JOIN bet_user 
                            LEFT JOIN match_prize ON match_prize.id = match.id AND match_prize.username = bet_user.username 
                            LEFT JOIN team_translation AS tr1 ON tr1.name = match.team1 AND tr1.language = :l 
                            LEFT JOIN team_translation AS tr2 ON tr2.name = match.team2 AND tr2.language = :l 
                            LEFT JOIN team_translation AS tr3 ON tr3.name = match.round AND tr3.language = :l 
                            WHERE unixepoch(match.datetime) <= unixepoch(:now) {date_filter}
                            ORDER BY match.datetime DESC, UPPER(bet_user.username)'''
    
    date_filter = 'AND date(match.datetime) = :date' if date != '' else ''
    match_query_string = text(match_query_string.format(date_filter=date_filter))
    
    hit_map = current_app.config['BONUS_MULTIPLIERS']
    match_result = get_db().session.execute(match_query_string, {'date' : date, 'now' : time_handler.get_now_time_string_with_seconds(), 'l' : session['language'], 'bullseye' : hit_map['bullseye'], 'difference' : hit_map['difference']})
    matches = match_result.fetchall()

    deletable_keys = ['odd1', 'oddX', 'odd2', 'round', 'team1', 'team2', 'goal1', 'goal2', 'id']

    result_matches = []
    for match in matches:
        match_dict = match._asdict()

        current_match = None

        for m in result_matches:
            if m['match']['id'] == match.id:
                current_match = m
                break

        if current_match is None:
            current_match = {'match': match_dict.copy(), 'players': [], 'success': 0} 
            result_matches.append(current_match)
        
        for key in deletable_keys:
            del match_dict[key]

        current_match['success'] += match_dict['success'] if match_dict['success'] is not None else 0
        current_match['players'].append(match_dict)

    return result_matches
