from app import auth
from flask import Blueprint
from flask import redirect
from flask import g
from flask import flash
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask import Markup
from app.db import get_db
from app.auth import login_required

bp = Blueprint("previous", __name__, '''url_prefix="/group"''')

@bp.route("/prev", methods=("GET", "POST"))
@login_required
def prev_bets():
    from collections import namedtuple

    if request.args.get("name") is not None:
        Match = namedtuple("MATCH", "ID, type, team1, team2, result1, result2, odd1, oddX, odd2, goal1, goal2, bet, prize, bonus, balance")
        matches1 = []
        matches1.append(Match(ID="1", type="A csoport / 1.kör", team1="Olaszország", team2="Anglia", result1=1, result2=1, odd1=1.7, oddX=4.86, odd2=9.2, goal1=4, goal2=3, bet=33, prize=47, bonus=2, balance=2456))
        matches1.append(Match(ID="2", type="A csoport / 1.kör", team1="Észak-Macedónia", team2="Észak-Macedónia", result1=0, result2=0, odd1=1.7, oddX=4.86, odd2=9.2, goal1=4, goal2=3, bet=33, prize=47, bonus=2, balance=2456))

        matches2 = []
        matches2.append(Match(ID="3", type="A csoport / 1.kör", team1="Németország", team2="Magyarország", result1=2, result2=2, odd1=1.7, oddX=4.86, odd2=9.2, goal1=4, goal2=3, bet=33, prize=47, bonus=2, balance=2456))
        matches2.append(Match(ID="4", type="A csoport / 1.kör", team1="Franciaország", team2="Portugália", result1=2, result2=2, odd1=1.7, oddX=4.86, odd2=9.2, goal1=4, goal2=3, bet=33, prize=47, bonus=2, balance=2456))

        Day = namedtuple("Day", "number, date, name, matches")
    
        days = []
        days.append(Day(number = 1, date="2021-07-26", name="péntek", matches=matches1))
        days.append(Day(number = 2, date="2021-07-27", name="péntek", matches=matches2))

        defaultResultNode = render_template("previous-bet/previous-day-match.html", days = days, group_evaulation_date = "2021-07-27", group_bonus = 5000, new_balance="7415")

        print("name: " + request.args.get("name"))
        return defaultResultNode

    players = get_db().execute("SELECT username FROM user WHERE NOT username='RESULT'", ())

    return render_template("previous-bet/previous-bets.html", username = g.user["username"], admin=g.user["admin"], players=players)