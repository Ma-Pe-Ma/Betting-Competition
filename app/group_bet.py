from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
from flask import jsonify

from datetime import datetime
from dateutil import tz
from collections import namedtuple

from app.auth import login_required
from app.db import get_db
from app.configuration import starting_bet_amount, max_group_bet_value, max_final_bet_value
from app.configuration import group_deadline_time, group_evaluation_time
from app.tools.group_calculator import get_group_object, get_final_bet
from app.tools.score_calculator import get_group_and_final_bet_amount, get_group_win_amount2

bp = Blueprint('group', __name__, '''url_prefix="/group"''')

def before_deadline():
    user_name = g.user['username']
    language = g.user['language']

    if request.method == 'GET':
        groups = get_group_object(user_name=user_name)
        final_bet_object = get_final_bet(user_name=user_name, language=language)

        return render_template(g.user['language'] + '/group-bet/group-edit.html', start_amount=starting_bet_amount, max_group_bet_value = max_group_bet_value, max_final_bet_value=max_final_bet_value, final_bet = final_bet_object, groups = groups)

    elif request.method == 'POST':
        bet_object = request.get_json()
        response_object = {}

        # parsing and checking final bet properties
        final = bet_object['final']

        final_team = final['team']
        cursor = get_db().cursor()
        cursor.execute('SELECT name FROM team WHERE name = %s', (final_team,))

        if cursor.fetchone() is None:
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
            if final_bet_value > max_final_bet_value:
                final['bet'] = max_final_bet_value

            if final_bet_value < 0:
                final['bet'] = max_final_bet_value

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
                if bet_value > max_group_bet_value:
                    bet_value = max_group_bet_value
                elif bet_value < 0:
                    bet_value = 0

                groups[group_id]['bet'] = bet_value

            except ValueError:
                response_object['result'] = 'error'
                response_object['info'] = 'GROUP_BET'
                break

            cursor = get_db().cursor()
            cursor.execute('SELECT name FROM team WHERE group_id = %s', (group_id,))
            db_teams = cursor.fetchall()
            
            if db_teams is None or len(db_teams) == 0:
                response_object['result'] = 'error'
                response_object['info'] = 'GROUP_ID'
                break
            else:
                for team in order:
                    team_found = False

                    for db_team in db_teams:
                        if db_team['name'] == team:
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
            cursor = get_db().cursor()
            cursor.execute('SELECT id FROM final_bet WHERE username=%s', (user_name,))
            id = cursor.fetchone()            

            if id is None:
                get_db().cursor().execute('INSERT INTO final_bet (username, bet, team, result, success) VALUES(%s, %s, %s, %s, %s)', (user_name, final_bet, final_team, final_result, None))
            else:
                get_db().cursor().execute('UPDATE final_bet SET username = %s, bet = %s, team = %s, result = %s WHERE id = %s', (user_name, final_bet, final_team, final_result, id['id'],))

            for group_id in groups:
                order = groups[group_id]['order']
                bet = groups[group_id]['bet']

                cursor1 = get_db().cursor()
                cursor1.execute('SELECT id FROM group_bet WHERE username=%s AND group_id=%s', (user_name, group_id))
                id = cursor1.fetchone()

                if id is None:
                    get_db().cursor().execute('INSERT INTO group_bet (username, bet, group_ID) VALUES(%s, %s, %s)', (user_name, bet, group_id))
                else:
                    get_db().cursor().execute('UPDATE group_bet SET username=%s, bet=%s, group_ID=%s WHERE id=%s', (user_name, bet, group_id, id['id']))

                position = 1
                for team in order:
                    cursor2 = get_db().cursor()
                    cursor2.execute('SELECT id FROM team_bet WHERE username=%s AND team=%s', (user_name, team))
                    id = cursor2.fetchone()
                    
                    if id is None:
                        get_db().cursor().execute('INSERT INTO team_bet (username, team, position) VALUES(%s, %s, %s)', (user_name, team, position))
                    else:
                        get_db().cursor().execute('UPDATE team_bet SET username=%s, team=%s, position=%s WHERE id=%s', (user_name, team, position, id['id']))                

                    position += 1

            get_db().commit()
            
            response_object['result'] = 'OK'
            return jsonify(response_object)

def during_groupstage():
    user_name = request.args.get('name')

    if user_name is not None:
        amount_after = starting_bet_amount - get_group_and_final_bet_amount(user_name=user_name)
        groups = get_group_object(user_name=user_name)
        final_bet_object = get_final_bet(user_name=user_name, language=g.user['language'])

        return render_template(g.user['language'] + '/group-bet/group-during.html', groups=groups, final_bet=final_bet_object, amount_after=amount_after, starting_bet_amount=starting_bet_amount)
    
    cursor = get_db().cursor()
    cursor.execute('SELECT username FROM bet_user WHERE NOT username=\'RESULT\' ORDER BY username ASC', ())
    players = cursor.fetchall()

    return render_template(g.user['language'] + '/group-bet/group-choose.html', players=players)

def after_evaluation():
    user_name = request.args.get('name')

    if user_name is not None:
        final_bet_object = get_final_bet(user_name=user_name, language=g.user['language'])
        groups = get_group_object(user_name=user_name)
        total_group_bet = get_group_and_final_bet_amount(user_name=user_name)
        total_win_amount = get_group_win_amount2(groups)

        return render_template(g.user['language'] + '/group-bet/group-after.html', group_containers=groups, total_bet=total_group_bet, total_win=total_win_amount, final_bet=final_bet_object)
    
    cursor = get_db().cursor()
    cursor.execute('SELECT username FROM bet_user WHERE NOT username=\'RESULT\'', ())
    players = cursor.fetchall()

    return render_template(g.user['language'] + '/group-bet/group-choose.html', players=players)

@bp.route('/group', methods=('GET', 'POST'))
@login_required
def group_order():
    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))

    deadline = datetime.strptime(group_deadline_time, '%Y-%m-%d %H:%M')
    deadline = deadline.replace(tzinfo=tz.gettz('UTC'))
    group_evaluation_time_object = datetime.strptime(group_evaluation_time, '%Y-%m-%d %H:%M')
    group_evaluation_time_object = group_evaluation_time_object.replace(tzinfo=tz.gettz('UTC'))

    if utc_now < deadline:
        return before_deadline()
    elif utc_now < group_evaluation_time_object:
        return during_groupstage()
    else:
        return after_evaluation()

@bp.route('/final-odds', methods=('GET',))
@login_required
def final_bet_odds():
    teams = []
    Team = namedtuple('Team', 'name, top1, top2, top4, top16')

    cursor = get_db().cursor()
    cursor.execute('SELECT top1, top2, top4, top16, name FROM team')

    for team in cursor.fetchall():
        cursor1 = get_db().cursor()
        cursor1.execute('SELECT translation FROM team_translation WHERE name=%s AND language=%s', (team['name'], g.user['language']))
        local_name = cursor1.fetchone()

        teams.append(Team(name=local_name['translation'], top1=team['top1'], top2=team['top2'], top4=team['top4'], top16=team['top16']))

    return render_template(g.user['language'] + '/group-bet/final-odds.html', teams=teams)