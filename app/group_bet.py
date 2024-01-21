from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
from flask import jsonify
from flask import current_app

from datetime import datetime

from app.auth import sign_in_required
from app.tools.db_handler import get_db
from app.tools import group_calculator
from app.tools import score_calculator
from app.tools import time_handler

from flask_babel import gettext
from sqlalchemy import text, bindparam

bp = Blueprint('group', __name__, '''url_prefix="/group"''')

def before_deadline():
    username = g.user['username']

    bet_values = current_app.config['BET_VALUES']

    if request.method == 'GET':
        groups = group_calculator.get_group_bet_dict_for_user(username=username)
        tournament_bet = group_calculator.get_tournament_bet_dict_for_user(username=username)

        return render_template('/group-bet/group-edit.html', bet_values=bet_values, tournament_bet = tournament_bet, groups = groups)

    elif request.method == 'POST':
        bet_object = request.get_json()
        response_string = None

        # parsing and checking final bet properties
        tournament = bet_object['tournament']

        final_team = tournament['team']
        query_string = text('SELECT name FROM team WHERE name = :final_team')
        result = get_db().session.execute(query_string, {'final_team' : final_team})
        if result.fetchone() is None:
            response_string = gettext('Invalid team for tournament bet.')
        try:
            tournament_result = int(tournament['result'])
            if tournament_result < 0 or 3 < tournament_result:
                raise ValueError
        except ValueError:
            response_string = gettext('Invalid result for tournament bet.')

        try:
            tournament_credit = int(tournament['bet'])
            if tournament_credit < 0 or tournament_credit > bet_values['max_tournament_bet_value']:
                raise ValueError
            tournament['bet'] = tournament_credit
        except ValueError:
            response_string = gettext('Invalid bet amount at tournament bet.')

        # parsing anc checking group properties
        groups = bet_object['group']

        for group_id in groups:
            order = groups[group_id]['order']

            # checking and trimming bet value
            try:
                group_bet = int(groups[group_id]['bet'])

                if group_bet < 0 or group_bet > bet_values['max_group_bet_value']:
                    raise ValueError

                groups[group_id]['bet'] = group_bet
            except ValueError:
                response_string = gettext('Invalid bet amount at group bet.')
                break

            query_string = text('SELECT name FROM team WHERE group_id = :group_id AND name IN :names')
            query_string = query_string.bindparams(bindparam('names', expanding=True))
            result = get_db().session.execute(query_string, {'group_id' : group_id, 'names' : order})
            
            db_teams = result.fetchall()
            
            if db_teams is None or len(db_teams) != 4:
                response_string = gettext('Invalid group or team name at the group bet.')                       
                break

        if response_string is not None:
            return response_string, 400
        
        tournament_bet = tournament['bet']
        
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

        return jsonify({})

def during_groupstage():
    username = request.args.get('name')

    if username is not None:
        amount_after = current_app.config['BET_VALUES']['starting_bet_amount'] - score_calculator.get_group_and_tournament_bet_amount(username=username)
        groups = group_calculator.get_group_bet_dict_for_user(username=username)
        tournament_bet = group_calculator.get_tournament_bet_dict_for_user(username=username)

        return render_template('/group-bet/group-during.html', groups=groups, tournament_bet=tournament_bet, amount_after=amount_after, starting_bet_amount=current_app.config['BET_VALUES']['starting_bet_amount'])
    
    query_string = text('SELECT username FROM bet_user ORDER BY username ASC')
    result = get_db().session.execute(query_string)
    players = result.fetchall()

    return render_template('/group-bet/group-choose.html', players=players)

def after_evaluation():
    username = request.args.get('name')

    if username is not None:
        total_bet = score_calculator.get_group_and_tournament_bet_amount(username=username)
        amount_after = current_app.config['BET_VALUES']['starting_bet_amount'] - total_bet
        groups = group_calculator.get_group_bet_dict_for_user(username=username)
        tournament_bet_dict = group_calculator.get_tournament_bet_dict_for_user(username=username)
        total_win_amount = sum(group['prize'] for group in groups.values())        

        return render_template('/group-bet/group-after.html', groups=groups, tournament_bet=tournament_bet_dict, amount_after=amount_after, starting_bet_amount=current_app.config['BET_VALUES']['starting_bet_amount'], total_win=total_win_amount, total_bet=total_bet)
    
    query_string = text('SELECT username FROM bet_user')
    result = get_db().session.execute(query_string)
    players = result.fetchall()

    return render_template('/group-bet/group-choose.html', players=players)

@bp.route('/group-bet', methods=('GET', 'POST'))
@sign_in_required
def group_order():
    deadline_times = current_app.config['DEADLINE_TIMES']

    utc_now : datetime = time_handler.get_now_time_object()
    register_time : datetime = time_handler.parse_datetime_string(deadline_times['register'])
    group_evaluation_time_object : datetime = time_handler.parse_datetime_string(deadline_times['group_evaluation'])

    if utc_now < register_time:
        return before_deadline()
    elif utc_now < group_evaluation_time_object:
        return during_groupstage()
    else:
        return after_evaluation()

@bp.route('/tournament-bet.json', methods=('GET',))
@sign_in_required
def tournament_bet_odds():
    query_string = text("SELECT top1, top2, top4, top16, team.name, tr.translation as tr "
                        "FROM team "
                        "INNER JOIN team_translation AS tr ON tr.name = team.name AND tr.language = :l "
                        "ORDER BY team.name "
                        )
    result = get_db().session.execute(query_string, {'l' : g.user['language']})

    tournament_bet_odds = {}

    for team in result.fetchall():
        tournament_bet_odds[team.name] = {
            0 : team.top1,
            1 : team.top2,
            2 : team.top4,
            3 : team.top16,
            "tr" : team.tr
        }

    import io, json
    from flask import send_file
    in_memory_file = io.BytesIO()
    in_memory_file.write(json.dumps(tournament_bet_odds).encode('utf8'))
    in_memory_file.seek(0)

    return send_file(in_memory_file, as_attachment=True, download_name='tournament-bet.json', mimetype='application/json')