from flask import Blueprint
from flask import g
from flask import render_template

from app.db import get_db
from app.auth import login_required
from app.tools import score_calculator 

from copy import copy
from sqlalchemy import text

bp = Blueprint('standings', __name__, '''url_prefix="/standings"''')

#@cache.cached(timeout=50, key_prefix='player_history')
def create_player_history():
    players = []

    #iterate through users
    query_string = text('SELECT username FROM bet_user')
    result = get_db().session.execute(query_string)

    for player in result.fetchall():
        username = player.username
        days = score_calculator.get_daily_points_by_current_time(username)
        players.append({'username' : username, 'days' : days})

    return players

#@cache.cached(timeout=50, key_prefix='standings')
def create_standings(language = None):
    if language is None:
        language = g.user['language']

    players = create_player_history()

    current_player_standings = [{'name' : player['username'], 'point' : player['days'][-1]['point'], 'previous_point' : player['days'][-2]['point'], 'position_diff' : 0} for player in players]

    #order the current player standings by the points
    current_player_standings.sort(key=lambda player_standing : player_standing['point'], reverse=True)

    #create previous day's standings
    previous_player_standings = copy(current_player_standings)
    previous_player_standings.sort(key=lambda prev_player_standing : prev_player_standing['previous_point'], reverse=True)

    for current_position, current_player_standing in enumerate(current_player_standings):
        position_diff = 0

        for previous_position, previous_player_standing in enumerate(previous_player_standings):
            if previous_player_standing['name'] == current_player_standing['name']:
                position_diff = - (current_position - previous_position)
                break

        current_player_standing['position_diff'] = position_diff

    previous_player_standings = None

    return (players, current_player_standings)

@bp.route('/standings', methods=('GET',))
@login_required
def standings():
    standings = create_standings()
    return render_template('/standings.html', players=standings[0], standings=standings[1])

@bp.route('/standings.json', methods=('GET',))
@login_required
def standings_json():
    import io, json
    from flask import send_file

    players = create_player_history()
    in_memory_file = io.BytesIO()
    in_memory_file.write(json.dumps(players).encode('utf8'))
    in_memory_file.seek(0)

    return send_file(in_memory_file, as_attachment=True, download_name='standings.json', mimetype='application/json')