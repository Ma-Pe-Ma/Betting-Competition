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
from app.db import get_db

from datetime import timezone, datetime
from collections import namedtuple

from app.score_calculator import *

bp = Blueprint("group", __name__, '''url_prefix="/group"''')

deadline = datetime(2022, 7, 25, 7, 56, tzinfo=timezone.utc)
group_evaulation_time = datetime(2022, 7, 25, 7, 56, tzinfo=timezone.utc)

Team = namedtuple("Team", "name, hun_name, position, top1, top2, top4, top16")
Group = namedtuple("Group", "ID, teams, bet")
FinalBet = namedtuple("FinalBet", "team, hun_name, result, multiplier, betting_amount, winning_amount, success")

def sort_groups(group):
    return group.ID

def sort_teams(team):
    return team.position

def sort_group_results(group_result):
    return group_result["position"]

def get_ordered_groups(user_name, user_bets):
    groups = []

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

    return groups

def get_final_bet(user_name):
    final_bet = get_db().execute("SELECT team, bet, result, success FROM final_bet WHERE username = ?", (user_name,)).fetchone()
    final_team = get_db().execute("SELECT hun_name, top1, top2, top4, top16 FROM team WHERE name=?", (final_bet["team"],)).fetchone()
    final_multiplier = 0

    if final_bet["result"] == 0:
        final_multiplier = final_team["top1"]
    elif final_bet["result"] == 1:
        final_multiplier = final_team["top2"]
    elif final_bet["result"] == 2:
        final_multiplier = final_team["top4"]
    elif final_bet["result"] == 3:
        final_multiplier = final_team["top16"]

    print("multiplier: " + str(final_multiplier))

    winning_amount = final_bet["bet"] * final_multiplier

    return FinalBet(team=final_bet["team"], hun_name=final_team["hun_name"], result=final_bet["result"], multiplier=final_multiplier, betting_amount=final_bet["bet"], winning_amount=winning_amount, success=final_bet["success"] )

def before_deadline():
    user_name = g.user["username"]

    if request.method == "GET":
        groups = []
        teams = []

        user_bets = get_db().execute("SELECT team, position FROM team_bet WHERE username =?", (user_name,)).fetchall()

        if len(user_bets) == 0:
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
            groups = get_ordered_groups(user_name, user_bets)

        groups.sort(key=sort_groups)

        for group in groups:
            group.teams.sort(key=sort_teams)

        final_bet_object = get_final_bet(user_name)
        print("final get: " + str(final_bet_object.betting_amount))

        return render_template("groupBet/group-edit.html", username = user_name, admin=g.user["admin"], start_amount=starting_bet_amount, final_bet = final_bet_object, groups = groups)

    elif request.method == "POST":
        print("group form: " + str(request.get_json()))

        group_bet = request.get_json()

        error = None

        #if get_db().execute("SELECT name FROM user WHERE name=?", (user_name)) is None:
            #error = ""    

        final = group_bet["final"]
        groups = group_bet["group"]

        final_team = final["team"]
        if get_db().execute("SELECT name FROM team WHERE name = ?", (final_team,)).fetchone() is None:
            error = "FINAL_TEAM"     

        try:
            final_result = int(final["result"])
            if final_result < 0 or final_result> 3 :
                error = "FINAL_RESULT"

            final_bet = int(final["bet"])
            print("posted final bet: " + str(int(final_bet)))
        except ValueError:
            error = "FINAL_RESULT"            

        for group_id in groups:
            bet = groups[group_id]["bet"]
            order = groups[group_id]["order"]

            #checking and trimming bet value
            try:
                bet_value = int(bet)
                if bet_value > max_group_bet_value:
                    bet_value = max_group_bet_value
                elif bet_value < 0:
                    bet_value = 0

            except ValueError:
                error = "BET"
                break

            db_teams = get_db().execute("SELECT name FROM team WHERE group_id = ?", (group_id,)).fetchall()
            if len(db_teams) == 0:
                error = "GROUP_ID"
                break
            else:
                for team in order:
                    team_found = False

                    for db_team in db_teams:
                        if db_team["name"] == team:
                            team_found = True
                            break
                        
                    if team_found is False:
                        error = "TEAM"
                        break

        if error is not None:
            print("error happened: " + error)
            return ""
        else:
            id = get_db().execute("SELECT id FROM final_bet WHERE username=?", (user_name,)).fetchone()

            if id is None:
                print("inserting into")
                get_db().execute("INSERT INTO final_bet (username, bet, team, result) VALUES(?,?,?,?)", (user_name, final_bet, final_team, final_result))
            else:
                print("updating - username: " + user_name + ", bet: " + str(final_bet) + ", team: " + final_team + ", result: " + str(final_result) + ", id: " + str(id["id"]))
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
                    print("new pos: " + team +", " + str(position))

                    id = get_db().execute("SELECT id FROM team_bet WHERE username=? AND team=?", (user_name, team)).fetchone()
                    if id is None:
                        get_db().execute("INSERT INTO team_bet (username, team, position) VALUES(?, ?, ?)", (user_name, team, position))
                    else:
                        get_db().execute("UPDATE team_bet SET username=?, team=?, position=? WHERE id=?", (user_name, team, position, id["id"]))                

                    position += 1

            get_db().commit()
            print("EVERYTHING IS OK!")
            return "OK"

def during_groupstage():
    user_name = request.args.get("name")

    if user_name is not None:
        user_bets = get_db().execute("SELECT team, position FROM team_bet WHERE username =?", (user_name,)).fetchall()

        if len(user_bets) == 0:
            print("NONE?")
            return render_template("groupBet/group-during.html", groups = None, starting_bet_amount=starting_bet_amount)
        else:
            final_bet_object = get_final_bet(user_name)

            groups = get_ordered_groups(user_name, user_bets)

            groups.sort(key=sort_groups)

            amount_after = starting_bet_amount
            amount_after -= final_bet_object.betting_amount

            for group in groups:
                amount_after -= group.bet
                group.teams.sort(key=sort_teams)

            return render_template("groupBet/group-during.html", groups=groups, final_bet = final_bet_object , amount_after=amount_after, starting_bet_amount=starting_bet_amount)
    
    players = get_db().execute("SELECT username FROM user WHERE NOT username='RESULT'", ())

    return render_template("groupBet/group-choose.html", username = g.user["username"], admin=g.user["admin"], players=players)

def after_evaulation():
    user_name = request.args.get("name")

    if user_name is not None:
        user_bets = get_db().execute("SELECT team, position FROM team_bet WHERE username =?", (user_name,)).fetchall()

        if len(user_bets) == 0:
            return render_template("groupBet/group-during.html", groups = None, starting_bet_amount=starting_bet_amount)
        else:
            GroupContainer = namedtuple("GroupContainer", "result, bet")
            GroupResult = namedtuple("GroupResult", "multiplier, win_amount, hit_number, teams")
            TeamResult = namedtuple("TeamResult", "name, background")
            
            group_containers = []

            groups = get_ordered_groups(user_name, user_bets)
            groups.sort(key=sort_groups)

            final_bet_object = get_final_bet(user_name)

            total_group_bet = 0
            total_win_amount = 0

            for group in groups:
                group.teams.sort(key=sort_teams)

                team_result_prefabs = get_db().execute("SELECT name, position, hun_name FROM team WHERE group_ID = ?", (group.ID,)).fetchall()
                
                for team_result_prefab in team_result_prefabs:
                    if team_result_prefab["position"] is None:
                        return render_template("groupBet/group-after.html", group_containers=None)

                team_result_prefabs.sort(key=sort_group_results)

                team_results = []

                i=0
                hit_number = 0
                for team_result_prefab in team_result_prefabs:
                    correct_position = False
                    if team_result_prefab["name"] == group.teams[i].name:
                        hit_number += 1
                        correct_position = True

                    background = "red"    
                    if correct_position:
                        background = "green"

                    team_results.append(TeamResult(name=team_result_prefab["hun_name"], background=background))
                    i += 1

                multiplier = hit_map[hit_number]
                win_amount = group.bet * multiplier
                result = GroupResult(teams=team_results, hit_number=hit_number, multiplier=multiplier, win_amount=win_amount)

                total_group_bet += group.bet
                total_win_amount += win_amount

                group_containers.append(GroupContainer(result=result, bet=group))                

            return render_template("groupBet/group-after.html", group_containers=group_containers, total_bet=total_group_bet, total_win=total_win_amount, final_bet=final_bet_object)
    
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