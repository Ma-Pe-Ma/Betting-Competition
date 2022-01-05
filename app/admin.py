from collections import namedtuple
from typing import Match
from app import auth
from flask import Blueprint
from flask import redirect
from flask import g
from flask import flash
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from app.db import get_db
from flask import jsonify
from app.auth import admin_required, login_required

from app.tools.ordering import order_teams

bp = Blueprint("admin", __name__, '''url_prefix="/group"''')

# request result csv update by button
# implement parsing result csv in file_request.py

# flask-init db, read teams + matches from csv! # when reading from csv, add position to team!!!!!!!
# email for everyone - implement sending
# daily standings reminder at end of match day
# backup sqlite database at night by email to admins

# auth oldal beégett stringjeit kiszervezni a html-be, inkább a nyelv specifikus dolgok kiszervezése a html-ből
# commenting sql schema too + removing default values
# readme + setup + user manual + deployment (apache or docker/heroku?)
# javascriptek + html-ek átnézése
# out comment starting csv fetch in init.py

# cleanup __init__.py
# rethink url paths
# fix title of pages 
# flask babel - multilanguage
# felesleges html oldalak törlése
# disqus
# replace logo
# replace icons at sidebar
# html template -> removing deadlinks + dashboard problem (?) + username problem (?)
# remove comments from HTML
# more starters gomb

# CHECK TODO-s


@bp.route("/admin", methods=("GET",))
@login_required
@admin_required
def admin_page():
    return render_template("admin/admin.html", username = g.user["username"], admin=g.user["admin"])

@bp.route("/admin/message", methods=("GET", "POST"))
@login_required
@admin_required
def message():
    success_message = None

    if request.method == "POST":
        for key in request.form:
            get_db().execute("UPDATE messages SET message=? WHERE label=?", (request.form[key],key))
        
        get_db().commit()
        success_message = True
    
    Message = namedtuple("Message", "id, text")

    messages = []

    for message_prefab in get_db().execute("SELECT * from messages").fetchall():
        messages.append(Message(id= message_prefab["label"], text=message_prefab["message"]))

    return render_template("admin/message.html", username = g.user["username"], admin=g.user["admin"], messages = messages, success_message=success_message)

@bp.route("/admin/send-email", methods=("GET", "POST"))
@login_required
@admin_required
def send_email():
    send_success = None
    note = ""

    if request.method == "POST":
        
        try:
            email_message = request.form["email"]
            
            if len(email_message) < 10:
                note = "short"
                send_success = False
            else:
                print("email_message: " + email_message)
                # send email from here
                send_success = True
        except:
            print("exception occured")
            send_success = False

    return render_template("admin/send-email.html", username = g.user["username"], admin=g.user["admin"], send_success=send_success, note = note)

@bp.route("/admin/odd", methods=("GET", "POST"))
@login_required
@admin_required
def odd():
    Match = namedtuple("Match", "ID, time, team1, team2, odd1, oddX, odd2, max_bet")

    matches = []

    for match_prefab in get_db().execute("SELECT id, time, team1, team2, odd1, oddX, odd2, max_bet FROM match "):
        team1_local = get_db().execute("SELECT local_name FROM team WHERE name=?", (match_prefab["team1"],)).fetchone()
        team2_local = get_db().execute("SELECT local_name FROM team WHERE name=?", (match_prefab["team2"],)).fetchone()

        matches.append(Match(ID=match_prefab["id"], time=match_prefab["time"], team1=team1_local["local_name"], team2=team2_local["local_name"], odd1=match_prefab["odd1"], oddX=match_prefab["oddX"], odd2=match_prefab["odd2"], max_bet=match_prefab["max_bet"]))

    return render_template("admin/odd.html", username = g.user["username"], admin=g.user["admin"], matches=matches)

@bp.route("/admin/odd/edit", methods=("GET", "POST"))
@login_required
@admin_required
def odd_edit():
    if request.method == "GET":
        matchIDString = request.args.get("matchID")

        from collections import namedtuple
        Match = namedtuple("MATCH", "ID, team1, team2, odd1, oddX, odd2, time, type, max_bet")

        if (matchIDString is not None):
            matchID : int = int(matchIDString)
            print ("matchID " + str(matchID))

            match_prefab = get_db().execute("SELECT team1, team2, ID, odd1, oddX, odd2, time, round, max_bet FROM match WHERE ID=?", (matchID,)).fetchone()

            match = Match(ID=matchID, team1=match_prefab["team1"], team2=match_prefab["team2"], odd1=match_prefab["odd1"], oddX=match_prefab["oddX"], odd2=match_prefab["odd2"], time=match_prefab["time"], type=match_prefab["round"], max_bet=match_prefab["max_bet"])
        else:
            return redirect(url_for("admin.odd"))

    elif request.method == "POST":
        dict = request.form
        odd1 = dict["odd1"]
        oddX = dict["oddX"]
        odd2 = dict["odd2"]
        max_bet = dict["max_bet"]
        print("max_bet: " + str(max_bet))
        ID = dict["ID"]

        get_db().execute("UPDATE match SET odd1=?, oddX=?, odd2=?, max_bet=? WHERE ID=?", (odd1, oddX, odd2, max_bet, ID))
        get_db().commit()

        print("group form: " + str(request.form.keys))
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
                get_db().execute("UPDATE team SET position=? WHERE name = ?", (i, team))
                i += 1

        get_db().commit()

        response_object['result'] = 'OK'

        return jsonify(response_object)
    
    Group = namedtuple("Group", "ID, teams")
    Team = namedtuple("Team", "name, local_name, position")

    groups = []

    for team in get_db().execute("SELECT name, local_name, group_id, position FROM team").fetchall():
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
            group.teams.sort(key=order_teams)

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

            get_db().execute("UPDATE final_bet SET success=? WHERE username=?", (success, key))

        get_db().commit()
    else:
        pass

    Player = namedtuple("Player", "name, team, result, success")
    players = []

    for final_bet in get_db().execute("SELECT * FROM final_bet", ()).fetchall():
        team = get_db().execute("SELECT local_name FROM team WHERE name=?", (final_bet["team"],)).fetchone()
        players.append(Player(name=final_bet["username"], team=team["local_name"], result=final_bet["result"], success=final_bet["success"]))

    return render_template("admin/final-bet.html", username = g.user["username"], admin=g.user["admin"], players=players)