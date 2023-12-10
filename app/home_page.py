from flask import Blueprint
from flask import g
from flask import flash
from flask import render_template
from flask import request
from app.db import get_db
from app.auth import login_required

from app.tools import time_determiner
from app.tools import score_calculator

from sqlalchemy import text
from flask_babel import gettext

bp = Blueprint('home', __name__, '''url_prefix="/"''')

# TODO create proper feedback messages
def process_arguments(args):
    feedback_messages = []

    if 'match' in args:
        if 'started' not in args['match']:
            # TODO: can this be reached?
            feedback_messages.append(gettext(u'Invalid match'))
        elif args['match']['started'] == 1:
            feedback_messages.append(gettext(u'Match with %(id) already started!', id=args['match']['id']))
        elif args['match']['started'] == 0:
            feedback_messages.append(gettext(u'Betting on match with %(id) was sucessful!', id=args['match']['id']))

    return feedback_messages

@bp.route('/', methods=('GET',))
@login_required
def homepage():
    # show messages for user!    
    query_string = text('SELECT * FROM messages')
    result = get_db().session.execute(query_string)

    for row in result.fetchall():
        if row.message is not None and row.message != '':
            flash(row.message, 'admin')

    # TODO create proper feedback responses
    #for state_message in process_arguments(request.args.to_dict()):
    #    flash(state_message, 'state')

    # list future matches with set bets
    days = []
    query_string = text("SELECT match.id, match.time AS datetime, match.round, match.odd1, match.oddX, match.odd2, match.max_bet, tr1.translation AS team1, tr2.translation AS team2, match_bet.goal1, match_bet.goal2, match_bet.bet, "
                        "date(match.time || :timezone) AS date, strftime('%H:%M', match.time || :timezone) AS time, (strftime('%w', match.time) + 6) % 7 AS weekday "
                        "FROM match "
                        "LEFT JOIN team_translation AS tr1 ON tr1.name=match.team1 AND tr1.language = :l "
                        "LEFT JOIN team_translation AS tr2 ON tr2.name=match.team2 AND tr2.language = :l "
                        "LEFT JOIN match_bet ON match_bet.match_id = match.id AND match_bet.username = :u "
                        "WHERE unixepoch(match.time) > unixepoch(:now) "
                        "ORDER BY date ASC, time ASC")
    
    result = get_db().session.execute(query_string, {'now' : time_determiner.get_now_time_string(), 'l' : g.user['language'], 'u' : g.user['username'], 'timezone' : g.user['timezone']})

    days = {}
    # TODO determine proper offset for day ID!
    offset = 1

    for match in result.fetchall():
        match_dict : dict = match._asdict()

        if match_dict['date'] not in days:
            days[match_dict['date']] = {'weekday': match.weekday, 'matches' : [match_dict], 'number' : offset + len(days) }
        else:
            days[match_dict['date']]['matches'].append(match_dict)

    amount = score_calculator.get_daily_points_by_current_time(g.user['username'])[-1]['point']

    return render_template('/home-page.html', days=days, current_amount=amount)
