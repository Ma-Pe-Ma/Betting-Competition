from flask import Blueprint
from flask import g
from flask import session
from flask import request
from flask import jsonify

from app.auth import sign_in_required
from app.tools.db_handler import get_db

from app.tools import time_handler

from sqlalchemy import text
from flask_babel import gettext

bp = Blueprint('match', __name__, '''url_prefix="/match"''')

@bp.route('/match', methods=['GET', 'POST'])
@sign_in_required()
def match_bet():
    try:
        match_id = request.args.get('matchID') if request.method == 'GET' else request.get_json()['id']
    except:
        match_id = None

    query_string = text("SELECT match.id, ROUND(match.odd1, 2) AS odd1, ROUND(match.oddX, 2) AS oddX, ROUND(match.odd2, 2) AS odd2, match.round, match.max_bet, match.goal1, match.goal2, "
                            "tr1.translation AS team1, tr2.translation AS team2, "
                            "date(match.local_datetime) AS date, strftime('%H:%M', match.local_datetime) AS time, match.local_datetime AS datetime, (strftime('%w', match.local_datetime) + 6) % 7 AS weekday, "
                            "bet.goal1 as bgoal1, bet.goal2 as bgoal2, bet.bet as bet, "
                            "(unixepoch(:now) > unixepoch(match.datetime)) as active "
                        "FROM (SELECT match.*, time_converter(match.datetime, 'utc', :tz) AS local_datetime FROM match) AS match "
                        "LEFT JOIN team_translation AS tr1 ON tr1.name = match.team1 AND tr1.language = :l "
                        "LEFT JOIN team_translation AS tr2 ON tr2.name = match.team2 AND tr2.language = :l "
                        "LEFT JOIN (SELECT * FROM match_bet WHERE username = :u ) AS bet ON bet.match_id = match.id "
                        "WHERE match.id = :match_id")

    result = get_db().session.execute(query_string, {'match_id' : match_id, 'now' : time_handler.get_now_time_string(), 'u' : g.user['username'], 'l' : session['language'], 'tz' : g.user['timezone']})
    match_from_db = result.fetchone()._asdict()

    if 'active' not in match_from_db or match_from_db['active'] == None:
        return  {'message': gettext(u'Match does not exist with the following id: %(id)s!', id=match_id), 'type': 'danger'}, 400

    if match_from_db['active'] > 0:
        return  {'message': gettext(u'Match %(id)s has already started!', id=match_from_db['id']), 'type': 'danger'}, 400

    if request.method == 'GET':
        return jsonify(match_from_db), 200

    if request.method == 'POST':
        parameters = request.get_json()

        try:
            bet_value = max(0, min(int(parameters['bet']), match_from_db['max_bet']))
            goal1 = int(parameters['bgoal1'])
            goal2 = int(parameters['bgoal2'])
        except (ValueError, KeyError) as error:
            return {'message': gettext('Invalid input for goal or credit!'), 'type': 'danger'}, 400
        
        if goal1 < 0 or goal2 < 0 or bet_value <= 0:
            return {'message': gettext('Invalid value (negative) for goal or credit!'), 'type': 'danger'}, 400

        query_string = text("INSERT OR REPLACE INTO match_bet (match_id, username, bet, goal1, goal2) VALUES(:m, :u, :b, :g1, :g2)")
        get_db().session.execute(query_string, {'m' : match_id, 'u' : g.user['username'], 'b' : bet_value, 'g1' : goal1, 'g2' : goal2})
        get_db().session.commit()

        return {'message': gettext(u'Betting on match %(id)s was successful!', id=match_from_db['id']), 'type': 'success'}, 200
