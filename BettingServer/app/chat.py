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
@bp.route('/chat', methods=['GET'])
def get_chat():
    datetime = request.args.get('datetime')
    age = '>' if request.args.get('age') == '>' else '<'

    if datetime is None:
        utc_date = time_handler.get_now_time_object()
    else:
        utc_date = time_handler.parse_datetime_string(datetime)

    o, s = ('ASC', '') if age == '>' else ('DESC', 'LIMIT 8')

    query_string = text("SELECT comment.username, comment.datetime AS datetime, content AS comment, "
                        "bet_user.email_hash AS email_hash, REPLACE(:s, '{email_hash}', bet_user.email_hash) AS image_path "
                        "FROM comment "
                        "LEFT JOIN bet_user ON comment.username = bet_user.username "
                        "WHERE unixepoch(datetime) " + age + " unixepoch(:datetime) "
                        "ORDER BY unixepoch(datetime) " + o + " " + s) 

    result = get_db().session.execute(query_string, {'datetime' : utc_date.strftime('%Y-%m-%dT%H:%M:%SZ'), 's' : current_app.config['IDENT_URL'], 'tz' : g.user['timezone']})

    comment_nr = cache.get('comment_nr')
    comment_nr[g.user['username']] = 0
    cache.set('comment_nr', comment_nr, timeout=0)

    return [comment._asdict() for comment in result.fetchall()]

@bp.route('/chat-add', methods=['POST'])
@sign_in_required()
def chat_page():
    message : dict = request.get_json()

    if len(message['comment']) < 4:
        return gettext('Too short message!'), 400
    try:
        now_time_string = time_handler.get_now_time_string_with_seconds()
        query_string = text('INSERT INTO comment (username, datetime, content) VALUES (:u, :d, :c)')
        get_db().session.execute(query_string, {'u' : g.user['username'], 'd' : now_time_string, 'c' : message['comment']})
        get_db().session.commit()
    except Exception as err:
        return gettext('Invalid data sent!'), 400

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

    return gettext('Comment posted successfully!'), 200
