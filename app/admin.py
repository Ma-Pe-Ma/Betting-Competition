from collections import namedtuple
from flask import Blueprint
from flask import redirect
from flask import g
from flask import flash
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from app.database_manager import download_data_csv, initialize_matches, initialize_teams
from app.db import get_db
from flask import jsonify
from app.auth import admin_required, login_required
from app.gmail_handler import create_message, send_messages
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
import os

bp = Blueprint("admin", __name__, '''url_prefix="/group"''')

# CHECK TODO-s

#BACKEND
# daily standings reminder at end of match day + welcome message [email]
# rethink initialization (scheduling, backuping, database updating etc.)
# outcomment starting csv fetch in init.py + start daily checker immidiately (check if match already started then!)

# rethink url paths
# LOGGING!!!!!!!!!!! (printek törlése)

#FRONTEND
# auth oldal beégett stringjeit kiszervezni a html-be, inkább a nyelv specifikus dolgok kiszervezése a html-ből
# javascriptek + html-ek átnézése, remove comments from HTML

# backlog:
# flask babel - multilanguage

#README: gmail, remark [docker], heroku, configuration, first as admin upload csv + apache2 + wsgi, fixture note, init-db-with data, TESTING: POSTGRES + OSVARIABLES

@bp.route("/admin", methods=("GET",))
@login_required
@admin_required
def admin_page():
    return render_template("admin/admin.html", username = g.user["username"], admin=g.user["admin"])

@bp.route("/admin/fetch-match", methods=("GET",))
@login_required
@admin_required
def fetch_match():
    result = {}
    result['result'] = download_data_csv()
    return jsonify(result)

@bp.route("/admin/message", methods=("GET", "POST"))
@login_required
@admin_required
def message():
    success_message = None

    if request.method == "POST":
        for key in request.form:
            get_db().cursor().execute("UPDATE messages SET message=%s WHERE id=%s", (request.form[key],key))
        
        get_db().commit()
        success_message = True
    
    Message = namedtuple("Message", "id, text")

    messages = []

    cursor = get_db().cursor()
    cursor.execute("SELECT * from messages")

    for message_prefab in cursor.fetchall():
        messages.append(Message(id=message_prefab["id"], text=message_prefab["message"]))

    return render_template("admin/message.html", username = g.user["username"], admin=g.user["admin"], messages = messages, success_message=success_message)

@bp.route("/admin/send-email", methods=("GET", "POST"))
@login_required
@admin_required
def send_email():
    send_success = None
    note = ""

    if request.method == "POST":
        try:
            email_message = request.form['email']
            subject = request.form['subject']
            
            if len(email_message) < 10 or len(subject) < 6:
                note = "short"
                send_success = False
            else:
                messages = []

                cursor = get_db().cursor()
                cursor.execute("SELECT email from bet_user")

                for user in cursor.fetchall():
                    messages.append(create_message(sender='me', to=user['email'], subject=subject, message_text=email_message))

                send_messages(messages=messages)
                send_success = True
        except:
            print("Error sending admin email to everyone")
            send_success = False

    return render_template("admin/send-email.html", username = g.user["username"], admin=g.user["admin"], send_success=send_success, note = note)

@bp.route("/admin/odd", methods=("GET", "POST"))
@login_required
@admin_required
def odd():
    Match = namedtuple("Match", "ID, time, team1, team2, odd1, oddX, odd2, max_bet")

    matches = []

    cursor = get_db().cursor()
    cursor.execute("SELECT id, time, team1, team2, odd1, oddX, odd2, max_bet FROM match")

    for match_prefab in cursor.fetchall():
        cursor1 = get_db().cursor()
        cursor1.execute("SELECT local_name FROM team WHERE name=%s", (match_prefab["team1"],))
        team1_local = cursor1.fetchone()

        cursor2 = get_db().cursor()
        cursor2.execute("SELECT local_name FROM team WHERE name=%s", (match_prefab["team2"],))
        team2_local = cursor2.fetchone()

        if team1_local is None or team2_local is None or team1_local['local_name'] == '' or team2_local['local_name'] == '':
            continue

        matches.append(Match(ID=match_prefab["id"], time=match_prefab["time"], team1=team1_local["local_name"], team2=team2_local["local_name"], odd1=match_prefab["odd1"], oddX=match_prefab["oddx"], odd2=match_prefab["odd2"], max_bet=match_prefab["max_bet"]))

    matches.sort(key=lambda match : datetime.strptime(match.time, "%Y-%m-%d %H:%M"))

    return render_template("admin/odd.html", username = g.user["username"], admin=g.user["admin"], matches=matches)

@bp.route("/admin/odd/edit", methods=("GET", "POST"))
@login_required
@admin_required
def odd_edit():
    if request.method == "GET":
        matchIDString = request.args.get("matchID")

        from collections import namedtuple
        Match = namedtuple("Match", "ID, team1, team2, odd1, oddX, odd2, time, type, max_bet")

        if (matchIDString is not None):
            matchID : int = int(matchIDString)

            cursor = get_db().cursor()
            cursor.execute("SELECT team1, team2, ID, odd1, oddX, odd2, time, round, max_bet FROM match WHERE ID=%s", (matchID,))
            match_prefab = cursor.fetchone()

            cursor1 = get_db().cursor()
            cursor1.execute("SELECT local_name FROM team WHERE name=%s", (match_prefab["team1"],))
            team1_local = cursor1.fetchone()

            cursor2 = get_db().cursor()
            cursor2.execute("SELECT local_name FROM team WHERE name=%s", (match_prefab["team2"],))
            team2_local = cursor2.fetchone()

            match = Match(ID=matchID, team1=team1_local["local_name"], team2=team2_local["local_name"], odd1=match_prefab["odd1"], oddX=match_prefab["oddx"], odd2=match_prefab["odd2"], time=match_prefab["time"], type=match_prefab["round"], max_bet=match_prefab["max_bet"])
        else:
            return redirect(url_for("admin.odd"))

    elif request.method == "POST":
        dict = request.form
        odd1 = dict["odd1"]
        oddX = dict["oddX"]
        odd2 = dict["odd2"]
        max_bet = dict["max_bet"]
        
        ID = dict["ID"]

        get_db().cursor().execute("UPDATE match SET odd1=%s, oddX=%s, odd2=%s, max_bet=%s WHERE ID=%s", (odd1, oddX, odd2, max_bet, ID))
        get_db().commit()

        return redirect(url_for("admin.odd"))
    
    return render_template("admin/odd-edit.html", admin=g.user["admin"], match=match)

@bp.route("/admin/group-evaluation", methods=("GET", "POST"))
@login_required
@admin_required
def group_evaluation():
    
    if request.method == "POST":
        response_object = {}

        for key in request.json:
            i = 1
            for team in request.json[key]:
                get_db().cursor().execute("UPDATE team SET position=%s WHERE name=%s", (i, team))
                i += 1

        get_db().commit()

        response_object['result'] = 'OK'

        return jsonify(response_object)
    
    Group = namedtuple("Group", "ID, teams")
    Team = namedtuple("Team", "name, local_name, position")

    groups = []

    cursor = get_db().cursor()
    cursor.execute("SELECT name, local_name, group_id, position FROM team")

    for team in cursor.fetchall():
        group_of_team = None

        for group in groups:
            if group.ID == team["group_id"]:
                group_of_team = group
                break

        if group_of_team == None:
            group_of_team = Group(ID=team["group_id"], teams=[])
            groups.append(group_of_team)

        group_of_team.teams.append(Team(name=team["name"], local_name=team["local_name"], position=team["position"]))

    already_submitted = True

    for group in groups:
        for team in group.teams:
            if team.position is None:
                already_submitted = False
                break    

    if already_submitted:
        for group in groups:
            group.teams.sort(key=lambda team : team.position)

    return render_template("admin/group-evaluation.html", username = g.user["username"], admin=g.user["admin"], groups = groups)

@bp.route("/admin/final-bet", methods=("GET", "POST"))
@login_required
@admin_required
def final_bet():
    if request.method == "POST":
        for key in request.form:
            success = request.form[key]
            if success == "":
                success = None

            get_db().cursor().execute("UPDATE final_bet SET success=%s WHERE username=%s", (success, key))

        get_db().commit()
    else:
        pass

    Player = namedtuple("Player", "name, team, result, success")
    players = []

    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM final_bet", ())

    for final_bet in cursor.fetchall():
        cursor1 = get_db().cursor()
        cursor1.execute("SELECT local_name FROM team WHERE name=%s", (final_bet["team"],))

        team = cursor1.fetchone()
        players.append(Player(name=final_bet["username"], team=team["local_name"], result=final_bet["result"], success=final_bet["success"]))

    return render_template("admin/final-bet.html", username = g.user["username"], admin=g.user["admin"], players=players)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route("/admin/upload-team-data", methods=("GET", "POST"))
@login_required
@admin_required
def upload_team_data():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

            initialize_teams(file_name=filename)
            initialize_matches()
            
            flash('UPLOAD_OK')
            return redirect(url_for('admin.admin_page'))

    return render_template("admin/upload-team-data.html", username = g.user["username"], admin=g.user["admin"])