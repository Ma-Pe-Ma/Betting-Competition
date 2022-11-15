from flask import Blueprint
from flask import g
from flask import flash
from flask import render_template
from flask import request, jsonify
from app.db import get_db
from app.auth import login_required

from dateutil import tz
from datetime import datetime, timedelta
from collections import namedtuple

from markdown import markdown

from app.tools.group_calculator import get_final_bet
from app.tools.score_calculator import get_current_points_by_player

from app.configuration import local_zone

bp = Blueprint('home', __name__, '''url_prefix="/"''')

Day = namedtuple('Day', 'number, date, id, matches')
Match = namedtuple('MATCH', 'ID, time, type, team1, team2, odd1, oddX, odd2, bet, goal1, goal2, max_bet')

@bp.route('/', methods=('GET',))
@login_required
def homepage():
    #successful match bet set (after redirecting)
    match_id = request.args.get('match_id')
    match_state = request.args.get('match_state')

    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))
    
    # show messages for user!
    cursor = get_db().cursor()
    cursor.execute('SELECT * FROM messages',())

    for row in cursor.fetchall():
        if row['message'] is not None and row['message'] != '':
            flash(row['message'])

    days = []

    # list future matches with set bets
    cursor = get_db().cursor()
    cursor.execute('SELECT * FROM match WHERE time::timestamp > %s::timestamp', (utc_now.strftime('%Y-%m-%d %H:%M'),))

    for match in cursor.fetchall():
        match_time_utc = datetime.strptime(match['time'], '%Y-%m-%d %H:%M')
        match_time_utc = match_time_utc.replace(tzinfo=tz.gettz('UTC'))
        
        #object holding the correct time adjusted to timezone
        match_time_local = match_time_utc.astimezone(local_zone)   

        #the local time's date string
        match_date = match_time_local.strftime('%Y-%m-%d')
        #the local time's time string
        match_time = match_time_local.strftime('%H:%M')        

        #get set bet
        cursor1 = get_db().cursor()
        cursor1.execute('SELECT * FROM match_bet WHERE (username = %s AND match_id = %s)', (g.user['username'], match['id']))
        match_bet = cursor1.fetchone()

        bet = "" if match_bet is None else match_bet['bet']
        goal1 = "" if match_bet is None else match_bet['goal1']
        goal2 = "" if match_bet is None else match_bet['goal2']

        cursor2 = get_db().cursor()
        cursor2.execute('SELECT translation FROM team_translation WHERE name=%s AND language=%s', (match['team1'], g.user['language']))
        team1_local = cursor2.fetchone()

        cursor3 = get_db().cursor()
        cursor3.execute('SELECT translation FROM team_translation WHERE name=%s AND language=%s', (match['team2'], g.user['language']))
        team2_local = cursor3.fetchone()

        if team1_local is None or team2_local is None or team1_local['translation'] == '' or team2_local['translation'] == '':
            continue

        odd1 = '-' if match['odd1'] is None else match['odd1']
        odd2 = '-' if match['odd2'] is None else match['odd2']
        oddX = '-' if match['oddx'] is None else match['oddx']

        match_object = Match(ID=match['id'], time=match_time, type=match['round'], team1=team1_local['translation'], team2=team2_local['translation'], odd1=odd1, oddX=oddX, odd2=odd2, bet=bet, goal1=goal1, goal2=goal2, max_bet=match['max_bet'])

        # found the day object of the match if it doesn't exist create it
        match_day = None
        for day in days:
            if day.date == match_date:
                match_day = day

        if match_day == None:
            match_day = Day(number = 0, date=match_date, id=match_time_local.weekday(), matches=[])
            days.append(match_day) 

        # add the match to its day
        match_day.matches.append(match_object)

    # order the day by date
    days.sort(key=lambda day : datetime.strptime(day.date, '%Y-%m-%d'))
    
    modified_days = []
    # add index to days (technically copying to new modified days list)
    for i, day in enumerate(days):
        day.matches.sort(key=lambda match : datetime.strptime(match.time, '%H:%M'))
        modified_days.append(day._replace(number = i + 1))
        i += 1

    days.clear()

    # determine the current credit of the player
    current_amount = get_current_points_by_player(g.user['username'])

    final_bet_object = get_final_bet(user_name=g.user['username'], language=g.user['language'])

    # if there's a final result then display it on a new day
    if final_bet_object is not None and final_bet_object.success is not None:
        if final_bet_object.success == 1:
            current_amount += final_bet_object.betting_amount * final_bet_object.multiplier
        elif final_bet_object.success == 2:
            pass

    return render_template(g.user['language'] + '/home-page.html', days=modified_days, current_amount=current_amount,
                                                                    match_id=match_id, match_state=match_state)

def get_comments(datetime_object, newer_comments):
    comments_object = []

    cursor = get_db().cursor()

    if newer_comments:
        cursor.execute('SELECT username, datetime, content FROM comment WHERE datetime::timestamp > %s::timestamp ORDER BY id ASC', (datetime.strftime(datetime_object, '%Y-%m-%d %H:%M:%S'),))
        comments = cursor.fetchall()
    else:
        cursor.execute('SELECT username, datetime, content FROM comment WHERE datetime::timestamp < %s::timestamp ORDER BY id DESC', (datetime.strftime(datetime_object, '%Y-%m-%d %H:%M:%S'),))
        comments = cursor.fetchall()[0:10]

    for item in comments:
        comment_object = {}

        date_object = datetime.strptime(item['datetime'], '%Y-%m-%d %H:%M:%S')
        date_object = date_object.replace(tzinfo=tz.gettz('UTC'))
        local_date_object = date_object.astimezone(local_zone)

        comment_object['datetime'] = local_date_object.strftime('%Y-%m-%d %H:%M:%S')
        comment_object['user'] = item['username']
        comment_object['comment'] = markdown(item['content'])

        comments_object.append(comment_object)

    return comments_object

@bp.route('/comment', methods=('POST',))
@login_required
def comments():
    utc_now = datetime.utcnow()
    #utc_now = datetime.strptime('2022-11-22 8:00', '%Y-%m-%d %H:%M')
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))

    request_object = request.get_json()

    newer_comments = request_object['newerComments']
    date_time_string = request_object['datetime']

    if date_time_string is not None and date_time_string != "":
        try:
            date_time_object = datetime.strptime(date_time_string, '%Y-%m-%d %H:%M:%S')
            date_time_object = date_time_object.replace(tzinfo=local_zone)
            date_time_object = date_time_object.astimezone(tz=tz.gettz('UTC'))
        except:
            response_object = {}
            response_object['STATUS'] = 'INVALID_DATA'
            return jsonify(response_object)
    else:
        date_time_object = utc_now + timedelta(seconds=1)
        newer_comments = False

    response_object = {}
    response_object['newerComments'] = newer_comments

    if 'comment' in request_object:
        if len(request_object['comment']) < 4:
            response_object = {}
            response_object['STATUS'] = 'SHORT_MESSAGE'
            return jsonify(response_object)
        try :
            get_db().cursor().execute('INSERT INTO comment (username, datetime, content) VALUES (%s, %s, %s)',(g.user['username'], utc_now.strftime('%Y-%m-%d %H:%M:%S'), request_object['comment']))
            get_db().commit()
        except:
            response_object = {}
            response_object['STATUS'] = 'INVALID_DATA'
            return jsonify(response_object)
    
    response_object['comments'] = get_comments(date_time_object, newer_comments)
    response_object['STATUS'] = 'OK'

    return jsonify(response_object)