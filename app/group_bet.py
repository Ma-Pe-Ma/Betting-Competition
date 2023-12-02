from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
from flask import jsonify

from datetime import datetime

from app.auth import login_required
from app.db import get_db
from app.configuration import configuration
from app.tools.group_calculator import get_group_object, get_tournament_bet
from app.tools.score_calculator import get_group_and_final_bet_amount, get_group_win_amount

from app.tools import time_determiner

from sqlalchemy import text

bp = Blueprint('group', __name__, '''url_prefix="/group"''')

def before_deadline():
    username = g.user['username']
    language = g.user['language']

    bet_values = configuration.bet_values

    if request.method == 'GET':
        groups = get_group_object(username=username)
        tournament_bet = get_tournament_bet(username=username, language=language)

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
            final_result = int(final['result'])
            if final_result < 0 or 3 < final_result:
                response_object['result'] = 'error'
                response_object['info'] = 'FINAL_RESULT'
        except ValueError:
            response_object['result'] = 'error'
            response_object['info'] = 'FINAL_RESULT'

        try:
            final_bet_value = int(final['bet'])
            if final_bet_value > bet_values.max_final_bet_value:
                final['bet'] = bet_values.max_final_bet_value

            if final_bet_value < 0:
                final['bet'] = bet_values.max_final_bet_value

        except ValueError:
            response_object['result'] = 'error'
            response_object['info'] = 'FINAL_BET'

        # parsing anc checking group properties
        groups = bet_object['group']

        for group_id in groups:
            bet = groups[group_id]['bet']
            order = groups[group_id]['order']

            # checking and trimming bet value
            try:
                bet_value = int(bet)
                if bet_value > bet_values.max_group_bet_value:
                    bet_value = bet_values.max_group_bet_value
                elif bet_value < 0:
                    bet_value = 0

                groups[group_id]['bet'] = bet_value

            except ValueError:
                response_object['result'] = 'error'
                response_object['info'] = 'GROUP_BET'
                break

            query_string = text('SELECT name FROM team WHERE group_id = :group_id')
            result = get_db().session.execute(query_string, {'group_id' : group_id})
            db_teams = result.fetchall()
            
            if db_teams is None or len(db_teams) == 0:
                response_object['result'] = 'error'
                response_object['info'] = 'GROUP_ID'
                break
            else:
                for team in order:
                    team_found = False

                    for db_team in db_teams:
                        if db_team.name == team:
                            team_found = True
                            break
                        
                    if team_found is False:
                        response_object['result'] = 'error'
                        response_object['info'] = 'GROUP_TEAM'
                        break

        if bool(response_object) is not False:
            return jsonify(response_object)
        else:
            final_bet = final['bet']
            query_string = text('SELECT id FROM final_bet WHERE username=:username')
            result = get_db().session.execute(query_string, {'username' : username})
            id = result.fetchone()            

            if id is None:
                query_string = text('INSERT INTO final_bet (username, bet, team, result, success) VALUES(:u, :b, :t, :r, :s)')
                get_db().session.execute(query_string,{'u' : username, 'b' : final_bet, 't' : final_team, 'r' : final_result, 's' : None})
            else:
                query_string = text('UPDATE final_bet SET username = :u, bet = :b, team = :t, result = :r WHERE id = :i')
                get_db().session.execute(query_string, {'u' : username, 'b' : final_bet, 't' : final_team, 'r' : final_result, 'i' : id.id})

            for group_id in groups:
                order = groups[group_id]['order']
                bet = groups[group_id]['bet']

                query_string = text('SELECT id FROM group_bet WHERE username=:u AND group_id=:g')
                result1 = get_db().session.execute(query_string, {'u' : username, 'g' : group_id})
                id = result1.fetchone()

                if id is None:
                    query_string = text('INSERT INTO group_bet (username, bet, group_ID) VALUES(:u, :b, :g)')
                    get_db().session.execute(query_string, {'u' : username, 'b' : bet, 'g' : group_id})
                else:
                    query_string = text('UPDATE group_bet SET username=:u, bet=:b, group_ID=:g WHERE id=:i')
                    get_db().session.execute(query_string, {'u' : username, 'b' : bet, 'g' : group_id, 'i' : id.id})

                position = 1
                for team in order:
                    query_string = text('SELECT id FROM team_bet WHERE username=:username AND team=:team')
                    result2 = get_db().session.execute(query_string, {'username' : username, 'team' : team})
                    id = result2.fetchone()
                    
                    if id is None:
                        query_string = text('INSERT INTO team_bet (username, team, position) VALUES(:u, :t, :p)')
                        get_db().session.execute(query_string, {'u' : username, 't' : team, 'p' : position})
                    else:
                        query_string = text('UPDATE team_bet SET username=:u, team=:t, position=:p WHERE id=:i')
                        get_db().session.execute(query_string, {'u' : username, 't' : team, 'p' : position, 'i' : id.id})                

                    position += 1

            get_db().session.commit()
            
            response_object['result'] = 'OK'
            return jsonify(response_object)

def during_groupstage():
    username = request.args.get('name')

    if username is not None:
        amount_after = configuration.bet_values.starting_bet_amount - get_group_and_final_bet_amount(username=username)
        groups = get_group_object(username=username)
        final_bet_object = get_tournament_bet(username=username, language=g.user['language'])

        return render_template('/group-bet/group-during.html', groups=groups, final_bet=final_bet_object, amount_after=amount_after, starting_bet_amount=configuration.bet_values.starting_bet_amount)
    
    query_string = text('SELECT username FROM bet_user WHERE NOT username=\'RESULT\' ORDER BY username ASC')
    result = get_db().session.execute(query_string)
    players = result.fetchall()

    return render_template('/group-bet/group-choose.html', players=players)

def after_evaluation():
    username = request.args.get('name')

    if username is not None:
        final_bet_object = get_tournament_bet(username=username, language=g.user['language'])
        groups = get_group_object(username=username)
        total_group_bet = get_group_and_final_bet_amount(username=username)
        total_win_amount = get_group_win_amount(groups)

        return render_template('/group-bet/group-after.html', group_containers=groups, total_bet=total_group_bet, total_win=total_win_amount, final_bet=final_bet_object)
    
    query_string = text('SELECT username FROM bet_user WHERE NOT username=\'RESULT\'')
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
def final_bet_odds():
    teams = []

    query_string = text('SELECT top1, top2, top4, top16, name FROM team')
    result = get_db().session.execute(query_string)

    for team in result.fetchall():
        query_string = text('SELECT translation FROM team_translation WHERE name=:name AND language=:language')
        result1 = get_db().session.execute(query_string, {'name' : team.name, 'language' : g.user['language']})
        local_name = result1.fetchone()

        team_dict : dict = team._asdict()
        team_dict['name'] = local_name.translation

        teams.append(team_dict)

    return render_template('/group-bet/final-odds.html', teams=teams)