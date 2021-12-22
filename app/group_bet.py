from os import name, stat_result
from typing import NamedTuple, final
from app.auth import login_required
from flask import Blueprint
from flask import redirect
from flask import g
from flask import flash
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask import jsonify
from app.db import get_db

from datetime import timezone, datetime
from dateutil import tz
from collections import namedtuple

from app.configuration import starting_bet_amount, max_group_bet_value, max_final_bet_value
from app.configuration import group_deadline_time, group_evaluation_date
from app.tools.group_calculator import get_group_object, get_final_bet
from app.tools.score_calculator import get_group_and_final_bet_amount, get_group_win_amount2

bp = Blueprint("group", __name__, '''url_prefix="/group"''')

def before_deadline():
    user_name = g.user["username"]

    if request.method == "GET":
        groups = get_group_object(user_name=user_name)
        final_bet_object = get_final_bet(user_name=user_name)

        return render_template("groupBet/group-edit.html", username = user_name, admin=g.user["admin"], start_amount=starting_bet_amount, max_group_bet_value = max_group_bet_value, max_final_bet_value=max_final_bet_value, final_bet = final_bet_object, groups = groups)

    elif request.method == "POST":
        bet_object = request.get_json()
        response_object = {}

        # parsing and checking final bet properties
        final = bet_object["final"]

        final_team = final["team"]
        if get_db().execute("SELECT name FROM team WHERE name = ?", (final_team,)).fetchone() is None:
            response_object['result'] = 'error'
            response_object['info'] = 'FINAL_TEAM'
        try:
            final_result = int(final["result"])
            if final_result < 0 or 3 < final_result:
                response_object['result'] = 'error'
                response_object['info'] = 'FINAL_RESULT'
        except ValueError:
            response_object['result'] = 'error'
            response_object['info'] = 'FINAL_RESULT'

        try:
            final_bet_value = int(final["bet"])
            if final_bet_value > max_final_bet_value:
                final["bet"] = max_final_bet_value

            if final_bet_value < 0:
                final["bet"] = max_final_bet_value

        except ValueError:
            response_object['result'] = 'error'
            response_object['info'] = 'FINAL_BET'

        # parsing anc checking group properties
        groups = bet_object["group"]

        for group_id in groups:
            bet = groups[group_id]["bet"]
            order = groups[group_id]["order"]

            # checking and trimming bet value
            try:
                bet_value = int(bet)
                if bet_value > max_group_bet_value:
                    bet_value = max_group_bet_value
                elif bet_value < 0:
                    bet_value = 0

                groups[group_id]["bet"] = bet_value

            except ValueError:
                response_object['result'] = 'error'
                response_object['info'] = "GROUP_BET"
                break

            db_teams = get_db().execute("SELECT name FROM team WHERE group_id = ?", (group_id,)).fetchall()
            if db_teams is None or len(db_teams) == 0:
                response_object['result'] = 'error'
                response_object['info'] = "GROUP_ID"
                break
            else:
                for team in order:
                    team_found = False

                    for db_team in db_teams:
                        if db_team["name"] == team:
                            team_found = True
                            break
                        
                    if team_found is False:
                        response_object['result'] = 'error'
                        response_object['info'] = "GROUP_TEAM"
                        break

        if bool(response_object) is not False:
            return jsonify(response_object)
        else:
            final_bet = final["bet"]
            id = get_db().execute("SELECT id FROM final_bet WHERE username=?", (user_name,)).fetchone()

            if id is None:
                get_db().execute("INSERT INTO final_bet (username, bet, team, result, success) VALUES(?,?,?,?,?)", (user_name, final_bet, final_team, final_result, ""))
            else:
                get_db().execute("UPDATE final_bet SET username = ?, bet = ?, team = ?, result = ? WHERE id = ?", (user_name, final_bet, final_team, final_result, id["id"],))

            for group_id in groups:
                order = groups[group_id]["order"]
                bet = groups[group_id]["bet"]

                id = get_db().execute("SELECT id FROM group_bet WHERE username=? AND group_id=?", (user_name, group_id)).fetchone()

                if id is None:
                    get_db().execute("INSERT INTO group_bet (username, bet, group_ID) VALUES(?, ?, ?)", (user_name, bet, group_id))
                else:
                    get_db().execute("UPDATE group_bet SET username=?, bet=?, group_ID=? WHERE id=?", (user_name, bet, group_id, id["id"]))

                position = 1
                for team in order:
                    id = get_db().execute("SELECT id FROM team_bet WHERE username=? AND team=?", (user_name, team)).fetchone()
                    if id is None:
                        get_db().execute("INSERT INTO team_bet (username, team, position) VALUES(?, ?, ?)", (user_name, team, position))
                    else:
                        get_db().execute("UPDATE team_bet SET username=?, team=?, position=? WHERE id=?", (user_name, team, position, id["id"]))                

                    position += 1

            get_db().commit()
            
            response_object["result"] = "OK"
            return jsonify(response_object)

def during_groupstage():
    user_name = request.args.get("name")

    if user_name is not None:
        amount_after = starting_bet_amount - get_group_and_final_bet_amount(user_name=user_name)
        groups = get_group_object(user_name=user_name)
        final_bet_object = get_final_bet(user_name=user_name)

        return render_template("groupBet/group-during.html", groups=groups, final_bet=final_bet_object, amount_after=amount_after, starting_bet_amount=starting_bet_amount)
    
    players = get_db().execute("SELECT username FROM user WHERE NOT username='RESULT'", ())

    return render_template("groupBet/group-choose.html", username = g.user["username"], admin=g.user["admin"], players=players)

def after_evaluation():
    user_name = request.args.get("name")

    if user_name is not None:
        final_bet_object = get_final_bet(user_name=user_name)
        groups = get_group_object(user_name=user_name)
        total_group_bet = get_group_and_final_bet_amount(user_name=user_name)
        total_win_amount = get_group_win_amount2(groups)

        return render_template("groupBet/group-after.html", group_containers=groups, total_bet=total_group_bet, total_win=total_win_amount, final_bet=final_bet_object)
    
    players = get_db().execute("SELECT username FROM user WHERE NOT username='RESULT'", ())

    return render_template("groupBet/group-choose.html", username = g.user["username"], admin=g.user["admin"], players=players)

@bp.route("/group", methods=("GET", "POST"))
@login_required
def group_order():
    current_time = datetime.now(tz=timezone.utc)
    deadline = datetime.strptime(group_deadline_time, "%Y-%m-%d %H:%M")
    deadline = deadline.replace(tzinfo=tz.gettz('UTC'))
    group_evaluation_time = datetime.strptime(group_evaluation_date, "%Y-%m-%d %H:%M")
    group_evaluation_time = group_evaluation_time.replace(tzinfo=tz.gettz('UTC'))

    if current_time < deadline:
        return before_deadline()
    elif current_time < group_evaluation_time:
        return during_groupstage()
    else:
        return after_evaluation()

@bp.route("/final-odds", methods=("GET",))
@login_required
def final_bet_odds():
    teams = []
    Team = namedtuple("Team", "name, top1, top2, top4, top16")

    for team in get_db().execute("SELECT local_name, top1, top2, top4, top16 FROM team"):
        teams.append(Team(name=team["local_name"], top1=team["top1"], top2=team["top2"], top4=team["top4"], top16=team["top16"]))

    return render_template("groupBet/final-odds.html", teams=teams)