from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
from app.db import get_db
from app.auth import login_required

from datetime import datetime
from dateutil import tz

from app.tools.score_calculator import get_group_and_tournament_bet_amount
from app.tools.score_calculator import match_evaluation_query_string
from app.tools.group_calculator import get_tournament_bet_dict_for_user, get_group_bet_dict_for_user
from app.tools import time_determiner

from app.configuration import configuration

from sqlalchemy import text

bp = Blueprint('previous', __name__, '''url_prefix="/previous"''')

@bp.route('/previous-bets', methods=('GET',))
@login_required
def prev_bets():
    username : str = request.args.get('name')

    # download users's previous bets which will be inserted into the webpage
    if username is not None:
        days : list = []

        match_list_query_string = match_evaluation_query_string.text + \
                            """SELECT match.id, match.goal1 AS rgoal1, match.goal2 AS rgoal2, match_bet.goal1 AS bgoal1, match_bet.goal2 AS bgoal2, match.odd1, match.odd2, match.oddX, match.round, 
                            match_prize.bonus * match_prize.bet AS bonus, match_prize.multiplier * match_prize.bet AS prize, match_prize.bet AS bet, tr1.translation AS team1, tr2.translation AS team2, 
                            (match_prize.bonus * match_prize.bet + match_prize.multiplier * match_prize.bet - match_prize.bet) AS credit_diff, match_prize.success, 
                            date(match.time || :timezone) AS date, strftime('%H:%M', match.time || :timezone) AS time, (strftime('%w', match.time) + 6) % 7 AS weekday 
                            FROM match 
                            LEFT JOIN match_prize ON match_prize.id = match.id 
                            LEFT JOIN match_bet ON match_bet.match_id = match.id AND match_bet.username = :u 
                            LEFT JOIN team_translation AS tr1 ON tr1.name=match.team1 AND tr1.language = :l 
                            LEFT JOIN team_translation AS tr2 ON tr2.name=match.team2 AND tr2.language = :l 
                            WHERE unixepoch(match.time) {r} unixepoch(:group_evaluation_time) AND unixepoch(match.time) < unixepoch(:now) 
                            ORDER BY date, time"""

        match_list_query_parameters = {'now' : time_determiner.get_now_time_string(), 'group_evaluation_time' : configuration.deadline_times.group_evaluation, 'l' : g.user['language'], 'u' : g.user['username'], 'timezone' : g.user['timezone'], 'bullseye' : configuration.bonus_multipliers.bullseye, 'difference' : configuration.bonus_multipliers.difference}

        def add_to_days(match_rows):
            for match_row in match_rows:
                if match_row.date not in days:
                    days[match_row.date] = {'dayID' : len(days) + 1, 'date' : match_row.date, 'weekday' : match_row.weekday, 'matches' : []}

                match_dict = match_row._asdict()
                del match_dict['weekday']
                del match_dict['date']

                if match_row.bet > 0:
                    nonlocal number_of_match_bets
                    nonlocal number_of_successful_bets

                    number_of_match_bets =+ 1
                    number_of_successful_bets += match_row.success

                nonlocal amount_at_end_of_match
                amount_at_end_of_match += match_dict['credit_diff']
                match_dict['balance'] = amount_at_end_of_match

                days[match_row.date]['matches'].append(match_dict)

        start_amount = configuration.bet_values.starting_bet_amount - get_group_and_tournament_bet_amount(username)
        amount_at_end_of_match : int = start_amount
        number_of_match_bets : int = 0
        number_of_successful_bets : int = 0

        days = {}        

        # add the group stage matches
        query_string = text(match_list_query_string.format(r='<'))
        group_matches = get_db().session.execute(query_string, match_list_query_parameters)
        add_to_days(group_matches.fetchall())

        # add the group bet results
        group_bonus : int = sum(group['prize'] for group in get_group_bet_dict_for_user(username=username).values())
        amount_at_end_of_match += group_bonus
        balance_after_group = amount_at_end_of_match

        # add the knockout stage results
        query_string = text(match_list_query_string.format(r='>'))
        knockout_matches = get_db().session.execute(query_string, match_list_query_parameters)
        add_to_days(knockout_matches)

        # add the tournament bet results
        tournament_bet_dict : dict = get_tournament_bet_dict_for_user(username=username)
        amount_at_end_of_match += tournament_bet_dict['prize']

        success_rate = number_of_successful_bets / number_of_match_bets if number_of_match_bets > 0 else 0

        return render_template('/previous-bet/previous-day-match.html', days=days, group_evaluation_date=time_determiner.parse_datetime_string(configuration.deadline_times.group_evaluation).date().strftime('%Y-%m-%d'), start_amount=start_amount, group_bonus=group_bonus, balance_after_group=balance_after_group, tournament_bet=tournament_bet_dict, finishing_balance = amount_at_end_of_match, success_rate=success_rate)

    # if no user name provided send down the username list and render the base page
    query_string = text('SELECT username FROM bet_user ORDER BY username ASC')
    result = get_db().session.execute(query_string)
    players = result.fetchall()

    return render_template('/previous-bet/previous-bets.html', players=players)