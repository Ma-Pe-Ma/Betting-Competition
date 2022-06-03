from flask import Blueprint
from flask import g
from flask import flash
from flask import render_template
from flask import request
from app.db import get_db
from app.auth import login_required

from dateutil import tz
from datetime import datetime
from collections import namedtuple

from app.tools.group_calculator import get_final_bet
from app.tools.score_calculator import get_current_points_by_player

from app.configuration import REMARK42_URL, REMARK42_SITE_ID, local_zone

bp = Blueprint('home', __name__, '''url_prefix="/group"''')

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
        cursor2.execute('SELECT local_name FROM team WHERE (name = %s)', (match['team1'],))
        team1_local = cursor2.fetchone()

        cursor3 = get_db().cursor()
        cursor3.execute('SELECT local_name FROM team WHERE (name = %s)', (match['team2'],))
        team2_local = cursor3.fetchone()

        if team1_local is None or team2_local is None or team1_local['local_name'] == '' or team2_local['local_name'] == '':
            continue

        odd1 = '-' if match['odd1'] is None else match['odd1']
        odd2 = '-' if match['odd2'] is None else match['odd2']
        oddX = '-' if match['oddx'] is None else match['oddx']

        match_object = Match(ID=match['id'], time=match_time, type=match['round'], team1=team1_local['local_name'], team2=team2_local['local_name'], odd1=odd1, oddX=oddX, odd2=odd2, bet=bet, goal1=goal1, goal2=goal2, max_bet=match['max_bet'])

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

    final_bet_object = get_final_bet(user_name=g.user['username'],)

    # if there's a final result then display it on a new day
    if final_bet_object is not None and final_bet_object.success is not None:
        if final_bet_object.success == 1:
            current_amount += final_bet_object.betting_amount * final_bet_object.multiplier
        elif final_bet_object.success == 2:
            pass

    return render_template('home-page.html', username = g.user['username'], admin=g.user['admin'],
                                            days=modified_days, current_amount=current_amount, match_id=match_id, match_state=match_state,
                                            REMARK42_URL=REMARK42_URL, REMARK42_SITE_ID=REMARK42_SITE_ID)