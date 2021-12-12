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

from app import home_page

from collections import namedtuple
import datetime
from dateutil import tz
Match = namedtuple("MATCH", "ID, team1, team2, odd1, oddX, odd2, time, type, goal1, goal2, bet, max_bet")

bp = Blueprint("match", __name__, '''url_prefix="/group"''')

from datetime import datetime
from app.configuration import local_zone

@bp.route("/match", methods=("GET", "POST"))
@login_required
def match_bet():
    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))

    user_name = g.user["username"]
    
    if request.method == "GET":
        matchIDString = request.args.get("matchID")

        if (matchIDString is not None):
            matchID : int = 0
            try:    
                matchID = int(matchIDString)
            except ValueError:
                # TODO: redirect message
                pass            

            match_from_db = get_db().execute("SELECT team1, team2, odd1, oddX, odd2, time, round, max_bet FROM match WHERE id=?", (matchID,)).fetchone()            
            match_time_utc = datetime.strptime(match_from_db["time"], "%Y-%m-%d %H:%M")
            match_time_utc = match_time_utc.replace(tzinfo=tz.gettz('UTC'))

            # if match time is before now then 
            if match_time_utc < utc_now:
                # TODO: redirect message
                return redirect(url_for("home.homepage"))

            #determine local time objects
            match_time_local = match_time_utc.astimezone(local_zone)
            match_date = match_time_local.strftime("%Y-%m-%d")
            match_time = match_time_local.strftime("%H:%M")        

            #description strings on client
            dateString = match_date + " - " +  home_page.day_names[match_time_local.weekday()] + " " + match_time
            typeString = match_from_db["round"]

            goal1 = ""
            goal2 = ""
            bet = ""

            # get user bet (if exists)
            user_match_bet = get_db().execute("SELECT goal1, goal2, bet FROM match_bet WHERE username=? AND match_id = ?", (user_name, matchID)).fetchone()

            if user_match_bet is not None:
                goal1 = user_match_bet["goal1"]
                goal2 = user_match_bet["goal2"]
                bet = user_match_bet["bet"]

            match = Match(ID=matchID, team1=match_from_db["team1"], team2=match_from_db["team2"], odd1=match_from_db["odd1"], oddX=match_from_db["oddX"], odd2=match_from_db["odd2"], time=dateString, type=typeString, goal1 = goal1, goal2 = goal2, bet=bet, max_bet=match_from_db["max_bet"])
            return render_template("match-bet.html", match=match)

        else:
            # TODO: redirect message
            return redirect(url_for("home.homepage"))

    elif request.method == "POST":
        dict = request.form

        match_id = request.form["matchID"]
        goal1 = request.form["goal1"]
        goal2 = request.form["goal2"]
        bet = request.form["bet"]
        
        match_from_db = get_db().execute("SELECT max_bet, time FROM match WHERE id=?", (match_id,)).fetchone()
        
        match_time_utc = datetime.strptime(match_from_db["time"], "%Y-%m-%d %H:%M")
        match_time_utc = match_time_utc.replace(tzinfo=tz.gettz('UTC'))

        #check if match time is before now if yes redirect to homepage
        if match_time_utc < utc_now:
            #TODO: redirect message
            return redirect(url_for("home.homepage"))
        
        #get the max bet for the match
        max_bet = match_from_db["max_bet"]

        try:
            bet_number = int(bet)

            # handle if player tries to cheat
            if bet_number > max_bet:
                bet_number = max_bet
            elif bet_number < 0:
                bet_number = 0

        except ValueError:
            #TODO notify user about bad number format
            return render_template("match-bet.html", )

        try:
            goal1_number = int(goal1)
            goal2_number = int(goal2)
        except ValueError:
            #TODO notify user about bad number format
            return render_template("match-bet.html", )

        # rude solution if entry not exists create it it does then update
        if get_db().execute("SELECT * FROM match_bet WHERE match_id=? AND username=?", (match_id, user_name)).fetchone() is None:
            get_db().execute("INSERT INTO match_bet (match_id, username, bet, goal1, goal2) VALUES(?,?,?,?,?)", (match_id, user_name, bet_number, goal1_number, goal2_number))
        else:
            get_db().execute("UPDATE match_bet SET bet = ?, goal1 = ?, goal2 = ? WHERE match_id = ? AND username = ?", (bet_number, goal1_number, goal2_number, match_id, user_name))

        get_db().commit()

        return redirect(url_for("home.homepage", matchID=match_id))
    

#https://stackoverflow.com/questions/17057191/redirect-while-passing-arguments