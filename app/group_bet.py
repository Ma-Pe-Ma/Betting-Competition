from os import stat_result
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

bp = Blueprint("group", __name__, '''url_prefix="/group"''')

deadline = datetime(2012, 7, 25, 7, 56, tzinfo=timezone.utc)
group_evaulation_time = datetime(2013, 7, 25, 7, 56, tzinfo=timezone.utc)

start_amount = 2000

def before_deadline():
    if request.method == "POST":
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
    
    from collections import namedtuple
    groups = []
    teams = []

    Team = namedtuple("Team", "id, name")

    Group = namedtuple("Group", "ID, teams, bet")
    hun = Team(id="HUN", name="Trinidad- és tobagó")
    ger = Team(id="GER", name="Észak-Macedónia")
    por = Team(id="POR", name="Amerikai Egyesült Államok")
    fra = Team(id="FRA", name="Franciaország")

    teams.append(hun)
    teams.append(ger)
    teams.append(por)
    teams.append(fra)

    groupA = Group(ID = "A", teams=teams, bet="174")
    groupB = Group(ID = "B", teams=teams, bet="111")

    groups.append(groupA)
    groups.append(groupB)

    return render_template("groupBet/group-edit.html", username = g.user["username"], admin=g.user["admin"], start_amount=start_amount, final_team ="GER", final_result = 3, final_result_bet = 11, groups = groups)

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