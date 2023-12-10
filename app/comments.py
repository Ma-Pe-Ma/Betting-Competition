from flask import request, jsonify
from flask import Blueprint
from flask import g

from markdown import markdown
from sqlalchemy import text

from app.auth import login_required
from app.tools import time_determiner
from app.db import get_db

from datetime import datetime

bp = Blueprint('comment', __name__, '''url_prefix="/comment"''')

def get_comments(datetime_string : str, newer_comments : bool, timezone : str) -> list:
    # get the newer/older comments relateive to the given date
    if newer_comments:
        r, o, s = ">", 'ASC', -1
    else:
        r, o, s = "<", 'DESC', 10

    query_string = text("SELECT username, strftime('%Y-%m-%d %H:%M:%S', datetime(comment.datetime || :tz)) AS datetime, content AS comment "
                        "FROM comment "
                        "WHERE unixepoch(datetime) " + r + " unixepoch(COALESCE(:datetime || :tz, datetime(datetime('now'), '+1  seconds'))) "
                        "ORDER BY unixepoch(datetime) " + o)

    result = get_db().session.execute(query_string, {'datetime' : datetime_string, 'tz' : timezone})
    comments = result.fetchall()[0:s]

    # TODO: determine where to render markdown content
    comment_list = []
    # create the comment objects for the client
    for comment in comments:
        comment_dict = comment._asdict()
        #comment_dict['comment'] = markdown(comment_dict['comment'])
        comment_list.append(comment_dict)

    return comment_list

# this method handles getting abd posting messages
@bp.route('/comment', methods=('POST',))
@login_required
def comments():
    request_object : dict = request.get_json()

    # this field determines if newer or older comments are needed to be loaded
    newer_comments : bool = request_object['newerComments']

    response_object = {}
    response_object['newerComments'] = newer_comments

    # if posting a new comment
    if 'comment' in request_object:
        if len(request_object['comment']) < 4:
            response_object = {}
            response_object['STATUS'] = 'SHORT_MESSAGE'
            return jsonify(response_object), 400
        try :
            now_time_string = time_determiner.get_now_time_string_with_seconds()
            query_string = text('INSERT INTO comment (username, datetime, content) VALUES (:u, :d, :c)')
            get_db().session.execute(query_string, {'u' : g.user['username'], 'd' : now_time_string, 'c' : request_object['comment']})
            get_db().session.commit()
        except:
            # TODO Restructure error handling with 400 code properly
            response_object = {}
            response_object['STATUS'] = 'INVALID_DATA'
            return jsonify(response_object), 400
    
    response_object['comments'] = get_comments(request_object['datetime'], newer_comments, g.user['timezone'])
    response_object['STATUS'] = 'OK'

    return jsonify(response_object)