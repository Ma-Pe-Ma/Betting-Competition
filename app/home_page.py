from flask import Blueprint
from flask import g
from flask import flash
from flask import render_template
from flask import request
from app.db import get_db
from app.auth import login_required

from app.tools.group_calculator import get_tournament_bet
from app.tools.score_calculator import get_current_points_by_player
from app.tools import time_determiner

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
    query_string = text("SELECT match.id, match.time AS datetime, match.round, match.odd1, match.oddX, match.odd2, match.max_bet, tr1.translation AS team1, tr2.translation AS team2, match_bet.goal1, match_bet.goal2, match_bet.bet, "
                        "date(match.time || :timezone) AS date, time(match.time || :timezone) AS time, (strftime('%w', match.time) + 6) % 7 AS weekday "
                        "FROM match "
                        "LEFT JOIN team_translation AS tr1 ON tr1.name=match.team1 AND tr1.language = :l "
                        "LEFT JOIN team_translation AS tr2 ON tr2.name=match.team2 AND tr2.language = :l "
                        "LEFT JOIN match_bet ON match_bet.match_id = match.id AND match_bet.username = :u "
                        "WHERE unixepoch(match.time) > unixepoch(:now) "
                        "ORDER BY date ASC, time ASC")
    
    result = get_db().session.execute(query_string, {'now' : time_determiner.get_now_time_string(), 'l' : g.user['language'], 'u' : g.user['username'], 'timezone' : g.user['tz_offset']})

    days = {}
    # TODO determine proper offset for day ID!
    offset = 1

    for match in result.fetchall():
        match_dict : dict = match._asdict()

        if match_dict['date'] not in days:
            days[match_dict['date']] = {'weekday': match.weekday, 'matches' : [match_dict], 'number' : offset + len(days) }
        else:
            days[match_dict['date']]['matches'].append(match_dict)

    # determine the current credit of the player
    current_amount = get_current_points_by_player(g.user['username'])

    tournament_bet_dict : dict = get_tournament_bet(g.user['username'])

    # if there's a final result then display it on a new day
    if tournament_bet_dict is not None and tournament_bet_dict['success'] is not None:
        current_amount += tournament_bet_dict['prize']

    return render_template('/home-page.html', days=days, current_amount=current_amount, match_id=match_id, match_state=match_state)
