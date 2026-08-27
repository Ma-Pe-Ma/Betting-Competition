from flask import Blueprint
from flask import g
from flask import session
from flask import current_app

from app.tools.db_handler import get_db
from app.auth import sign_in_required

from app.tools import time_handler
from app.tools import score_calculator
from app.tools import statistics

from sqlalchemy import text

bp = Blueprint('home', __name__, '''url_prefix="/"''')

@bp.route('/matches', methods=['GET'])
@sign_in_required()
def homepage():
    # list future matches with set bets
    days = []
    query_string = text("SELECT match.id, match.datetime AS datetime, match.odd1, match.oddX, match.odd2, match.max_bet, tr1.translation AS team1, tr2.translation AS team2, tr3.translation as round, "
                            "match_bet.goal1 AS bgoal1, match_bet.goal2 AS bgoal2, match_bet.bet, "
                            "date(match.local_datetime) AS date, strftime('%H:%M', match.local_datetime) AS time, (strftime('%w', match.local_datetime) + 6) % 7 AS weekday, "
                            "(CASE WHEN (tr1.translation IS NULL OR tr2.translation IS NULL) THEN 0 ELSE 1 END) AS active "
                        "FROM (SELECT match.*, time_converter(match.datetime, 'utc', :tz) AS local_datetime FROM match) AS match "
                        "LEFT JOIN team_translation AS tr1 ON tr1.name=match.team1 AND tr1.language = :l "
                        "LEFT JOIN team_translation AS tr2 ON tr2.name=match.team2 AND tr2.language = :l "
                        "LEFT JOIN team_translation AS tr3 ON tr3.name=match.round AND tr3.language = :l "
                        "LEFT JOIN match_bet ON match_bet.match_id = match.id AND match_bet.username = :u "
                        "WHERE unixepoch(match.datetime) > unixepoch(:now) "
                        "ORDER BY date ASC, time ASC")

    result = get_db().session.execute(query_string, {'now' : time_handler.get_now_time_string_with_seconds(), 'l' : session['language'], 'u' : g.user['username'], 'tz' : g.user['timezone']})

    days_query_string = text("SELECT DISTINCT date(time_converter(match.datetime, 'utc', :tz)) AS date FROM match")
    days_result = get_db().session.execute(days_query_string, {'tz' : g.user['timezone']})
    
    offset = 1
    matches = result.fetchall()

    if len(matches) > 0:
        for index, date in enumerate(days_result.fetchall()):
            if matches[0].date == date.date:
                offset = index + 1

    days = []

    for match in matches:
        match_dict : dict = match._asdict()

        current_day = None 
        for day in days: 
            if day['date'] == match_dict['date']:
                current_day = day
                break
        
        if current_day is None:
            current_day = {'date': match_dict['date'], 'weekday': match.weekday, 'matches' : [], 'number' : offset + len(days) }
            days.append(current_day)

        current_day['matches'].append(match_dict)

    return days

@bp.route('/credit', methods=['GET'])
@sign_in_required()
def credit():
    daily_point_parameters = score_calculator.get_daily_point_parameters()
    daily_point_parameters.update({'u' : g.user['username'], 'l' : session['language'], 'now' : time_handler.get_now_time_object().strftime('%Y-%m-%dT%H:%M:%SZ')})

    daily_point_query = score_calculator.get_daily_points_by_current_time_query(users=':u')
    day_result = get_db().session.execute(text(daily_point_query), daily_point_parameters)

    return {'credit' : day_result.fetchall()[-1]._asdict()['point']}    

@bp.route('/statistics', methods=['GET'])
@sign_in_required()
def get_statistics():
    return statistics.get_statistics(session['language']) if time_handler.get_now_time_object() > time_handler.parse_datetime_string(current_app.config['DEADLINE_TIMES']['tournament_end']) else {'players': [], 'matches': []}

@bp.route('/players', methods=['GET'])
@sign_in_required()
def players():
    player_query_string = text('SELECT username FROM bet_user ORDER BY UPPER(username) ASC')
    player_result = get_db().session.execute(player_query_string)
    players = player_result.fetchall()

    return [ p._asdict()['username'] for p in players ]

@bp.route('/dates', methods=['GET'])
@sign_in_required()
def results():
    date_query_string = text('SELECT date(match.datetime) AS date FROM match WHERE unixepoch(match.datetime) < unixepoch(:now) GROUP BY date(match.datetime) ORDER BY date(match.datetime) DESC')
    date_result = get_db().session.execute(date_query_string, {'now' : time_handler.get_now_time_string_with_seconds()})
    dates = date_result.fetchall()

    return [d._asdict()['date'] for d in dates]

@bp.route('/game-configuration', methods=['GET'])
def deadlines():
    return {
        'deadlineTimes' : current_app.config['DEADLINE_TIMES'],
        'betValues' : current_app.config['BET_VALUES'],
        'groupHitMap' : current_app.config['GROUP_BET_HIT_MAP'],
        'serverConfiguration' : {
            'languages' : current_app.config['SUPPORTED_LANGUAGES'],
            'pushKey': current_app.config['PUSH_KEYS']['public']
        }}
