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

from collections import namedtuple
from app.score_calculator import *
from app.standings import get_current_points_by_player

bp = Blueprint("home", __name__, '''url_prefix="/group"''')

Day = namedtuple("Day", "number, date, name, matches")
Match = namedtuple("MATCH", "ID, time, type, team1, team2, odd1, oddX, odd2, bet, goal1, goal2, max_bet")

day_names = ["hétfő", "kedd", "szerda", "csütörtök", "péntek", "szombat", "vasárnap"]

def sorting_date(day):
    return datetime.strptime(day.date, "%Y-%m-%d")

def sorting_time(match):
    return datetime.strptime(match.time, "%H:%M")


@bp.route("/", methods=("GET",))
@login_required
def homepage():

    match_id = request.args.get("matchID")

    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))
    
    for row in get_db().execute("SELECT * FROM messages",()):
        flash(row["message"])

    days = []

    for match in get_db().execute("SELECT * FROM match WHERE DATETIME(time) > ?", (utc_now.strftime("%Y-%m-%d %H:%M"),)):
        match_time = datetime.strptime(match["time"], "%Y-%m-%d %H:%M")
        match_time = match_time.replace(tzinfo=tz.gettz('UTC'))
        
        #object holding the correct time adjusted to timezone
        match_time_local = match_time.astimezone(local_zone)   

        #the local time's date string
        match_date = match_time_local.strftime("%Y-%m-%d")
        #the local time's time string
        match_time_string = match_time_local.strftime("%H:%M")        

        match_bet = get_db().execute("SELECT * FROM match_bet WHERE (username = ? AND match_id = ? )", (g.user["username"], match["id"])).fetchone()

        goal1 = ""
        goal2 = ""
        bet = "-"

        if match_bet is not None:
            bet = match_bet["bet"]
            goal1 = match_bet["goal1"]
            goal2 = match_bet["goal2"] 
        else:
            print("Matchbet is none?" + str(match["id"]))

        match_object = Match(ID=match["id"], time=match_time_string, type=match["round"], team1=match["team1"], team2=match["team2"], odd1=match["odd1"], oddX=match["oddX"], odd2=match["odd2"], bet=bet, goal1=goal1, goal2=goal2, max_bet=match["max_bet"])

        match_day = None

        for day in days:
            if day.date == match_date:
                match_day = day

        if match_day == None:
            match_day = Day(number = 0, date=match_date, name=day_names[match_time_local.weekday()], matches=[])
            days.append(match_day) 

        match_day.matches.append(match_object)

    days.sort(key=sorting_date)
    modified_days = []

    i = 1
    for day in days:
        day.matches.sort(key=sorting_time)
        modified_days.append(day._replace(number = i))
        i += 1

    days.clear()

    return render_template("home-page.html", username = g.user["username"], admin=g.user["admin"], days=modified_days, current_amount=get_current_points_by_player(g.user["username"]), match_id = match_id)