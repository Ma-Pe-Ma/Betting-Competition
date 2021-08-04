from os import name, stat_result
from app.auth import login_required
from flask import Blueprint
from flask import redirect
from flask import g
from flask import flash
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from app.db import get_db

from datetime import timezone, datetime
from collections import namedtuple

from app.score_calculator import *

bp = Blueprint("group", __name__, '''url_prefix="/group"''')

deadline = datetime(2022, 7, 25, 7, 56, tzinfo=timezone.utc)
group_evaulation_time = datetime(2013, 7, 25, 7, 56, tzinfo=timezone.utc)

Team = namedtuple("Team", "name, hun_name, position, top1, top2, top4, top16")
Group = namedtuple("Group", "ID, teams, bet")

def sort_groups(group):
    return group.ID

def sort_teams(team):
    return team.position

def before_deadline():
    if request.method == "GET":
        groups = []
        teams = []

        user_name = g.user["username"]

        user_bets = get_db().execute("SELECT team, position FROM team_bet WHERE username =?", (user_name,)).fetchall()

        if len(user_bets) == 0 :
            team_prefabs = get_db().execute("SELECT name, hun_name, group_id, top1, top2, top4, top16 FROM team", ()).fetchall()

            for team_prefab in team_prefabs:

                group_of_team = None

                for group in groups:
                    if group.ID == team_prefab["group_id"]:
                        group_of_team = group

                if group_of_team == None:
                    group_of_team = Group(ID=team_prefab["group_id"], teams=[], bet=0)
                    groups.append(group_of_team)
                
                team_nr = len(group_of_team.teams)
                group_of_team.teams.append(Team(name=team_prefab["name"], hun_name=team_prefab["hun_name"], position=(team_nr + 1), top1=team_prefab["top1"], top2=team_prefab["top2"], top4=team_prefab["top4"], top16=team_prefab["top16"]))

        else:
            for user_bet in user_bets:
                team_prefab = get_db().execute("SELECT name, hun_name, group_id, top1, top2, top4, top16 FROM team WHERE name = ?", (user_bet["team"],)).fetchone()

                group_of_team = None

                for group in groups:
                    if group.ID == team_prefab["group_id"]:
                        group_of_team = group

                if group_of_team == None:
                    group_bet = get_db().execute("SELECT bet FROM group_bet WHERE (username = ? AND group_ID = ?)", (user_name, team_prefab["group_id"],)).fetchone()
                    group_of_team = Group(ID=team_prefab["group_id"], teams=[], bet=group_bet["bet"])
                    groups.append(group_of_team)
                
                group_of_team.teams.append(Team(name=team_prefab["name"], hun_name=team_prefab["hun_name"], position=user_bet["position"], top1=team_prefab["top1"], top2=team_prefab["top2"], top4=team_prefab["top4"], top16=team_prefab["top16"]))

        groups.sort(key=sort_groups)

        for group in groups:
            group.teams.sort(key=sort_teams)

        final_bet = get_db().execute("SELECT team, bet, result FROM final_bet WHERE username = ?", (user_name,)).fetchone()

        return render_template("groupBet/group-edit.html", username = user_name, admin=g.user["admin"], start_amount=starting_bet_amount, final_team = final_bet["team"], final_result = final_bet["result"], final_result_bet = final_bet["bet"], groups = groups)

    elif request.method == "POST":
        print("group form: " + str(request.get_json()))

        group_bet = request.get_json()

        result = group_bet["final"]
        groups = group_bet["group"]

        for group in groups:
            print("key: " + group)
            print("order: " + str())

            bet = groups[group]["bet"]
            order = groups[group]["order"]

            print("bet: " + bet)
            print("order: " + str(order))

            i = 1
            for team in order:
                print(str(i) + ". team: " + team)
                i = i + 1

        return "okszi!"

def during_groupstage():
    if request.args.get("name") is not None:
        groups = []

        from collections import namedtuple
        Group = namedtuple("Group", "ID, first, second, third, fourth, bet_amount")
        groups.append(Group(ID="A",first="Magyarország", second="Szlovákia", third="Románia", fourth="Jugoszlávia", bet_amount="200"))
        groups.append(Group(ID="B",first="Ukrajna", second="Ausztria", third="Szlovénia", fourth="Horvátország", bet_amount="150"))

        return render_template("groupBet/group-during.html", groups=groups, amount_after=500)
    
    players = get_db().execute("SELECT username FROM user WHERE NOT username='RESULT'", ())

    return render_template("groupBet/group-choose.html", username = g.user["username"], admin=g.user["admin"], players=players)

def after_evaulation():
    if request.args.get("name") is not None:
        groups = []

        from collections import namedtuple
        Group = namedtuple("Group", "ID, result, bet, bet_amount, multiplier, multiplier_text, win_amount") 

        Result = namedtuple("Result", "first, second, third, fourth")

        result = Result(first="Magyarország", second="Szlovákia", third="Románia", fourth="Jugoszlávia")
        bet = Result(first=("Szlovákia", "green"), second=("Románia", "green"), third=("Jugoszlávia", "red"), fourth=("Magyarország", "blue"))

        groups.append(Group(ID="A",result=result, bet=bet, bet_amount="200", multiplier=4, multiplier_text="telitalálat", win_amount="310"))
        groups.append(Group(ID="B",result=result, bet=bet, bet_amount="144", multiplier=2, multiplier_text="két találat", win_amount="111"))

        return render_template("groupBet/group-after.html", groups=groups, total_bet=600, total_win=2000)
    
    players = get_db().execute("SELECT username FROM user WHERE NOT username='RESULT'", ())

    return render_template("groupBet/group-choose.html", username = g.user["username"], admin=g.user["admin"], players=players)

@bp.route("/group", methods=("GET", "POST"))
@login_required
def group_order():

    current_time = datetime.now(tz=timezone.utc)

    if current_time < deadline:
        return before_deadline()
    elif current_time < group_evaulation_time:
        return during_groupstage()
    else:
        return after_evaulation()