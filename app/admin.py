from flask import Blueprint
from flask import redirect
from flask import g
from flask import flash
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify
from flask import current_app

from datetime import datetime
from werkzeug.utils import secure_filename

from app.database_manager import download_data_csv, initialize_matches, initialize_teams
from app.db import get_db
from app.auth import admin_required, login_required
from app.gmail_handler import create_message, send_messages

from sqlalchemy import text

import os

bp = Blueprint('admin', __name__, '''url_prefix="/admin"''')

@bp.route('/admin', methods=('GET',))
@login_required
@admin_required
def admin_page():
    return render_template('/admin/admin.html')

@bp.route('/admin/fetch-match', methods=('GET',))
@login_required
@admin_required
def fetch_match():
    result = {}
    result['result'] = download_data_csv()
    return jsonify(result)

@bp.route('/admin/message', methods=('GET', 'POST'))
@login_required
@admin_required
def message():
    success_message = None

    if request.method == 'POST':
        for key in request.form:
            query_string = text('UPDATE messages SET message=:message WHERE id=:id')
            get_db().session.execute(query_string, {'message' : request.form[key], 'id' : key})
        
        get_db().session.commit()
        success_message = True

    messages = []

    query_string = text('SELECT * from messages')
    result = get_db().session.execute(query_string)

    for message in result.fetchall():
        messages.append(message._asdict())

    return render_template('/admin/message.html', messages = messages, success_message=success_message)

@bp.route('/admin/send-email', methods=('GET', 'POST'))
@login_required
@admin_required
def send_email():
    send_success = None
    note = ''

    if request.method == 'POST':
        try:
            email_message = request.form['email']
            subject = request.form['subject']
            
            if len(email_message) < 10 or len(subject) < 6:
                note = 'short'
                send_success = False
            else:
                messages = []

                query_string = text('SELECT email from bet_user')
                result = get_db().session.execute(query_string)

                for user in result.fetchall():
                    messages.append(create_message(sender='me', to=user.email, subject=subject, message_text=email_message))

                send_messages(messages=messages)
                send_success = True
        except:
            print('Error sending admin email to everyone')
            send_success = False

    return render_template('/admin/send-email.html', send_success=send_success, note = note)

@bp.route('/admin/odd', methods=('GET', 'POST'))
@login_required
@admin_required
def odd():
    matches = []

    query_string = text('SELECT id, time, team1, team2, odd1, oddX, odd2, max_bet FROM match')
    result = get_db().session.execute(query_string)

    for match in result.fetchall():
        query_string = text('SELECT translation FROM team_translation WHERE name=:name AND language=:language')

        result1 = get_db().session.execute(query_string, {'name' : match.team1, 'language' :  g.user['language']})
        team1_local = result1.fetchone()
        result2 = get_db().session.execute(query_string, {'name' : match.team2, 'language' :  g.user['language']})
        team2_local = result2.fetchone()

        if team1_local is None or team2_local is None or team1_local.translation == '' or team2_local.translation == '':
            continue

        match_dict : dict = match._asdict()
        match_dict['team1'] = team1_local.translation
        match_dict['team2'] = team2_local.translation

        matches.append(match_dict)

    matches.sort(key=lambda match : datetime.strptime(match['time'], '%Y-%m-%d %H:%M'))

    return render_template('/admin/odd.html', matches=matches)

@bp.route('/admin/odd/edit', methods=('GET', 'POST'))
@login_required
@admin_required
def odd_edit():
    if request.method == 'GET':
        matchIDString = request.args.get('matchID')

        if matchIDString is not None:
            matchID : int = int(matchIDString)

            query_string = text('SELECT team1, team2, ID, odd1, oddX, odd2, time, round, max_bet FROM match WHERE ID=:matchID')
            result = get_db().session.execute(query_string, {'matchID,' : matchID})
            match = result.fetchone()

            query_string = text('SELECT translation FROM team_translation WHERE name=:name AND language=:language')
            
            result1 = get_db().session.execute(query_string, {'name': match.team1, 'language' : g.user['language']})
            team1_local = result1.fetchone()

            result2 = get_db().session.execute(query_string, {'name': match.team2, 'language' : g.user['language']})
            team2_local = result2.fetchone()

            match_dict : dict = match._asdict()
            match_dict['team1'] = team1_local.translation
            match_dict['team2'] = team2_local.translation
            return render_template('/admin/odd-edit.html', match=match_dict)
        else:
            return redirect(url_for('admin.odd'))

    elif request.method == 'POST':
        dict = request.form
        odd1 = dict['odd1']
        oddX = dict['oddX']
        odd2 = dict['odd2']
        max_bet = dict['max_bet']
        
        ID = dict['ID']

        query_string = text('UPDATE match SET odd1=:o1, oddX=:ox, odd2=:o2, max_bet=max_bet WHERE ID=:ID')
        get_db().session.execute(query_string, {'o1' : odd1, 'ox' : oddX, 'o2' : odd2, 'max_bet ': max_bet, 'ID' : ID})
        get_db().session.commit()

        return redirect(url_for('admin.odd'))

@bp.route('/admin/group-evaluation', methods=('GET', 'POST'))
@login_required
@admin_required
def group_evaluation():    
    if request.method == 'POST':
        response_object = {}

        for key in request.json:
            i = 1
            for team in request.json[key]:
                query_string = text('UPDATE team SET position=:position WHERE name=:team')
                get_db().session.execute(query_string, {'position' : i, 'team ' : team})
                i += 1

        get_db().session.commit()

        response_object['result'] = 'OK'

        return jsonify(response_object)
    
    groups = []

    query_string = text('SELECT name, group_id, position FROM team')
    result = get_db().session.execute(query_string)

    for team in result.fetchall():
        group_of_team = None

        for group in groups:
            if group['ID'] == team.group_id:
                group_of_team = group
                break

        if group_of_team == None:
            group_of_team = {'ID' : team.group_id, 'teams': [] }
            groups.append(group_of_team)

        query_string = text('SELECT translation FROM team_translation WHERE name=:teamname AND language=:language')
        result2 = get_db().session.execute(query_string, {'teamname' : team.name, 'language' :  g.user['language']})
        team_local = result2.fetchone()

        group_of_team['teams'].append({'name' : team.name, 'local_name' : team_local.translation, 'position' :  team.position})

    already_submitted = True

    for group in groups:
        for team in group['teams']:
            if team['position'] is None:
                already_submitted = False
                break    

    if already_submitted:
        for group in groups:
            group['teams'].sort(key=lambda team : team['position'])

    return render_template('/admin/group-evaluation.html', groups = groups)

@bp.route('/admin/final-bet', methods=('GET', 'POST'))
@login_required
@admin_required
def final_bet():
    if request.method == 'POST':
        for key in request.form:
            success = request.form[key]
            if success == '':
                success = None

            query_string = text('UPDATE final_bet SET success=:success WHERE username=:username')
            get_db().session.execute(query_string, {'success' : success, 'username' : key})

        get_db().session.commit()
    else:
        pass

    players = []

    query_string = text('SELECT * FROM final_bet')
    result = get_db().session.execute(query_string)

    for final_bet in result.fetchall():
        query_string = text('SELECT translation FROM team_translation WHERE name=:team AND language=:language')
        result1 = get_db().session.execute(query_string, {'team' : final_bet.team, 'language' : g.user['language']})
        team = result1.fetchone()

        players.append({'name' : final_bet.username, 'team' : team.translation, 'result' : final_bet.result, 'success' : final_bet.success})

    return render_template('/admin/final-bet.html', players=players)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/admin/upload-team-data', methods=('GET', 'POST'))
@login_required
@admin_required
def upload_team_data():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'team' not in request.files and 'translation' not in request.files:
            flash('No file part')
            return redirect(request.url)
        team_file = request.files['team']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if team_file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        translation_file = request.files['translation']

        if translation_file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if team_file and allowed_file(team_file.filename) and translation_file and allowed_file(translation_file.filename):
            team_file_name = secure_filename(team_file.filename)
            team_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], team_file_name))

            translation_file_name = secure_filename(translation_file.filename)
            translation_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], translation_file_name))

            initialize_teams(team_file_name=team_file_name, translation_file_name=translation_file_name)
            initialize_matches()
            
            flash('UPLOAD_OK')
            return redirect(url_for('admin.admin_page'))

    return render_template('/admin/upload-team-data.html')