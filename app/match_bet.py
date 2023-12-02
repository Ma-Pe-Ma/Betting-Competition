from flask import Blueprint
from flask import redirect
from flask import g
from flask import flash
from flask import render_template
from flask import request
from flask import url_for

from app.auth import login_required
from app.db import get_db

from datetime import datetime, time
from app.configuration import configuration

from app.tools import time_determiner

import datetime
from dateutil import tz

from enum import Enum

from sqlalchemy import text

bp = Blueprint('match', __name__, '''url_prefix="/match"''')

MatchState = Enum('MatchState', 'invalid started nonstarted')

def get_match_bet(match_id, username) -> dict:
    utc_now = time_determiner.get_now_time_object()

    try:
        match_id = int(match_id)
    except:
        return {'state' : MatchState.invalid, 'match' : None}

    query_string = text('SELECT team1, team2, odd1, oddX, odd2, time, round, max_bet, id FROM match WHERE id=:match_id')
    result = get_db().session.execute(query_string, {'match_id' : match_id})
    match_from_db = result.fetchone()       

    if match_from_db is None:
        return {'state' :  MatchState.invalid, 'match' : None}        

    match_time_utc = time_determiner.parse_datetime_string(match_from_db.time)

    # check if match time is before now if yes redirect to homepage
    if match_time_utc < utc_now:
        return {'state' : MatchState.started, 'match' : None}

    #determine local time objects
    match_time_local : datetime = match_time_utc.astimezone(g.user['tz'])
    match_date_string : str = match_time_local.strftime('%Y-%m-%d')
    match_time_string : str = match_time_local.strftime('%H:%M')

    # get user bet (if exists)
    query_string = text('SELECT goal1, goal2, bet FROM match_bet WHERE username=:u AND match_id = :m')
    result0 = get_db().session.execute(query_string, {'u' : username, 'm' : match_id})
    user_match_bet = result0.fetchone()

    query_string = text('SELECT translation FROM team_translation WHERE name=:teamname AND language=:language')
    
    result1 = get_db().session.execute(query_string, {'teamname' : match_from_db.team1, 'language' : g.user['language']})
    team1_local = result1.fetchone()
    
    result2 = get_db().session.execute(query_string, {'teamname' : match_from_db.team2, 'language' : g.user['language']})
    team2_local = result2.fetchone()

    if team1_local is None or team2_local is None:
        return {'state' : MatchState.invalid, 'match' : None}

    match_dict = match_from_db._asdict()
    match_dict['team1'] = team1_local.translation
    match_dict['team2'] = team2_local.translation
    match_dict['date'] = match_date_string
    match_dict['time'] = match_time_string
    match_dict['day_id'] = match_time_local.weekday()
    match_dict['goal1'] = user_match_bet.goal1 if user_match_bet else ""
    match_dict['goal2'] = user_match_bet.goal2 if user_match_bet else ""
    match_dict['bet'] = user_match_bet.bet if user_match_bet is not None else 0    

    return  {'state' : MatchState.nonstarted, 'match' : match_dict}

@bp.route('/match', methods=('GET', 'POST'))
@login_required
def match_bet():
    username = g.user['username']

    if request.method == 'GET':
        match_id = request.args.get('matchID')
        match_bet_dict : dict = get_match_bet(match_id=match_id, username=username)

        if match_bet_dict['state'] == MatchState.invalid:
            return redirect(url_for('home.homepage', match_state='invalid'))
        elif match_bet_dict['state'] == MatchState.started:
            return redirect(url_for('home.homepage', match_state='started', match_id = match_id))
        
        return render_template('/match-bet.html', match=match_bet_dict['match'])

    elif request.method == 'POST':
        match_id = request.form['matchID']
        goal1 = request.form['goal1']
        goal2 = request.form['goal2']
        bet = request.form['bet']

        match_bet_dict = get_match_bet(match_id=match_id, username=username)

        if match_bet_dict['state'] == MatchState.invalid:
            return redirect(url_for('home.homepage', match_state='invalid'))
        elif match_bet_dict['state'] == MatchState.started:
            return redirect(url_for('home.homepage', match_state='started', match_id = match_id))

        try:
            bet_number = int(bet)

            # handle if player tries to cheat
            if bet_number > match_bet_dict['match'].max_bet:
                bet_number = match_bet_dict['match'].max_bet
            elif bet_number < 0:
                bet_number = 0

        except ValueError:
            flash('invalid_bet')
            return render_template('/match-bet.html', match=match_bet_dict['match'])

        try:
            goal1_number = int(goal1)
            goal2_number = int(goal2)
        except ValueError:
            flash('invalid_goal')
            match_bet_dict['match']['bet'] = bet_number
            return render_template('/match-bet.html', match=match_bet_dict)

        query_string = text('SELECT * FROM match_bet WHERE match_id=:match_id AND username=:username')
        result = get_db().session.execute(query_string, {'match_id' : match_id , 'username' : username})
        # rude solution if entry not exists create it it does then update
        if result.fetchone() is None:
            query_string = text('INSERT INTO match_bet (match_id, username, bet, goal1, goal2) VALUES(:m,:u,:b,:g1,:g2)')
            get_db().session.execute(query_string, {'m' : match_id, 'u' : username, 'b' : bet_number, 'g1' : goal1_number, 'g2' : goal2_number})
        else:
            query_string = text('UPDATE match_bet SET bet = :b, goal1 = :g1, goal2 = :g2 WHERE match_id = :m AND username = :u')
            get_db().session.execute(query_string, {'b' : bet_number, 'g1' : goal1_number, 'g2' : goal2_number, 'm' : match_id, 'u' : username})

        get_db().session.commit()

        return redirect(url_for('home.homepage', match_state = 'nonstarted', match_id=match_id))