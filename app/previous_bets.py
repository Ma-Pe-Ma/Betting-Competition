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

from datetime import datetime
from dateutil import tz

from app.score_calculator import *

bp = Blueprint("previous", __name__, '''url_prefix="/group"''')

Day = namedtuple("Day", "number, date, name, matches")
Match = namedtuple("Match", "ID, type, time, team1, team2, result1, result2, odd1, oddX, odd2, goal1, goal2, bet, prize, bonus, balance, color")

@bp.route("/prev", methods=("GET", "POST"))
@login_required
def prev_bets():
    user_name = request.args.get("name")

    if user_name is not None:
        utc_now = datetime.utcnow()
        utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))
    
        start_amount = starting_bet_amount - get_group_bet_amount(user_name)
        group_bonus = get_group_win_amount(user_name)
        balance_after_group = 0

        days = []

        for previous_match in get_db().execute("SELECT * FROM match WHERE DATETIME(time) < ?", (utc_now.strftime("%Y-%m-%d %H:%M"),)):
            match_time = datetime.strptime(previous_match["time"], "%Y-%m-%d %H:%M")
            match_time = match_time.replace(tzinfo=tz.gettz('UTC'))
            
            match_time_local = match_time.astimezone(local_zone)   

            match_date = match_time_local.strftime("%Y-%m-%d")
            match_time_string = match_time_local.strftime("%H:%M")

            match_bet = get_db().execute("SELECT * FROM match_bet WHERE username=? AND match_id = ?",(user_name, previous_match["id"] )).fetchone()

            result1 = previous_match["goal1"]
            result2 = previous_match["goal2"]

            odd1 = previous_match["odd1"]
            oddX = previous_match["oddX"]
            odd2 = previous_match["odd2"]

            goal1 = ""
            goal2 = ""
            bet = ""
            bonus = 0
            prize = 0

            color = ""

            if match_bet is not None:
                goal1 = match_bet["goal1"]
                goal2 = match_bet["goal2"]
                bet = match_bet["bet"]

                if result1 is not None :
                    result_value = prize_result(result1, result2, goal1, goal2)

                    color = "lightcoral"

                    if result_value.actual == result_value.bet:
                        if result_value.actual == 1:
                            prize = bet * odd1
                        elif result_value.actual == -1:
                            prize = bet * odd2
                        else:
                            prize = bet * oddX
                        
                        bonus = bet * result_value.bonus_multiplier

                        color = "lime"

            match_object = Match(previous_match["id"], time = match_time_string, type=previous_match["round"], team1=previous_match["team1"], team2=previous_match["team2"], result1=result1, result2=result2, odd1=odd1, oddX=oddX, odd2=odd2, goal1=goal1, goal2=goal2, bet=bet, prize=prize, bonus=bonus, balance=0, color=color )

            match_day = None

            for day in days:
                if day.date == match_date:
                    match_day = day

            if match_day is None:
                match_day = Day(number = 0, date=match_date, name=day_names[match_time_local.weekday()], matches=[])
                days.append(match_day) 

            match_day.matches.append(match_object)

        days.sort(key=sorting_date)
        amount = start_amount

        modified_days = []

        i = 1

        for day in days:
            day.matches.sort(key=sorting_time)

            modifed_matches = []

            for match in day.matches:
                amount = amount + match.prize + match.bonus
                
                print("balance: " + str(amount))
                modifed_matches.append(match._replace(balance=amount))
        
            day.matches.clear()
            modified_days.append(day._replace(number = i, matches = modifed_matches))

            if day.date == group_evaluation_date:
                amount = amount + group_bonus
                balance_after_group = amount
            i += 1

        days.clear()     

        defaultResultNode = render_template("previous-bet/previous-day-match.html", days = modified_days, group_evaluation_date = group_evaluation_date, start_amount = start_amount, group_bonus = group_bonus, balance_after_group = balance_after_group)
        return defaultResultNode

    players = get_db().execute("SELECT username FROM user WHERE NOT username='RESULT'", ())

    return render_template("previous-bet/previous-bets.html", username = g.user["username"], admin=g.user["admin"], players=players)