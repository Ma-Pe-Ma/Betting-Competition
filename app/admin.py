from flask import Blueprint
from flask import g
from flask import render_template
from flask import render_template_string
from flask import request
from flask import jsonify
from flask import current_app
from flask import send_from_directory
from flask import flash
from flask import Response
from flask import redirect
from flask import url_for
from markupsafe import escape

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
from flask_babel import gettext
from sqlalchemy import text

bp = Blueprint('admin', __name__, '''url_prefix="/admin"''')

@bp.route('/admin', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def admin_page():
    query_string = text('SELECT * from messages')
    result = get_db().session.execute(query_string)
    messages = [message._asdict() for message in result.fetchall()]

    groups = {}    
    if time_handler.get_now_time_object() > time_handler.parse_datetime_string(current_app.config['DEADLINE_TIMES']['group_evaluation']) :
        query_string = text("SELECT team.name, team.group_id, team.position, tr.translation AS local_name "
                            "FROM team "
                            "INNER JOIN team_translation AS tr ON tr.name = team.name AND tr.language = :l "
                            "ORDER BY team.group_id, team.position")
        result = get_db().session.execute(query_string, {'l' : g.user['language']})

        for team in result.fetchall():
            if team.group_id not in groups:
                groups[team.group_id] = []

            groups[team.group_id].append({'name' : team.name, 'local_name' : team.local_name, 'position' :  team.position})

    tournament_bets = []
    if time_handler.get_now_time_object() > time_handler.parse_datetime_string(current_app.config['DEADLINE_TIMES']['tournament_end']):
        query_string = text("SELECT tournament_bet.*, tr.translation as local_name "
                            "FROM tournament_bet "
                            "LEFT JOIN team_translation AS tr ON tr.name=tournament_bet.team AND tr.language = :language "
                            "ORDER BY tournament_bet.username")
        result = get_db().session.execute(query_string, {'language' : g.user['language']})

        tournament_bets = [tournament_bet._asdict() for tournament_bet in result.fetchall()]

    query_string = text("SELECT match.id, match.datetime, match.goal1, match.goal2, match.odd1, match.oddX, match.odd2, match.max_bet, t1.translation AS team1, t2.translation as team2 "
                        "FROM match "
                        "LEFT JOIN team_translation AS t1 ON t1.name = match.team1 AND t1.language = :l "
                        "LEFT JOIN team_translation AS t2 ON t2.name = match.team2 AND t2.language = :l "
                        "ORDER BY match.datetime")
    result = get_db().session.execute(query_string, {'l' : g.user['language']})

    matches = [match._asdict() for match in result.fetchall()]

    reset_keys = cache.get('password_reset_keys')

    if reset_keys is None:
        reset_keys = {}

    return render_template('/admin.html', matches = matches, messages = messages, groups = groups, tournament_bets = tournament_bets, reset_keys = reset_keys, scheduled_jobs=scheduler_handler.scheduler.get_jobs())

@bp.route('/admin/message', methods=['POST'])
@sign_in_required(role=Role.ADMIN)
def message():
    for message_id, message in enumerate(request.get_json()):
        query_string = text('UPDATE messages SET message=:message WHERE id=:id')
        get_db().session.execute(query_string, {'message' : message, 'id' : message_id})
        
    get_db().session.commit()

    return gettext('Messages updated successfully!'), 200    

@bp.route('/admin/send-notification', methods=['POST'])
@sign_in_required(role=Role.ADMIN)
def send_notification():
    try:
        message_text = request.get_json()['text']
        message_subject = request.get_json()['subject']
        
        if len(message_text) < 10:
            return gettext('Too short message!'), 400
            
        if len(message_subject) < 6:
            return gettext('Too short subject!'), 400

        messages = []

        query_string = text('SELECT email, username FROM bet_user')
        result = get_db().session.execute(query_string)

        for user in result.fetchall():
            messages.append(notification_handler.get_notifier().create_message(sender='me', user=user._asdict(), subject=message_subject, message_text=message_text))

        notification_handler.get_notifier().send_messages(messages=messages)
    except Exception as error:
        current_app.logger.info('Error sending notification to everyone: ' + str(error))
        return gettext('Error sending notification to everyone!'), 400

    return gettext('Notifications successfully sent!'), 200

@bp.route('/admin/standings', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def standings():
    with current_app.open_resource('./templates/notifications/standings.html', 'r') as standings_template, current_app.open_resource('./templates/notifications/standings-subject.txt', 'r') as subject:
        standings = create_standings()
        date = time_handler.get_now_time_object().strftime('%Y.%m.%d')

        subject = render_template_string(subject.read(), date=date)
        message_text = render_template_string(standings_template.read(), username=gettext('player'), date=date, standings=standings)

    return message_text

@bp.route('/admin/emails', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def emails():
    query_string = text('SELECT email FROM bet_user')
    result = get_db().session.execute(query_string)

    email_list = ''

    for email in result.fetchall():
        email_list += '{email}; '.format(email=email.email)

    return email_list

@bp.route('/admin/match', methods=['GET', 'POST'])
@sign_in_required(role=Role.ADMIN)
def odd_edit():
    if request.method == 'GET':
        try:
            matchID = int(request.args.get('matchID'))

            query_string = text("SELECT match.id, ROUND(match.odd1, 2) AS odd1, ROUND(match.oddX, 2) AS oddX, ROUND(match.odd2, 2) AS odd2, match.datetime, match.round, match.max_bet, match.goal1, match.goal2, "
                                "t1.translation AS team1, t2.translation AS team2 "
                                "FROM match "
                                "LEFT JOIN team_translation AS t1 ON t1.name = match.team1 AND t1.language = :l "
                                "LEFT JOIN team_translation AS t2 ON t2.name = match.team2 AND t2.language = :l "
                                "WHERE match.id=:matchID")
            result = get_db().session.execute(query_string, {'matchID' : matchID, 'l' : g.user['language']})

            return jsonify(result.fetchone()._asdict()), 200
        except Exception as error:
            current_app.logger.info('Failed to fetch match data: ' + str(error))
            return gettext('Failed to fetch match data!'), 400

    elif request.method == 'POST':
        updated_data = request.get_json()

        if type(updated_data['goal1']) != type(updated_data['goal2']) or (updated_data['goal1'] is not None and type(updated_data['goal1']) is not int):
            return gettext('Invalid goal value specified!'), 400

        query_string = text('UPDATE match SET odd1=:odd1, oddX=:oddX, odd2=:odd2, max_bet=:max_bet WHERE id=:id')
        get_db().session.execute(query_string, updated_data)

        query_string = text('UPDATE match SET goal1=:goal1, goal2=:goal2 WHERE id=:id AND unixepoch(datetime) < unixepoch(\'now\')')
        get_db().session.execute(query_string, updated_data)

        get_db().session.commit()

        flash(escape(gettext('Updating data for match %(id)s was successful!', id=updated_data['id'])), 'success')

        return {}

@bp.route('/admin/group-evaluation', methods=['POST'])
@sign_in_required(role=Role.ADMIN)
def group_evaluation():    
    for key in request.json:
        for index, team in enumerate(request.json[key]):
            query_string = text('UPDATE team SET position=:position WHERE name=:team')
            get_db().session.execute(query_string, {'position' : index + 1, 'team' : team})

    get_db().session.commit()

    return gettext('Group results set successfully!'), 200

@bp.route('/admin/tournament-bet', methods=['POST'])
@sign_in_required(role=Role.ADMIN)
def tournament_bet():
    for username, success in request.get_json().items():
        success = None if success == '' else success
        query_string = text('UPDATE tournament_bet SET success=:success WHERE username=:username')
        get_db().session.execute(query_string, {'success' : success, 'username' : username})

    get_db().session.commit()

    return gettext('Tournament bet results set successfully!'), 200

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
            return gettext('Database file was not specified!'), 400

        new_file = request.files['database']

        if not new_file or new_file.filename == '':
            return gettext('Database file is null!'), 400

        if allowed_file(new_file.filename):
            try:
                #filename = secure_filename(new_file.filename)                
                file_path = os.path.join(current_app.instance_path, db_filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                new_file.save(file_path)

                return gettext('Database file uploading was successful!'), 200
            except Exception as error:
                current_app.logger.info('Error while saving new database file: ' + str(error))
                return gettext('Error while saving new database file!'), 400
            
        return gettext('The specified format cannot be uploaded!'), 400

@bp.route('/admin/maintenance', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def maintain_toggle():
    cache.set('maintenance', not cache.get('maintenance'), timeout=120)

    state_string = gettext('ON') if cache.get('maintenance') else gettext('OFF')
    flash(gettext('Maintenance successfully turned %(id)s!', id=state_string), 'success')

    return redirect(url_for('admin.admin_page'))

@bp.route('/admin/manual-daily-checker', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def manual_daily_checker():
    scheduler_handler.daily_checker()
    flash(gettext('Daily checker manually initiated!'), 'success')

    return redirect(url_for('admin.admin_page'))

@bp.route('/admin/match-update', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def match_update():
    if not database_manager.update_match_data_from_fixture():
        return gettext('Match data updating failed!'), 400
    
    return gettext('Match data succsesfully updated!'), 200    

@bp.route('/admin/standings-notification', methods=['GET'])
@sign_in_required(role=Role.ADMIN)
def standings_notification():
    if not scheduler_handler.daily_standings():
        return gettext('Standings notification failed!'), 400
    
    return gettext('Standings successfully notified!'), 200

@bp.route('/admin/log')
@sign_in_required(role=Role.ADMIN)
def log():
    with current_app.open_resource(os.path.join(current_app.instance_path, 'logfile_info.log')) as log_file:
        return Response(log_file.read(), mimetype='text/plain')
