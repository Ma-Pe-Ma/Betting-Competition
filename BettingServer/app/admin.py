from flask import Blueprint
from flask import g
from flask import render_template_string
from flask import request
from flask import current_app
from flask import send_from_directory
from flask import Response

from werkzeug.utils import secure_filename

from app.tools import database_manager
from app.tools.db_handler import get_db
from app.tools.cache_handler import cache
from app.auth import sign_in_required, Role
from app.notification import notification_handler
from app.tools import time_handler
from app.tools import database_manager
from app.tools import scheduler_handler
from app.standings import create_standings

import os
from datetime import timedelta
from flask_babel import gettext
from sqlalchemy import text

bp = Blueprint('admin', __name__, '''url_prefix="/admin"''')

@bp.route('/admin/match-update', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def match_update():
    if not database_manager.update_match_data_from_fixture():
        return { 'message': gettext('Match data updating failed!'), 'type': 'success'}

    return {'message': gettext('Match data succsesfully updated!'), 'type': 'success'}

@bp.route('/admin/matches')
def matches():
    query_string = text("SELECT match.id, match.datetime, match.goal1, match.goal2, match.odd1, match.oddX, match.odd2, match.max_bet, t1.translation AS team1, t2.translation as team2 "
                        "FROM match "
                        "LEFT JOIN team_translation AS t1 ON t1.name = match.team1 AND t1.language = :l "
                        "LEFT JOIN team_translation AS t2 ON t2.name = match.team2 AND t2.language = :l "
                        "ORDER BY match.datetime")
    result = get_db().session.execute(query_string, {'l' : g.user['language'], 'tz' : g.user['timezone']})

    return [match._asdict() for match in result.fetchall()]

@bp.route('/admin/match-get', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def odd_get():
    try:
        matchID = int(request.args.get('matchID'))

        query_string = text("SELECT match.id, ROUND(match.odd1, 2) AS odd1, ROUND(match.oddX, 2) AS oddX, ROUND(match.odd2, 2) AS odd2, match.datetime, match.round, match.max_bet, match.goal1 AS bgoal1, match.goal2 AS bgoal2, "
                            "t1.translation AS team1, t2.translation AS team2 "
                            "FROM match "
                            "LEFT JOIN team_translation AS t1 ON t1.name = match.team1 AND t1.language = :l "
                            "LEFT JOIN team_translation AS t2 ON t2.name = match.team2 AND t2.language = :l "
                            "WHERE match.id=:matchID")
        result = get_db().session.execute(query_string, {'matchID' : matchID, 'l' : g.user['language'], 'tz' : g.user['timezone']})

        return result.fetchone()._asdict()
    except Exception as error:
        current_app.logger.info('Failed to fetch match data: ' + str(error))
        return {'message': gettext('Failed to fetch match data!'), 'type': 'danger'}, 400

@bp.route('/admin/match-set', methods=['POST'])
@sign_in_required(role=Role.ADMIN)
def odd_set():
    updated_data = request.get_json()

    if type(updated_data['bgoal1']) != type(updated_data['bgoal2']) or (updated_data['bgoal1'] is not None and type(updated_data['bgoal1']) is not int):
        return {'message': gettext('Invalid goal value specified!'), 'type': 'danger'}

    query_string = text('UPDATE match SET odd1=:odd1, oddX=:oddX, odd2=:odd2, max_bet=:max_bet WHERE id=:id')
    get_db().session.execute(query_string, updated_data)

    query_string = text('UPDATE match SET goal1=:bgoal1, goal2=:bgoal2 WHERE id=:id AND unixepoch(datetime) < unixepoch(\'now\')')
    get_db().session.execute(query_string, updated_data)

    get_db().session.commit()

    return {'message': gettext('Successfully updated match data!'), 'type': 'success'}

@bp.route('/admin/message-get', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def messages_get():
    query_string = text('SELECT * from messages')
    result = get_db().session.execute(query_string)
    return [message._asdict() for message in result.fetchall()]

@bp.route('/admin/message-set', methods=['POST'])
@sign_in_required(role=Role.ADMIN)
def messages_set():
    try:
        for message in request.get_json():
            query_string = text('UPDATE messages SET message=:message WHERE id=:id')
            get_db().session.execute(query_string, {'message' : message['message'], 'id' : message['id']})

        get_db().session.commit()
    except Exception as e:
        return {'message': gettext('Error while setting home messages: {e}'.format(e=e)), 'type' : 'danger'}

    return {'message': gettext('Messages updated successfully!'), 'type': 'success'}

@bp.route('/admin/send-notification', methods=['POST'])
@sign_in_required(role=Role.ADMIN)
def send_notification():
    try:
        message_text = request.get_json()['message']
        message_subject = request.get_json()['subject']
        
        if len(message_text) < 10:
            return {'message' : gettext('Too short message!'), 'type': 'danger' }
            
        if len(message_subject) < 6:
            return {'message' : gettext('Too short subject!'), 'type': 'danger' }

        messages = []

        query_string = text('SELECT email, username FROM bet_user')
        result = get_db().session.execute(query_string)

        for user in result.fetchall():
            messages.append(notification_handler.get_notifier().create_message(sender='me', user=user._asdict(), subject=message_subject, message_text=message_text))

        notifications = notification_handler.get_notifier().send_messages(messages=messages)

        return {'message' : 'Notifications successfully sent: ' + str(notifications) , 'type' : 'success'}
    except Exception as error:
        current_app.logger.info('Error sending notification to everyone: ' + str(error))
        return {'message' : gettext('Error sending notification to everyone!'), 'type': 'danger' }

@bp.route('/admin/standings', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def standings():
    with current_app.open_resource('./templates/notifications/standings.html', 'r') as standings_template, current_app.open_resource('./templates/notifications/standings-subject.txt', 'r') as subject:
        standings = create_standings()
        date = time_handler.get_now_time_object().strftime('%Y.%m.%d')

        subject = render_template_string(subject.read(), date=date)
        message_text = render_template_string(standings_template.read(), username=gettext('player'), date=date, standings=standings)

    query_string = text('SELECT email FROM bet_user')
    result = get_db().session.execute(query_string)

    email_list = ''

    for email in result.fetchall():
        email_list += '{email}; '.format(email=email.email)

    return {'standings': message_text, 'emails': email_list}    

@bp.route('/admin/group-get', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def get_groups():
    groups = []
    try:
        if time_handler.get_now_time_object() > time_handler.parse_datetime_string(current_app.config['DEADLINE_TIMES']['group_evaluation']) - timedelta(minutes=30):
            query_string = text("SELECT team.name, team.group_id, team.position, tr.translation AS local_name "
                                "FROM team "
                                "INNER JOIN team_translation AS tr ON tr.name = team.name AND tr.language = :l "
                                "ORDER BY team.group_id, team.position")
            result = get_db().session.execute(query_string, {'l' : g.user['language']})

            for team in result.fetchall():
                current_group = None

                for gr in groups:
                    if gr['id'] == team.group_id:
                        current_group = gr

                if current_group is None:
                    current_group = {'id': team.group_id, 'teams': []}
                    groups.append(current_group)

                current_group['teams'].append({'name' : team.name, 'name_tr' : team.local_name, 'position' :  team.position})
    except Exception as e:
        return {'message': gettext('Error while setting order: {e}'.format(e=e)), 'type' : 'danger'}

    return groups

@bp.route('/admin/group-set', methods=['POST'])
@sign_in_required(role=Role.ADMIN)
def set_groups():
    try:
        for group in request.json:
            for index, team in enumerate(group['teams']):
                query_string = text('UPDATE team SET position=:position WHERE name=:team')
                get_db().session.execute(query_string, {'position' : index + 1, 'team' : team['name']})

        get_db().session.commit()
    except Exception as e:
        return {'message': gettext('Error while setting order: {e}'.format(e=e)), 'type' : 'danger'}

    return {'message': gettext('Group results set successfully!'), 'type' : 'success'}

@bp.route('/admin/tournament-bet-get', methods=['GET'])
def tournament_bet_get():
    tournament_bets = []
    if time_handler.get_now_time_object() > time_handler.parse_datetime_string(current_app.config['DEADLINE_TIMES']['tournament_end']) - timedelta(minutes=30):
        query_string = text("SELECT tournament_bet.*, tr.translation as local_name "
                            "FROM tournament_bet "
                            "LEFT JOIN team_translation AS tr ON tr.name=tournament_bet.team AND tr.language = :language "
                            "ORDER BY UPPER(tournament_bet.username)")
        result = get_db().session.execute(query_string, {'language' : g.user['language']})

        tournament_bets = [tournament_bet._asdict() for tournament_bet in result.fetchall()]

    return tournament_bets

@bp.route('/admin/tournament-bet-set', methods=['POST'])
@sign_in_required(role=Role.ADMIN)
def tournament_bet_set():
    for tournament_bet in request.get_json():
        query_string = text('UPDATE tournament_bet SET success=:success WHERE username=:username')
        get_db().session.execute(query_string, {'success' : tournament_bet['success'], 'username' : tournament_bet['username']})

    get_db().session.commit()

    return {'message': gettext('Tournament bet results set successfully!'), 'type': 'success'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/admin/team-data', methods=['POST'])
@sign_in_required(role=Role.ADMIN)
def upload_team_data():
    # check if the post request has the file part
    if 'team' not in request.files and 'translation' not in request.files:
        return gettext('One of the files was not specified for the request!'), 400

    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    team_file = request.files['team']        
    if team_file.filename == '':
        return gettext('No team file was specified!'), 400

    translation_file = request.files['translation']
    if translation_file.filename == '':
        return gettext('No translation file was specified!'), 400
        
    if not team_file or not allowed_file(team_file.filename) or not translation_file or not allowed_file(translation_file.filename):    
        return gettext('The uploaded file\'s extension is not correct!'), 400
    
    try:
        team_file_name = secure_filename(team_file.filename)
        team_file_path = os.path.join(current_app.instance_path, current_app.config['UPLOAD_FOLDER'], team_file_name)
        team_file.save(team_file_path)

        translation_file_name = secure_filename(translation_file.filename)
        translation_file_path = os.path.join(current_app.instance_path, current_app.config['UPLOAD_FOLDER'], translation_file_name)
        translation_file.save(translation_file_path)
    except Exception as error:
        current_app.logger.info('Failing to write team-data files to local storage: ' + str(error))
        return gettext('Failing to write team-data files to local storage!'), 400

    if not database_manager.initialize_teams(team_file_name=team_file_path, translation_file_name=translation_file_path):
        return gettext('Error while initializing the teams!'), 400

    if not database_manager.initialize_matches():
        return gettext('Error while initializing the matches!'), 400

    return gettext('Team data file uploading was successful!'), 200

@bp.route('/admin/database', methods=['GET', 'POST'])
@sign_in_required(role=Role.ADMIN)
def database_file():
    database_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    db_filename = database_uri.replace('sqlite:///', '')
    db_filename_components = db_filename.split('.')

    if request.method == 'GET':
        from dateutil import tz # TODO
        datetime_string = time_handler.get_now_time_object().astimezone(tz.gettz('Europe/Budapest')).strftime('%Y-%m-%d %H-%M')

        download_name = '{original_name}_{datetime}.{extension}'.format(original_name=db_filename_components[0], datetime=datetime_string, extension=db_filename_components[1])

        return send_from_directory(current_app.instance_path, db_filename, as_attachment=True, download_name=download_name)
    
    if request.method == 'POST':
        if 'database' not in request.files:
            return {'message':gettext('Database file was not specified!'), 'type' : 'danger'}

        new_file = request.files['database']

        if not new_file or new_file.filename == '':
            return {'message': gettext('Database file is null!'), 'type' : 'danger'}

        if allowed_file(new_file.filename):
            try:
                #filename = secure_filename(new_file.filename)                
                file_path = os.path.join(current_app.instance_path, db_filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                new_file.save(file_path)

                return {'message': gettext('Database file uploading was successful!'), 'type' : 'success'}
            except Exception as error:
                current_app.logger.info('Error while saving new database file: ' + str(error))
                return {'message': gettext('Error while saving new database file!'), 'type' : 'danger'}
        
        return {'message': gettext('The specified format cannot be uploaded!'), 'type' : 'danger'}

@bp.route('/admin/maintenance', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def maintenance():
    return {'scheduledTasks' : scheduler_handler.scheduler.get_jobs()}

@bp.route('/admin/maintenance-set', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def maintain_toggle():
    cache.set('maintenance', not cache.get('maintenance'), timeout=120)

    state_string = gettext('ON') if cache.get('maintenance') else gettext('OFF')
    return {'message' : gettext('Maintenance successfully turned %(id)s!', id=state_string), 'type' : 'success'}

@bp.route('/admin/manual-daily-checker', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def manual_daily_checker():
    scheduler_handler.daily_checker()
    return {'message' : gettext('Daily checker manually initiated!'), 'type' : 'success'}

@bp.route('/admin/standings-notification', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def standings_notification():
    if not scheduler_handler.daily_standings():
        return {'message': gettext('Standings notification failed!'), 'type': 'danger'}
    
    return {'message': gettext('Standings successfully notified!'), 'type' : 'success'}

@bp.route('/admin/log')
@sign_in_required(role=Role.ADMIN)
def log():
    with current_app.open_resource(os.path.join(current_app.instance_path, 'logfile_info.log')) as log_file:
        return Response(log_file.read(), mimetype='text/plain')

@bp.route('/admin/reset-keys', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def admin_page():
    reset_keys = cache.get('password_reset_keys')

    if reset_keys is None:
        reset_keys = []

    return reset_keys
