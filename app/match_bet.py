from flask import Blueprint
from flask import g
from flask import request
from flask import jsonify
from flask import flash

from app.auth import sign_in_required
from app.tools.db_handler import get_db

from app.tools import time_handler

from sqlalchemy import text
from flask_babel import gettext

bp = Blueprint('match', __name__, '''url_prefix="/match"''')

@bp.route('/match', methods=('GET', 'POST'))
@sign_in_required()
def match_bet():
    try:
        match_id = request.args.get('matchID') if request.method == 'GET' else request.get_json()['id']
    except:
        match_id = None

    query_string = text("SELECT match_state.*, match_bet.bet, match_bet.goal1, match_bet.goal2 "
                        "FROM bet_user "
                        "LEFT JOIN ("
                            "SELECT match.id, ROUND(match.odd1, 2) AS odd1, ROUND(match.oddX, 2) AS oddX, ROUND(match.odd2, 2) AS odd2, match.round, match.max_bet, "
                                "tr1.translation AS team1, tr2.translation AS team2, match.datetime, (strftime('%w', match.datetime) + 6) % 7 AS weekday, "
                                "(unixepoch(:now) > unixepoch(match.datetime)) as started "
                            "FROM match "
                            "LEFT JOIN team_translation AS tr1 ON tr1.name = match.team1 AND tr1.language = :l "
                            "LEFT JOIN team_translation AS tr2 ON tr2.name = match.team2 AND tr2.language = :l "
                            "WHERE match.id = :match_id"
                        ") AS match_state ON match_state.id = :match_id "
                        "LEFT JOIN match_bet ON match_bet.username = bet_user.username AND match_bet.match_id = :match_id "
                        "WHERE bet_user.username = :u ")

    result = get_db().session.execute(query_string, {'match_id' : match_id, 'now' : time_handler.get_now_time_string(), 'u' : g.user['username'], 'l' : g.user['language']})
    match_from_db = result.fetchone()._asdict()
    match_from_db['date'], match_from_db['time'] = time_handler.local_date_time_from_utc(match_from_db['datetime'], g.user['timezone'])

    if 'started' not in match_from_db or match_from_db['started'] == None:
        return gettext(u'Match does not exist with the following id: %(id)s!', id=match_id), 400

    if match_from_db['started'] > 0:
        return gettext(u'Match %(id)s has already started!', id=match_from_db['id']), 400

    if request.method == 'GET':
        return jsonify(match_from_db), 200

    if request.method == 'POST':
        parameters = request.get_json()

        try:
            bet_value = max(0, min(int(parameters['bet']), match_from_db['max_bet']))
            goal1 = int(parameters['goal1'])
            goal2 = int(parameters['goal2'])
        except (ValueError, KeyError) as error:
            return gettext('Invalid input for goal or credit!'), 400
        
        if goal1 < 0 or goal2 < 0 or bet_value <= 0:
            return gettext('Invalid value (negative) for goal or credit!'), 400

        query_string = text("INSERT OR REPLACE INTO match_bet (match_id, username, bet, goal1, goal2) VALUES(:m, :u, :b, :g1, :g2)")
        get_db().session.execute(query_string, {'m' : match_id, 'u' : g.user['username'], 'b' : bet_value, 'g1' : goal1, 'g2' : goal2})
        get_db().session.commit()

        flash(gettext(u'Betting on match %(id)s was successful!', id=match_from_db['id']), 'success')

        return {}, 200
