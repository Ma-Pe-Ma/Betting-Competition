from flask import Blueprint
from flask import g
from flask import request
from flask import current_app

from datetime import datetime

from app.auth import sign_in_required
from app.tools.db_handler import get_db
from app.tools import score_calculator
from app.tools import time_handler

from flask_babel import gettext
from sqlalchemy import text, bindparam

bp = Blueprint('group', __name__, '''url_prefix="/group"''')

@bp.route('/group-bet', methods=['POST'])
@sign_in_required()
def set_group_bet():
    bet_values = current_app.config['BET_VALUES']
    username = g.user['username']

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
    groups = bet_object['groups']

    for group in groups:
        team_names = [team['bet_name'] for team in group['teams']]

        # checking and trimming bet value
        try:
            group_bet = int(group['bet'])

            if group_bet < 0 or group_bet > bet_values['max_group_bet_value']:
                raise ValueError

            group['bet'] = group_bet
        except ValueError:
            response_string = gettext('Invalid bet amount at group bet.')
            break

        query_string = text('SELECT name FROM team WHERE group_id = :group_id AND name IN :names')
        query_string = query_string.bindparams(bindparam('names', expanding=True))
        result = get_db().session.execute(query_string, {'group_id' : group['id'], 'names' : team_names})
        
        db_teams = result.fetchall()
        
        if db_teams is None or len(db_teams) != 4:
            response_string = gettext('Invalid group or team name at the group bet.')                       
            break

    if response_string is not None:
        return {'message': response_string, 'type': 'danger'}
    
    tournament_bet = tournament['bet']
    
    query_string = text("INSERT OR REPLACE INTO tournament_bet (username, bet, team, result, success) "
                        "VALUES(:u, :b, :t, :r, 0)")
    get_db().session.execute(query_string, {'u' : username, 'b' : tournament_bet, 't' : final_team, 'r' : tournament_result})

    for group in groups:
        team_names = [team['bet_name'] for team in group['teams']]
        bet = group['bet']

        query_string = text("INSERT OR REPLACE INTO group_bet (username, group_id, bet) "
                            "VALUES (:u, :g, :b)")
        get_db().session.execute(query_string, {'u' : username, 'g' : group['id'], 'b' : bet})

        for index, team in enumerate(team_names):
            print("INS TEAM: ", index, ", team: ",team)
            query_string = text('INSERT OR REPLACE INTO team_bet (username, team, position) VALUES(:u, :t, :p)')
            get_db().session.execute(query_string, {'u' : username, 't' : team, 'p' : index + 1})

    get_db().session.commit()

    return {'message': gettext('Successfully updated groups!'), 'type': 'success'}

@bp.route('/group-status', methods=['GET'])
@sign_in_required()
def group_order():
    deadline_times = current_app.config['DEADLINE_TIMES']

    utc_now : datetime = time_handler.get_now_time_object()
    register_time : datetime = time_handler.parse_datetime_string(deadline_times['register'])

    username = g.user['username'] if utc_now < register_time else request.args.get('name')

    if username is None:
        return '', 401

    groups = score_calculator.get_group_bet_dict_for_user(username=username)
    tournament_bet_dict = score_calculator.get_tournament_bet_dict_for_user(username=username)

    return {'groups': groups, 'tournament': tournament_bet_dict}

@bp.route('/tournament-bet', methods=['GET'])
@sign_in_required()
def tournament_bet_odds():
    query_string = text("SELECT top1, top2, top4, top8, team.name, tr.translation AS tr "
                        "FROM team "
                        "INNER JOIN team_translation AS tr ON tr.name = team.name AND tr.language = :l "
                        "ORDER BY team.name "
                        )
    result = get_db().session.execute(query_string, {'l' : g.user['language']})

    teams = []
    for team in result.fetchall():
        team_dict = {
            'team': team.name,
            'team_tr': team.tr,
            'odds': [team.top1, team.top2, team.top4, team.top8]
        }

        teams.append(team_dict)

    return teams
