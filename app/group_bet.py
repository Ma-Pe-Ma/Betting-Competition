from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
from flask import jsonify

from datetime import datetime

from app.auth import login_required
from app.db import get_db
from app.configuration import configuration
from app.tools.group_calculator import get_group_bet_dict_for_user, get_tournament_bet_dict_for_user
from app.tools.score_calculator import get_group_and_tournament_bet_amount

from app.tools import time_determiner

from sqlalchemy import text, bindparam

bp = Blueprint('group', __name__, '''url_prefix="/group"''')

# TODO rewrite this ugly input and error handling method
def before_deadline():
    username = g.user['username']
    language = g.user['language']

    bet_values = configuration.bet_values

    if request.method == 'GET':
        groups = get_group_bet_dict_for_user(username=username)
        tournament_bet = get_tournament_bet_dict_for_user(username=username)

        return render_template('/group-bet/group-edit.html', bet_values=bet_values, tournament_bet = tournament_bet, groups = groups)

    elif request.method == 'POST':
        bet_object = request.get_json()
        response_object = {}

        # parsing and checking final bet properties
        final = bet_object['final']

        final_team = final['team']
        query_string = text('SELECT name FROM team WHERE name = :final_team')
        result = get_db().session.execute(query_string, {'final_team' : final_team})
        if result.fetchone() is None:
            response_object['result'] = 'error'
            response_object['info'] = 'FINAL_TEAM'
        try:
            tournament_result = int(final['result'])
            if tournament_result < 0 or 3 < tournament_result:
                response_object['result'] = 'error'
                response_object['info'] = 'FINAL_RESULT'
        except ValueError:
            response_object['result'] = 'error'
            response_object['info'] = 'FINAL_RESULT'

        try:
            final['bet'] = max(0, min(int(final['bet']), bet_values.max_tournament_bet_value))

        except ValueError:
            response_object['result'] = 'error'
            response_object['info'] = 'tournament_bet'

        # parsing anc checking group properties
        groups = bet_object['group']

        for group_id in groups:
            order = groups[group_id]['order']

            # checking and trimming bet value
            try:
                groups[group_id]['bet'] = max(0, min(bet_values.max_group_bet_value, int(groups[group_id]['bet'])))
            except ValueError:
                response_object['result'] = 'error'
                response_object['info'] = 'GROUP_BET'
                break

            query_string = text('SELECT name FROM team WHERE group_id = :group_id AND name IN :names')
            query_string = query_string.bindparams(bindparam('names', expanding=True))
            result = get_db().session.execute(query_string, {'group_id' : group_id, 'names' : order})
            
            db_teams = result.fetchall()
            
            if db_teams is None or len(db_teams) != 4:
                response_object['result'] = 'error'
                response_object['info'] = 'GROUP_TEAM'
                break

            groups[group_id]['order'] = [db_team for db_team in db_teams]                        

        if bool(response_object) is not False:
            return jsonify(response_object)
        
        tournament_bet = final['bet']
        
        query_string = text("INSERT OR REPLACE INTO tournament_bet (username, bet, team, result) "
                            " VALUES(:u, :b, :t, :r)")
        get_db().session.execute(query_string, {'u' : username, 'b' : tournament_bet, 't' : final_team, 'r' : tournament_result})

        for group_id in groups:
            order = groups[group_id]['order']
            bet = groups[group_id]['bet']

            query_string = text("INSERT OR REPLACE INTO group_bet (username, group_id, bet) "
                                "VALUES (:u, :g, :b)")
            get_db().session.execute(query_string, {'u' : username, 'g' : group_id, 'b' : bet})

            for index, team in enumerate(order):
                query_string = text('INSERT OR REPLACE INTO team_bet (username, team, position) VALUES(:u, :t, :p)')
                get_db().session.execute(query_string, {'u' : username, 't' : team, 'p' : index + 1})

        get_db().session.commit()

        response_object['result'] = 'OK'
        return jsonify(response_object)

def during_groupstage():
    username = request.args.get('name')

    if username is not None:
        amount_after = configuration.bet_values.starting_bet_amount - get_group_and_tournament_bet_amount(username=username)
        groups = get_group_bet_dict_for_user(username=username)
        tournament_bet_object = get_tournament_bet_dict_for_user(username=username)

        return render_template('/group-bet/group-during.html', groups=groups, tournament_bet=tournament_bet_object, amount_after=amount_after, starting_bet_amount=configuration.bet_values.starting_bet_amount)
    
    query_string = text('SELECT username FROM bet_user ORDER BY username ASC')
    result = get_db().session.execute(query_string)
    players = result.fetchall()

    return render_template('/group-bet/group-choose.html', players=players)

def after_evaluation():
    username = request.args.get('name')

    if username is not None:
        total_group_bet = get_group_and_tournament_bet_amount(username=username)
        tournament_bet_dict = get_tournament_bet_dict_for_user(username=username)
        groups = get_group_bet_dict_for_user(username=username)
        total_win_amount = sum(group['prize'] for group in groups.values())

        return render_template('/group-bet/group-after.html', groups=groups, total_bet=total_group_bet, total_win=total_win_amount, tournament_bet=tournament_bet_dict)
    
    query_string = text('SELECT username FROM bet_user')
    result = get_db().session.execute(query_string)
    players = result.fetchall()

    return render_template('/group-bet/group-choose.html', players=players)

@bp.route('/group', methods=('GET', 'POST'))
@login_required
def group_order():
    deadline_times = configuration.deadline_times

    utc_now : datetime = time_determiner.get_now_time_object()
    register_time : datetime = time_determiner.parse_datetime_string(deadline_times.register)
    group_evaluation_time_object : datetime = time_determiner.parse_datetime_string(deadline_times.group_evaluation)

    if utc_now < register_time:
        return before_deadline()
    elif utc_now < group_evaluation_time_object:
        return during_groupstage()
    else:
        return after_evaluation()

@bp.route('/final-odds', methods=('GET',))
@login_required
def tournament_bet_odds():
    teams = []

    query_string = text("SELECT top1, top2, top4, top16, tr.translation AS name "
                        "FROM team "
                        "INNER JOIN team_translation AS tr ON tr.name = team.name AND tr.language = :l ")
    result = get_db().session.execute(query_string, {'l' : g.user['language']})

    for team in result.fetchall():
        teams.append(team._asdict())

    return render_template('/group-bet/final-odds.html', teams=teams)