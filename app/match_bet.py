from flask import Blueprint
from flask import redirect
from flask import g
from flask import flash
from flask import render_template
from flask import request
from flask import url_for

from app.auth import login_required
from app.db import get_db

bp = Blueprint('match', __name__, '''url_prefix="/match"''')

import datetime
from dateutil import tz

from collections import namedtuple
from enum import Enum

Match = namedtuple('Match', 'ID, team1, team2, odd1, oddX, odd2, date, time, day_id, type, goal1, goal2, bet, max_bet')
MatchContainer = namedtuple('MatchContainer', 'state, match')
MatchState = Enum('MatchState', 'invalid started nonstarted')

from datetime import datetime, time
from app.configuration import configuration

def get_match_bet(match_id, user_name):
    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))
    local_zone =  tz.gettz(configuration.local_zone)

    try:
        match_id = int(match_id)
    except:
        return MatchContainer(state=MatchState.invalid, match=None)

    cursor = get_db().cursor()
    cursor.execute('SELECT team1, team2, odd1, oddX, odd2, time, round, max_bet FROM match WHERE id=%s', (match_id,))
    match_from_db = cursor.fetchone()       

    if match_from_db is None:
        return MatchContainer(state=MatchState.invalid, match=None)        

    match_time_utc = datetime.strptime(match_from_db['time'], '%Y-%m-%d %H:%M')
    match_time_utc = match_time_utc.replace(tzinfo=tz.gettz('UTC'))

    # check if match time is before now if yes redirect to homepage
    if match_time_utc < utc_now:
        return MatchContainer(state=MatchState.started, match=None)        

    #determine local time objects
    match_time_local = match_time_utc.astimezone(local_zone)
    match_date = match_time_local.strftime('%Y-%m-%d')
    match_time = match_time_local.strftime('%H:%M')        

    #description strings on client
    typeString = match_from_db['round']

    # get user bet (if exists)
    cursor0 = get_db().cursor()
    cursor0.execute('SELECT goal1, goal2, bet FROM match_bet WHERE username=%s AND match_id = %s', (user_name, match_id))
    user_match_bet = cursor0.fetchone()

    cursor1 = get_db().cursor()
    cursor1.execute('SELECT translation FROM team_translation WHERE name=%s AND language=%s', (match_from_db['team1'], g.user['language']))
    team1_local = cursor1.fetchone()
    
    cursor2 = get_db().cursor()
    cursor2.execute('SELECT translation FROM team_translation WHERE name=%s AND language=%s', (match_from_db['team2'], g.user['language']))
    team2_local = cursor2.fetchone()

    if team1_local is None or team2_local is None:
        return MatchContainer(state=MatchState.invalid, match=None)        

    goal1 = user_match_bet['goal1'] if user_match_bet is not None else ""
    goal2 = user_match_bet['goal2'] if user_match_bet is not None else ""
    bet = user_match_bet['bet'] if user_match_bet is not None else 0

    match = Match(ID=match_id, team1=team1_local['translation'], team2=team2_local['translation'],
                    odd1=match_from_db['odd1'], oddX=match_from_db['oddx'], odd2=match_from_db['odd2'],
                    date=match_date, time=match_time, day_id=match_time_local.weekday(), type=typeString,
                    goal1 = goal1, goal2 = goal2, bet=bet, max_bet=match_from_db['max_bet'])
    return  MatchContainer(state=MatchState.nonstarted, match=match)

@bp.route('/match', methods=('GET', 'POST'))
@login_required
def match_bet():
    user_name = g.user['username']

    if request.method == 'GET':
        match_id = request.args.get('matchID')
        match_bet_object = get_match_bet(match_id=match_id, user_name=user_name)

        if match_bet_object.state == MatchState.invalid:
            return redirect(url_for('home.homepage', match_state='invalid'))
        elif match_bet_object.state == MatchState.started:
            return redirect(url_for('home.homepage', match_state='started', match_id = match_id))
        
        return render_template('/match-bet.html', match=match_bet_object.match)            

    elif request.method == 'POST':
        match_id = request.form['matchID']
        goal1 = request.form['goal1']
        goal2 = request.form['goal2']
        bet = request.form['bet']

        match_bet_object = get_match_bet(match_id=match_id, user_name=user_name)

        if match_bet_object.state == MatchState.invalid:
            return redirect(url_for('home.homepage', match_state='invalid'))
        elif match_bet_object.state == MatchState.started:
            return redirect(url_for('home.homepage', match_state='started', match_id = match_id))

        try:
            bet_number = int(bet)

            # handle if player tries to cheat
            if bet_number > match_bet_object.match.max_bet:
                bet_number = match_bet_object.match.max_bet
            elif bet_number < 0:
                bet_number = 0

        except ValueError:
            flash('invalid_bet')
            return render_template('/match-bet.html', match=match_bet_object.match)

        try:
            goal1_number = int(goal1)
            goal2_number = int(goal2)
        except ValueError:
            flash('invalid_goal')
            match = match_bet_object.match._replace(bet=bet_number)
            return render_template('/match-bet.html', match=match)

        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM match_bet WHERE match_id=%s AND username=%s', (match_id, user_name))

        # rude solution if entry not exists create it it does then update
        if cursor.fetchone() is None:
            get_db().cursor().execute('INSERT INTO match_bet (match_id, username, bet, goal1, goal2) VALUES(%s,%s,%s,%s,%s)', (match_id, user_name, bet_number, goal1_number, goal2_number))
        else:
            get_db().cursor().execute('UPDATE match_bet SET bet = %s, goal1 = %s, goal2 = %s WHERE match_id = %s AND username = %s', (bet_number, goal1_number, goal2_number, match_id, user_name))

        get_db().commit()

        return redirect(url_for('home.homepage', match_state = 'nonstarted', match_id=match_id))