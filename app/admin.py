from app.score_calculator import sort_teams
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
from app.auth import admin_required, login_required

bp = Blueprint("admin", __name__, '''url_prefix="/group"''')

# groupbet, matchbet feedback for result of posting in client #message after redirect (after posting, group or match!)
# calculate + add final_bet win amount to standings after last match

# user config page
# request csv update by button

# flask-init db, read teams + matches from csv!
# email for everyone - implement sending
# timed email notifications!
# configure schedulings properly
# daily standings reminder at end of match day?
# backup sqlite database at night by email

# change app secure key!
# deployment
# disqus
# replace logo
# html template -> removing deadlinks + dashboard problem + username problem
# remove comments

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
        matches.append(Match(ID=match_prefab["id"], time=match_prefab["time"], team1=match_prefab["team1"], team2=match_prefab["team2"], odd1=match_prefab["odd1"], oddX=match_prefab["oddX"], odd2=match_prefab["odd2"], max_bet=match_prefab["max_bet"]))

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
        for key in request.json:
            i = 1
            for team in request.json[key]:
                get_db().execute("UPDATE team SET position=? WHERE name = ?", (i, team))
                i += 1

        get_db().commit()

        return "OK"
    
    Group = namedtuple("Group", "ID, teams")
    Team = namedtuple("Team", "name, hun_name, position")

    groups = []

    for team in get_db().execute("SELECT name, hun_name, group_id, position FROM team").fetchall():
        group_of_team = None

        for group in groups:
            if group.ID == team["group_id"]:
                group_of_team = group
                break

        if group_of_team == None:
            group_of_team = Group(ID=team["group_id"], teams=[])
            groups.append(group_of_team)

        group_of_team.teams.append(Team(name=team["name"], hun_name=team["hun_name"], position=team["position"]))

    already_submitted = True

    for group in groups:
        for team in group.teams:
            if team.position is None:
                already_submitted = False
                break    

    if already_submitted:
        for group in groups:
            group.teams.sort(key=sort_teams)

    return render_template("admin/group-evaluation.html", username = g.user["username"], admin=g.user["admin"], groups = groups)

@bp.route("/admin/final-bet", methods=("GET", "POST"))
@login_required
@admin_required
def final_bet():
    if request.method == "POST":
        print("final bet keys: " + str(request.form.keys))

        for key in request.form:
            get_db().execute("UPDATE final_bet SET success=? WHERE username=?", (request.form[key], key))
            print("value: " + request.form[key])

        get_db().commit()

    else:
        pass

    Player = namedtuple("Player", "name, team, result, success")
    players = []

    for final_bet in get_db().execute("SELECT * FROM final_bet", ()).fetchall():
        team = get_db().execute("SELECT hun_name FROM team WHERE name=?", (final_bet["team"],)).fetchone()
        players.append(Player(name=final_bet["username"], team=team["hun_name"], result=final_bet["result"], success=final_bet["success"]))
        print("success: " + str(final_bet["success"]))

    return render_template("admin/final-bet.html", username = g.user["username"], admin=g.user["admin"], players=players)