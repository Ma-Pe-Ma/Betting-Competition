from flask import Blueprint
from flask import g
from flask import render_template

from app.tools.db_handler import get_db
from app.auth import sign_in_required
from app.tools import score_calculator 
from app.tools import time_handler
from app.tools.cache_handler import cache

from sqlalchemy import text

bp = Blueprint('standings', __name__, '''url_prefix="/standings"''')

cache_time = 5

def create_player_history(select='*', group_by='', order_by=''):
    user_query = score_calculator.get_daily_points_by_current_time_query(user_filter='', users='SELECT username FROM bet_user ORDER BY UPPER(username)')
    user_query = '''WITH days AS (
                        SELECT days.*, 
                        LAST_VALUE(point) OVER (PARTITION BY days.username) AS last_point,
	                    LAST_VALUE(penultimate) OVER (PARTITION BY days.username) AS penultimate_point            
                        FROM (''' + user_query + ''') AS days)
        
        SELECT {select}, (penultimate_pos - position) AS position_diff
        FROM (SELECT days1.date, days1.year, days1.month, days1.day, days1.point, days1.username, days1.point, days1.penultimate, penultimate_point, last_point,
            REPLACE(:s, '{{email_hash}}', bet_user.email_hash) AS image_path, 
            (SELECT COUNT(DISTINCT last_point) FROM days AS days2 WHERE days2.last_point >= days1.last_point) AS position,
            (SELECT COUNT(DISTINCT penultimate_point) FROM days AS days3 WHERE days3.penultimate_point >= days1.penultimate_point) AS penultimate_pos
            FROM days AS days1
            LEFT JOIN bet_user ON bet_user.username = days1.username)
        {group_by}
        {order_by}
        '''.format(select=select, group_by=group_by, order_by=order_by)
    return user_query

@cache.cached(timeout=cache_time, key_prefix='standings')
def create_standings(language = None):
    daily_point_parameters = score_calculator.get_daily_point_parameters()
    daily_point_parameters.update({'now' : time_handler.get_now_time_object().strftime('%Y-%m-%d %H:%M'), 'l' : language or g.user['language']})

    user_query = create_player_history(select='username, image_path, last_point, penultimate_point', group_by='GROUP BY username', order_by='ORDER BY position')
    all_user_result = get_db().session.execute(text(user_query), daily_point_parameters)

    return [user._asdict() for user in all_user_result.fetchall()]

@bp.route('/standings', methods=['GET'])
@sign_in_required()
def standings():
    return render_template('/standings.html', standings=create_standings())

@bp.route('/standings.json', methods=['GET'])
@sign_in_required()
def standings_json():
    daily_point_parameters = score_calculator.get_daily_point_parameters()
    daily_point_parameters.update({'now' : time_handler.get_now_time_object().strftime('%Y-%m-%d %H:%M'), 'l' : g.user['language']})

    user_query = create_player_history(select='username, image_path, date, year, month, day, point', group_by='', order_by='ORDER BY UPPER(username)')
    all_user_result = get_db().session.execute(text(user_query), daily_point_parameters)

    players = {}
    for user in all_user_result.fetchall():
        if user.username not in players:
            players[user.username] = {'username' : user.username, 'image_path' : user.image_path, 'days' : []}

        day_dict = user._asdict()
        del day_dict['username']
        del day_dict['image_path']
        players[user.username]['days'].append(day_dict)

    import io, json
    from flask import send_file

    in_memory_file = io.BytesIO()
    in_memory_file.write(json.dumps(list(players.values())).encode('utf8'))
    in_memory_file.seek(0)

    return send_file(in_memory_file, as_attachment=True, download_name='standings.json', mimetype='application/json')
