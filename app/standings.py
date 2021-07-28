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
from app.auth import login_required

bp = Blueprint("standings", __name__, '''url_prefix="/group"''')

@bp.route("/standings", methods=("GET", "POST"))
@login_required
def standings():

    from collections import namedtuple
    Player = namedtuple("Player", "nick, days")
    players = []

    Day = namedtuple("Day", "date, point")

    days1 = []
    days1.append(Day(date="2014, 00, 01",point="979"))
    days1.append(Day(date="2014, 00, 02",point="2000"))

    days2 = []
    days2.append(Day(date="2014, 00, 01",point="301"))
    days2.append(Day(date="2014, 00, 02",point="350"))

    players.append(Player(nick="MPM", days=days1))
    players.append(Player(nick="Sanyi", days=days2))

    return render_template("standings.html", username = g.user["username"], admin=g.user["admin"], players=players)


#https://canvasjs.com/html5-javascript-line-chart/
#https://stackoverflow.com/questions/35854244/how-can-i-create-a-horizontal-scrolling-chart-js-line-chart-with-a-locked-y-axis