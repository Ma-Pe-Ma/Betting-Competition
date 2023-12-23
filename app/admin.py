from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
from flask import jsonify
from flask import current_app

from werkzeug.utils import secure_filename

from app import database_manager
from app.db import get_db
from app.auth import admin_required, login_required
from app.gmail_handler import create_message, send_messages

from app.tools import time_determiner
from app.configuration import configuration

import os
from flask_babel import gettext
from sqlalchemy import text

bp = Blueprint('admin', __name__, '''url_prefix="/admin"''')

@bp.route('/admin', methods=('GET',))
@login_required
@admin_required
def admin_page():
    query_string = text('SELECT * from messages')
    result = get_db().session.execute(query_string)
    messages = [message._asdict() for message in result.fetchall()]

    groups = {}    
    if time_determiner.get_now_time_object() > time_determiner.parse_datetime_string(configuration.deadline_times.group_evaluation) :
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
    if time_determiner.get_now_time_object() > time_determiner.parse_datetime_string(configuration.deadline_times.tournament_end):
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

    return render_template('/admin.html', matches = matches, messages = messages, groups = groups, tournament_bets = tournament_bets)

@bp.route('/admin/message', methods=('POST',))
@login_required
@admin_required
def message():
    for message_id, message in enumerate(request.get_json()):
        query_string = text('UPDATE messages SET message=:message WHERE id=:id')
        get_db().session.execute(query_string, {'message' : message, 'id' : message_id})
        
    get_db().session.commit()

    return gettext('Messages updated successfully!'), 200    

@bp.route('/admin/send-email', methods=('POST',))
@login_required
@admin_required
def send_email():
    try:
        email_message = request.get_json()['email']
        subject = request.get_json()['subject']
        
        if len(email_message) < 10:
            return gettext('Too short message!'), 400
            
        if len(subject) < 6:
            return gettext('Too short subject!'), 400

        messages = []

        query_string = text('SELECT email from bet_user')
        result = get_db().session.execute(query_string)

        for user in result.fetchall():
            messages.append(create_message(sender='me', to=user.email, subject=subject, message_text=email_message))

        send_messages(messages=messages)
    except:
        return gettext('Error sending email to everyone!')

    return gettext('Emails successfully sent!'), 200

@bp.route('/admin/match', methods=('GET', 'POST'))
@login_required
@admin_required
def odd_edit():
    if request.method == 'GET':
        try:
            matchID = int(request.args.get('matchID'))

            query_string = text("SELECT match.id, match.odd1, match.oddX, match.odd2, match.datetime, match.round, match.max_bet, match.goal1, match.goal2, "
                                "t1.translation AS team1, t2.translation AS team2 "
                                "FROM match "
                                "LEFT JOIN team_translation AS t1 ON t1.name = match.team1 AND t1.language = :l "
                                "LEFT JOIN team_translation AS t2 ON t2.name = match.team2 AND t2.language = :l "
                                "WHERE match.id=:matchID")
            result = get_db().session.execute(query_string, {'matchID' : matchID, 'l' : g.user['language']})

            return jsonify(result.fetchone()._asdict()), 200
        except:
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

        return gettext('Match data successfully updated!'), 200

@bp.route('/admin/group-evaluation', methods=('POST',))
@login_required
@admin_required
def group_evaluation():    
    for key in request.json:
        for index, team in enumerate(request.json[key]):
            query_string = text('UPDATE team SET position=:position WHERE name=:team')
            get_db().session.execute(query_string, {'position' : index + 1, 'team' : team})

    get_db().session.commit()

    return gettext('Group results set successfully!'), 200

@bp.route('/admin/tournament-bet', methods=('POST',))
@login_required
@admin_required
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

@bp.route('/admin/team-data', methods=('POST',))
@login_required
@admin_required
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
        team_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], team_file_name))

        translation_file_name = secure_filename(translation_file.filename)
        translation_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], translation_file_name))
    except:
        return gettext('Failing to write team-data files to local storage!');

    if not database_manager.initialize_teams(team_file_name=team_file_name, translation_file_name=translation_file_name):
        return gettext('Error while initializing the teams!'), 400

    if not database_manager.initialize_matches():
        return gettext('Error while initializing the matches!'), 400

    return gettext('Team data file uploading was successful!'), 200