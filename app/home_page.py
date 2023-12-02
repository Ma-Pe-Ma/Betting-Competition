from flask import Blueprint
from flask import g
from flask import flash
from flask import render_template
from flask import request, jsonify
from app.db import get_db
from app.auth import login_required

from dateutil import tz
from datetime import datetime, timedelta

from markdown import markdown

from app.tools.group_calculator import get_tournament_bet
from app.tools.score_calculator import get_current_points_by_player
from app.tools import time_determiner

from app.configuration import configuration

from sqlalchemy import text

bp = Blueprint('home', __name__, '''url_prefix="/"''')

@bp.route('/', methods=('GET',))
@login_required
def homepage():
    # successful match bet set (after redirecting)
    match_id = request.args.get('match_id')
    match_state = request.args.get('match_state')

    # show messages for user!    
    query_string = text('SELECT * FROM messages')
    result = get_db().session.execute(query_string)

    for row in result.fetchall():
        if row.message is not None and row.message != '':
            flash(row.message)

    # list future matches with set bets
    days = []
    query_string = text('SELECT * FROM match WHERE unixepoch(time) > unixepoch(:now)')
    result = get_db().session.execute(query_string, {'now' : time_determiner.get_now_time_string()})

    for match in result.fetchall():
        # datetime object holding the match's current utc time
        match_time_utc : datetime = time_determiner.parse_datetime_string(match.time)
        
        # datetime object holding the correct time adjusted to timezone
        match_time_local : datetime = match_time_utc.astimezone(g.user['tz'])   

        # the local time's date string
        match_date_string : str = match_time_local.strftime('%Y-%m-%d')
        # the local time's time string
        match_time_string : str = match_time_local.strftime('%H:%M')        

        # get user's earlier bet
        query_string = text('SELECT * FROM match_bet WHERE (username = :username AND match_id = :id)')
        result0 = get_db().session.execute(query_string, {'username' : g.user['username'], 'id' : match.id})
        match_bet = result0.fetchone()

        # get the translation for the team names
        query_string = text('SELECT translation FROM team_translation WHERE name=:teamname AND language=:language')

        result1 = get_db().session.execute(query_string, { 'teamname' : match.team1, 'language' : g.user['language']})
        team1_local = result1.fetchone()
        
        result2 = get_db().session.execute(query_string, {'teamname' : match.team2, 'language' : g.user['language']})
        team2_local = result2.fetchone()

        if team1_local is None or team2_local is None or team1_local.translation == '' or team2_local.translation == '':
            continue

        # convert db data to dict and add bet properties for template
        match_dict : dict = match._asdict()
        match_dict['time'] = match_time_string
        match_dict['bet'] = match_bet.bet if match_bet else ''
        match_dict['goal1'] = match_bet.goal1 if match_bet else ''
        match_dict['goal2'] = match_bet.goal2 if match_bet else ''
        match_dict['team1'] = team1_local.translation
        match_dict['team2'] = team2_local.translation

        # found the day object of the match if it doesn't exist create it
        match_day = None
        for day in days:
            if day['date'] == match_date_string:
                match_day = day

        if match_day == None:
            match_day : dict = {'number' : 0, 'date' : match_date_string, 'id' : match_time_local.weekday(), 'matches' : []}
            days.append(match_day) 

        # add the match to its day
        match_day['matches'].append(match_dict)

    # order the day by date
    days.sort(key=lambda day : datetime.strptime(day['date'], '%Y-%m-%d'))
    
    # add index to days and order matches
    for i, day in enumerate(days):
        day['number'] = i
        day['matches'].sort(key=lambda match : datetime.strptime(match['time'], '%H:%M'))

    # determine the current credit of the player
    current_amount = get_current_points_by_player(g.user['username'])

    tournament_bet_dict : dict = get_tournament_bet(username=g.user['username'], language=g.user['language'])

    # if there's a final result then display it on a new day
    if tournament_bet_dict is not None and tournament_bet_dict['success'] is not None:
        if tournament_bet_dict['success'] == 1:
            current_amount += tournament_bet_dict['betting_amount'] * tournament_bet_dict['multiplier']
        elif tournament_bet_dict['success'] == 2:
            pass

    return render_template('/home-page.html', days=days, current_amount=current_amount, match_id=match_id, match_state=match_state)

def get_comments(datetime_object : datetime, newer_comments : bool) -> list:
    datetime_string = datetime_object.strftime('%Y-%m-%d %H:%M:%S')

    comment_list = []

    # get the newer/older comments relateive to the given date
    if newer_comments:
        query_string = text('SELECT username, datetime, content FROM comment WHERE unixepoch(datetime) > unixepoch(:datetime) ORDER BY unixepoch(datetime) ASC')
        result = get_db().session.execute(query_string, {'datetime' : datetime_string})
        comments = result.fetchall()
    else:
        query_string = text('SELECT username, datetime, content FROM comment WHERE unixepoch(datetime) < unixepoch(:datetime) ORDER BY unixepoch(datetime) DESC')
        result = get_db().session.execute(query_string, {'datetime' : datetime_string})
        comments = result.fetchall()[0:10]

    # create the comment objects for the client
    for item in comments:
        comment_object : dict = {}
        
        # convert comment utc timestamp to user's local
        datetime_object = datetime.strptime(item.datetime, '%Y-%m-%d %H:%M:%S')
        datetime_object = datetime_object.replace(tzinfo=tz.gettz('UTC'))
        local_datetime_object = datetime_object.astimezone(g.user['tz'])

        comment_object['datetime'] = local_datetime_object.strftime('%Y-%m-%d %H:%M:%S')
        comment_object['user'] = item.username
        comment_object['comment'] = markdown(item.content)

        comment_list.append(comment_object)

    return comment_list

# this method handles getting abd posting messages
@bp.route('/comment', methods=('POST',))
@login_required
def comments():
    request_object : dict = request.get_json()
    
    # this field determines if newer or older comments are needed to be loaded
    newer_comments : bool = request_object['newerComments']    
    # this field holds the relative date, the sendable comment's time value needed to be next to this datetime
    datetime_string : str = request_object['datetime']

    # determine the proper date object from the posted string
    if datetime_string is not None and datetime_string != "":
        try:
            datetime_object : datetime = time_determiner.parse_datetime_string_with_seconds(datetime_string)
            datetime_object = datetime_object.replace(tzinfo=g.user['tz']).astimezone(tz=tz.gettz('UTC'))            
        except:
            response_object = {}
            response_object['STATUS'] = 'INVALID_DATA'
            return jsonify(response_object)
    else:
        datetime_object = time_determiner.get_now_time_object() + timedelta(seconds=1)
        newer_comments = False

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
    
    response_object['comments'] = get_comments(datetime_object, newer_comments)
    response_object['STATUS'] = 'OK'

    return jsonify(response_object)