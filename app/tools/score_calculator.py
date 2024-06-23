from app.tools.db_handler import get_db
from flask import g
from flask import current_app

from app.tools import time_handler
from app.tools import group_calculator

from sqlalchemy import text

# this method returns the sum of group bets and the tournament bet of a user
def get_group_and_tournament_bet_amount(username : str) -> int:    
    query_string = text("SELECT COALESCE(SUM(group_bet.bet), 0) + COALESCE(tournament_bet.bet, 0) AS total_bet "
                        "FROM bet_user "
                        "LEFT JOIN group_bet ON group_bet.username = bet_user.username "
                        "LEFT JOIN tournament_bet ON tournament_bet.username = bet_user.username "
                        "WHERE bet_user.username = :username "
                        "GROUP BY group_bet.username"
                        )

    result = get_db().session.execute(query_string, {'username' : username})

    return result.fetchone()._asdict()['total_bet']

match_evaluation_query_string = text(
                            "WITH match_prize AS("
                                "SELECT match.id, match.outcome AS match_outcome, match_bet.outcome AS bet_outcome, (match.outcome = match_bet.outcome) AS success, "
                                "match_bet.goal1, match_bet.goal2, match_bet.username AS username, "
                                    "CASE match.outcome = match_bet.outcome "
                                        "WHEN 1 THEN CASE match.outcome "
                                            "WHEN 1 THEN match.odd1 "
                                            "WHEN 0 THEN match.oddX "
                                            "WHEN -1 THEN match.odd2 "
                                            "ELSE 0 END "
                                        "ELSE 0 "
                                    "END AS multiplier, "
                                    "CASE match.outcome = match_bet.outcome "
                                        "WHEN 1 THEN CASE WHEN match.goal1 = match_bet.goal1 AND match.goal2 = match_bet.goal2 "
                                            "THEN :bullseye "
                                            "ELSE CASE WHEN (match.goal1 - match.goal2) = (match_bet.goal1 - match_bet.goal2) AND (match.outcome != 0) "
                                                "THEN :difference "
                                                "ELSE 0 "
                                                "END "
                                            "END "
                                        "ELSE 0 "
                                    "END AS bonus, "
                                    "COALESCE(match_bet.bet, 0) AS bet "
                                "FROM (SELECT match.*, SIGN(match.goal1 - match.goal2) AS outcome FROM match) AS match "
                                "LEFT JOIN (SELECT match_bet.*, SIGN(match_bet.goal1 - match_bet.goal2) AS outcome FROM match_bet) AS match_bet ON match_bet.match_id = match.id "
                            ")")

def get_daily_points_by_current_time(username : str):
    simple_entry_query = '''SELECT strftime('%Y', date.datetime) AS year, strftime('%m', date.datetime) -1 AS month, strftime('%d', date.datetime) AS day, 
                    date.datetime, {diff} AS diff 
                    FROM (SELECT DATE('{st}', '{days}' || ' days') AS datetime) AS date 
                    UNION ALL '''

    match_query = """SELECT * FROM 
                        (SELECT strftime('%Y', match.datetime) AS year, strftime('%m', match.datetime) -1 AS month, strftime('%d', match.datetime) AS day, MAX(match.datetime) AS datetime,
                            SUM(COALESCE(match_prize.bonus * match_prize.bet + match_prize.multiplier * match_prize.bet - match_prize.bet, -match_prize.bet, 0)) AS diff
                        FROM match
                        RIGHT JOIN bet_user
                        LEFT JOIN match_prize ON match_prize.id = match.id AND match_prize.username = bet_user.username
                        WHERE unixepoch(datetime) < unixepoch(:now) AND unixepoch(datetime) {r} unixepoch(:group_evaluation_time) AND bet_user.username = :u
                        GROUP BY date(match.datetime)
                        ORDER BY datetime)
                    UNION ALL """

    deadline_times = current_app.config['DEADLINE_TIMES']

    # add match_evaluation CTE
    complete_query = match_evaluation_query_string.text
    # add starting credit
    complete_query += simple_entry_query.format(st=deadline_times['register'], days=-2, diff=0)
    # subtract group + tournament bet credits
    complete_query += simple_entry_query.format(st=deadline_times['register'], days=-1, diff=-get_group_and_tournament_bet_amount(username))
    # calculate group stage results
    complete_query += match_query.format(r='<')
    # add group stage bonus
    complete_query += simple_entry_query.format(st=deadline_times['group_evaluation'], days=1, diff= sum(group['prize'] for group in group_calculator.get_group_bet_dict_for_user(username=username).values()))
    # calculate knock-out stage results
    complete_query += match_query.format(r='>')
    # add tournament bonus
    complete_query += simple_entry_query.format(st=deadline_times['tournament_end'], days=1, diff=group_calculator.get_tournament_bet_dict_for_user(username=username, language=g.user['language'])['prize'])
    # add empty SELECT after UNION ALL
    complete_query += 'SELECT 1, 2, 3, 4, 5 WHERE 0 = 1'
    
    hitmap = current_app.config['BONUS_MULTIPLIERS']
    daily_point_parameters = {
        'now' : time_handler.get_now_time_object().strftime('%Y-%m-%d %H:%M'),
        'group_evaluation_time' : deadline_times['group_evaluation'],
        'starting_point' : current_app.config['BET_VALUES']['starting_bet_amount'],
        'u' : username,
        'bullseye' : hitmap['bullseye'], 'difference' : hitmap['difference']
    }

    complete_query =  '''
    SELECT date(days.datetime) AS date, days.year, days.month, days.day,
        COALESCE(:starting_point + SUM(diff) OVER (ROWS BETWEEN UNBOUNDED PRECEDING AND 0 PRECEDING), :starting_point) AS point
    FROM (''' + complete_query + ''') AS days
    WHERE unixepoch(datetime) < unixepoch(:now)'''

    day_result = get_db().session.execute(text(complete_query), daily_point_parameters)

    return [day._asdict() for day in day_result.fetchall()]
