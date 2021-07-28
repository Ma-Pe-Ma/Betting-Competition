from os import name
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

from datetime import date, datetime, timezone
from dateutil import tz

from collections import namedtuple

bp = Blueprint("home", __name__, '''url_prefix="/group"''')
local_zone = tz.gettz('Europe/Budapest')

Day = namedtuple("Day", "date, name, matches")
Match = namedtuple("MATCH", "ID, time, type, team1, team2, odd1, oddX, odd2, bet, goal1, goal2")

day_names = ["hétfő", "kedd", "szerda", "csütörtök", "péntek", "szombat", "vasárnap"]

@bp.route("/", methods=("GET", "POST"))
@login_required
def homepage():
    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))
    
    for row in get_db().execute("SELECT * FROM messages",()):
        flash(row["message"])


    days = []

    for match in get_db().execute("SELECT * FROM match WHERE DATETIME(time) > ?", (utc_now.strftime("%Y-%m-%d %H:%M"),)):
        match_time = datetime.strptime(match["time"], "%Y-%m-%d %H:%M")
        match_time.replace(tzinfo=tz.gettz('UTC'))
        
        match_time_local = match_time.astimezone(local_zone)   

        match_date = match_time.strftime("%Y-%m-%d")
        match_time_string = match_time.strftime("%H:%M")

        match_day = None

        match_bet = get_db().execute("SELECT * FROM match_bets WHERE (username = ? AND match_id = ? )", (g.user["username"], match["id"])).fetchone()

        goal1 = ""
        goal2 = ""
        bet = "-"

        if match_bet is not None:
            bet = match_bet["bet"]
            goal1 = match_bet["goal1"]
            goal2 = match_bet["goal2"]        

        match_object = Match(ID=match["id"], time=match_time_string, type=match["round"], team1=match["team1"], team2=match["team2"], odd1=match["odd1"], oddX=match["oddX"], odd2=match["odd2"], bet=bet, goal1=goal1, goal2=goal2)

        for day in days:
            if day.date == match_date:
                match_day = day

        if match_day == None:
            match_day = Day(date=match_date, name=day_names[match_time_local.weekday()], matches=[])
            days.append(match_day) 

        match_day.matches.append(match_object)

    return render_template("home-page.html", username = g.user["username"], admin=g.user["admin"], days=days)