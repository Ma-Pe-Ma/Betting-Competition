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

bp = Blueprint("match", __name__, '''url_prefix="/group"''')

@bp.route("/match", methods=("GET", "POST"))
@login_required
def match_bet():
    
    if request.method == "GET":
        matchIDString = request.args.get("matchID")

        if (matchIDString is not None):
            matchID : int = int(matchIDString)
            print ("matchID " + str(matchID))
        else:
            pass

        from collections import namedtuple

        Match = namedtuple("MATCH", "ID, team1, team2, odd1, oddX, odd2, time, type, goal1, goal2, bet")

        match = Match(ID=1, team1="Olaszország", team2="Anglia", odd1=1, oddX=1, odd2=3, time="július 2 - 18:00", type="A csoport / 1. kör", goal1 = None, goal2 = 13, bet="11")

        return render_template("match-bet.html", match=match)

    elif request.method == "POST":
        print("POST REQUEST!")
        dict = request.form
        for key in dict:
            print('form key '+dict[key])

        print("group form: " + str(request.form.keys))
        return redirect(url_for("home.homepage"))
    

#https://stackoverflow.com/questions/17057191/redirect-while-passing-arguments