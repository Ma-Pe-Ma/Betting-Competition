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

# TODO eliminate this bloated return dict, and return the SQL result row only!
def get_match_bet(match_id, username) -> dict:
    utc_now = time_determiner.get_now_time_object()

    try:
        match_id = int(match_id)
    except:
        return {'state' : MatchState.invalid, 'match' : None}

    query_string = text("SELECT match.odd1, match.oddX, match.odd2, match.round, match.max_bet, match.id, "
                        "tr1.translation AS team1, tr2.translation AS team2, match_bet.bet, match_bet.goal1, match_bet.goal2, "
                        "date(match.time || :timezone) AS date, strftime('%H:%M', time(match.time || :timezone)) AS time, (strftime('%w', match.time) + 6) % 7 AS weekday "
                        "FROM match "
                        "LEFT JOIN match_bet ON match_bet.match_id = match.id AND match_bet.username = :u "
                        "LEFT JOIN team_translation AS tr1 ON tr1.name = match.team1 AND tr1.language = :l "
                        "LEFT JOIN team_translation AS tr2 ON tr2.name = match.team2 AND tr2.language = :l "
                        "WHERE match.id=:match_id")
    result = get_db().session.execute(query_string, {'match_id' : match_id, 'u' : g.user['username'], 'l' : g.user['language'], 'timezone' : g.user['tz_offset']})
    match_from_db = result.fetchone()       

    if match_from_db is None:
        return {'state' :  MatchState.invalid, 'match' : None}        

    # TODO integrate this check into SQL query!
    # check if match time is before now if yes redirect to homepage
    #if match_time_utc < utc_now:
        #return {'state' : MatchState.started, 'match' : None}

    return  {'state' : MatchState.nonstarted, 'match' : match_from_db._asdict()}

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
        bet_value = request.form['bet']

        match_bet_dict = get_match_bet(match_id=match_id, username=username)

        if match_bet_dict['state'] == MatchState.invalid:
            return redirect(url_for('home.homepage', match_state='invalid'))
        elif match_bet_dict['state'] == MatchState.started:
            return redirect(url_for('home.homepage', match_state='started', match_id = match_id))

        try:
            bet_value = int(bet_value)

            # handle if player tries to cheat
            if bet_value > match_bet_dict['match'].max_bet:
                bet_value = match_bet_dict['match'].max_bet
            elif bet_value < 0:
                bet_value = 0

        except ValueError:
            flash('invalid_bet')
            return render_template('/match-bet.html', match=match_bet_dict['match'])

        try:
            goal1_number = int(goal1)
            goal2_number = int(goal2)
        except ValueError:
            flash('invalid_goal')
            match_bet_dict['match']['bet'] = bet_value
            return render_template('/match-bet.html', match=match_bet_dict)

        query_string = text('SELECT * FROM match_bet WHERE match_id=:match_id AND username=:username')
        result = get_db().session.execute(query_string, {'match_id' : match_id , 'username' : username})
        # rude solution if entry not exists create it it does then update
        if result.fetchone() is None:
            query_string = text('INSERT INTO match_bet (match_id, username, bet, goal1, goal2) VALUES(:m,:u,:b,:g1,:g2)')
            get_db().session.execute(query_string, {'m' : match_id, 'u' : username, 'b' : bet_value, 'g1' : goal1_number, 'g2' : goal2_number})
        else:
            query_string = text('UPDATE match_bet SET bet = :b, goal1 = :g1, goal2 = :g2 WHERE match_id = :m AND username = :u')
            get_db().session.execute(query_string, {'b' : bet_value, 'g1' : goal1_number, 'g2' : goal2_number, 'm' : match_id, 'u' : username})

        get_db().session.commit()

        return redirect(url_for('home.homepage', match_state = 'nonstarted', match_id=match_id))