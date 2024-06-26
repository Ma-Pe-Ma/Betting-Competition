from flask import request, jsonify
from flask import Blueprint
from flask import g
from flask import render_template
from flask import current_app

from flask_babel import gettext
from sqlalchemy import text

from app.auth import sign_in_required
from app.tools import time_handler
from app.tools.db_handler import get_db
from app.tools.cache_handler import cache

bp = Blueprint('chat', __name__, '''url_prefix="/chat"''')

# get the newer/older comments relateive to the given date
def get_comments(utc_datetime_string : str, newer_comments : bool, timezone : str) -> list:
    r, o, s = ('>', 'ASC', '') if newer_comments else ('<', 'DESC', 'LIMIT 8')

    query_string = text("SELECT comment.username, time_converter(comment.datetime, 'utc', :tz, '%Y-%m-%d %H:%M:%S') AS datetime, content AS comment, "
                        "bet_user.email_hash AS email_hash, REPLACE(:s, '{email_hash}', bet_user.email_hash) AS image_path "
                        "FROM comment "
                        "LEFT JOIN bet_user ON comment.username = bet_user.username "
                        "WHERE unixepoch(datetime) " + r + " unixepoch(:datetime) "
                        "ORDER BY unixepoch(datetime) " + o + " " + s)

    result = get_db().session.execute(query_string, {'datetime' : utc_datetime_string, 's' : current_app.config['IDENT_URL'], 'tz' : timezone})

    return [comment._asdict() for comment in result.fetchall()]

@bp.route('/chat', methods=['GET', 'POST'])
@sign_in_required()
def chat_page():
    if request.method == 'POST':
        request_object : dict = request.get_json()

        if 'comment' in request_object:
            if len(request_object['comment']) < 4:
                return gettext('Too short message!'), 400
            try:
                now_time_string = time_handler.get_now_time_string_with_seconds()
                query_string = text('INSERT INTO comment (username, datetime, content) VALUES (:u, :d, :c)')
                get_db().session.execute(query_string, {'u' : g.user['username'], 'd' : now_time_string, 'c' : request_object['comment']})
                get_db().session.commit()
            except Exception as err:
                return gettext('Invalid data sent!'), 400

        if request_object['datetime'] is None:
            utc_date = time_handler.get_now_time_object()
        else:
            date, time = time_handler.utc_date_time_from_local(request_object['datetime'], timezone=g.user['timezone'], in_format='%Y-%m-%d %H:%M:%S', out_time_format='%H:%M:%S')
            utc_date = time_handler.parse_datetime_string_with_seconds('{date} {time}'.format(date=date, time=time))

        response_object = {
            'newerComments' : request_object['newerComments'],
            'comments' : get_comments(utc_date.strftime('%Y-%m-%d %H:%M:%S'), request_object['newerComments'], g.user['timezone'])
        }

        if 'comment' in request_object:
            name_query = text('SELECT username FROM bet_user')
            names = get_db().session.execute(name_query)

            comment_nr = cache.get('comment_nr')
            for name in names:
                if name.username not in comment_nr:
                    comment_nr[name.username] = 0
                else:
                    comment_nr[name.username] += 1
            
            comment_nr[g.user['username']] = 0
            cache.set('comment_nr', comment_nr, timeout=0)

        return jsonify(response_object), 200
    
    comment_nr = cache.get('comment_nr')
    comment_nr[g.user['username']] = 0
    cache.set('comment_nr', comment_nr, timeout=0)

    return render_template('/chat.html')
