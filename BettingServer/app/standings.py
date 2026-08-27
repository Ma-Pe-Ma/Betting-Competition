from flask import Blueprint
from flask import session

from app.tools.db_handler import get_db
from app.auth import sign_in_required
from app.tools import score_calculator 
from app.tools import time_handler

from sqlalchemy import text

bp = Blueprint('standings', __name__, '''url_prefix="/standings"''')

@bp.route('/standings', methods=['GET'])
@sign_in_required()
def standings(language = None):
    daily_point_parameters = score_calculator.get_daily_point_parameters()
    daily_point_parameters.update({'now' : time_handler.get_now_time_object().strftime('%Y-%m-%dT%H:%M:%SZ'), 'l' : session['language'] or language})

    user_query = score_calculator.get_daily_points_by_current_time_query(users='SELECT username FROM bet_user ORDER BY UPPER(username)')
    user_query = '''
            SELECT days.date, days.point, days.username, REPLACE(:s, '{email_hash}', bet_user.email_hash) AS image_path
            FROM ( ''' + user_query + ''' ) AS days
            LEFT JOIN bet_user ON bet_user.username = days.username
            ORDER BY UPPER(bet_user.username)
        '''
        
    all_user_result = get_db().session.execute(text(user_query), daily_point_parameters)

    players = []
    for user in all_user_result.fetchall():
        current_player = None

        for p in players:
            if p['username'] == user.username:
                current_player = p
                break

        if current_player is None:
            current_player = {'username' : user.username, 'imagePath' : user.image_path, 'days' : []}
            players.append(current_player)

        day_dict = user._asdict() 

        del day_dict['username']
        del day_dict['image_path']

        current_player['days'].append(day_dict)

    return players

def create_standings(language = None):
    players = standings(language)

    for player in players:
        player['point'] = player['days'][-1]['point']
        player['penultimatePoint'] = player['days'][-2]['point']

    players.sort(key=lambda x: x['penultimatePoint'], reverse=True)

    for index, pos in enumerate(players):
        pos['penultimatePosition'] = index

    players.sort(key=lambda x: x['point'], reverse=True)
    
    return players
