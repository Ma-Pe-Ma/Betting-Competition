from flask import request, jsonify
from flask import Blueprint
from flask import g
from flask import render_template

from sqlalchemy import text

from app.auth import login_required
from app.tools import time_determiner
from app.db import get_db

from datetime import timedelta
from flask_babel import gettext

bp = Blueprint('chat', __name__, '''url_prefix="/chat"''')

# get the newer/older comments relateive to the given date
def get_comments(utc_datetime_string : str, newer_comments : bool, timezone : str) -> list:
    if newer_comments:
        r, o, s = ">", 'ASC', None
    else:
        r, o, s = "<", 'DESC', 10

    query_string = text("SELECT username, strftime('%Y-%m-%d %H:%M:%S', datetime(comment.datetime || :tz)) AS datetime, content AS comment "
                        "FROM comment "
                        "WHERE unixepoch(datetime) " + r + " unixepoch(:datetime) "
                        "ORDER BY unixepoch(datetime) " + o)

    result = get_db().session.execute(query_string, {'datetime' : utc_datetime_string, 'tz' : timezone})
    comments = result.fetchall()[0:s]

    return [comment._asdict() for comment in comments]

# this method handles getting abd posting messages
@bp.route('/comment', methods=('POST',))
@login_required
def comments():
    request_object : dict = request.get_json()

    if 'comment' in request_object:
        if len(request_object['comment']) < 4:
            return gettext('Too short message!'), 400
        try:
            now_time_string = time_determiner.get_now_time_string_with_seconds()
            query_string = text('INSERT INTO comment (username, datetime, content) VALUES (:u, :d, :c)')
            get_db().session.execute(query_string, {'u' : g.user['username'], 'd' : now_time_string, 'c' : request_object['comment']})
            get_db().session.commit()
        except Exception as err:
            return gettext('Invalid data sent!'), 400

    if request_object['datetime'] is None:
        utc_date = time_determiner.get_now_time_object()
    else:
        utc_date = time_determiner.parse_datetime_string_with_seconds(request_object['datetime']) + timedelta(hours=int(g.user['timezone'][:3]), minutes=int(g.user['timezone'][4:]))

    response_object = {
        'newerComments' : request_object['newerComments'],
        'comments' : get_comments(utc_date.strftime('%Y-%m-%d %H:%M:%S'), request_object['newerComments'], g.user['timezone'])
    }

    return jsonify(response_object), 200

@bp.route('/chat', methods=('GET',))
@login_required
def chat_page():
    return render_template('/chat.html')