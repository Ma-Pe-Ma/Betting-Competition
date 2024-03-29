from app.tools.db_handler import get_db
from flask import g
from flask import current_app

from datetime import datetime, timedelta

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
                                "SELECT match.id, m_outcome.outcome AS match_outcome, b_outcome.outcome AS bet_outcome, COALESCE(m_outcome.outcome = b_outcome.outcome, 0) AS success, "
                                    "CASE m_outcome.outcome = b_outcome.outcome WHEN 1 "
                                        "THEN CASE m_outcome.outcome WHEN 1 "
                                            "THEN match.odd1 WHEN -1 THEN match.odd2 WHEN 0 THEN match.oddX ELSE 0 END "
                                        "ELSE 0 "
                                    "END AS multiplier, "
                                    "CASE m_outcome.outcome = b_outcome.outcome WHEN 1 "
                                        "THEN CASE WHEN match.goal1 = match_bet.goal1 AND match.goal2 = match_bet.goal2 "
                                            "THEN :bullseye "
                                            "ELSE CASE WHEN (match.goal1 - match.goal2) = (match_bet.goal1 - match_bet.goal2) "
                                                "THEN :difference "
                                                "ELSE 0 "
                                                "END "
                                            "END "
                                        "ELSE 0 "
                                    "END AS bonus, "
                                    "COALESCE(match_bet.bet, 0) AS bet "
                                "FROM match "
                                "LEFT JOIN match_bet ON match_bet.match_id = match.id AND match_bet.username = :u "
                                "LEFT JOIN (SELECT SIGN(match.goal1 - match.goal2) AS outcome, match.id AS id FROM match) AS m_outcome ON m_outcome.id = match.id "
                                "LEFT JOIN (SELECT SIGN(match_bet.goal1 - match_bet.goal2) AS outcome, match_bet.match_id AS match_id FROM match_bet WHERE match_bet.username = :u) AS b_outcome ON b_outcome.match_id = match.id "
                            ")")

def get_daily_points_by_current_time(username : str):
    utc_now = time_handler.get_now_time_object()
    deadline_times = current_app.config['DEADLINE_TIMES']

    daily_point_query_string = match_evaluation_query_string.text + \
                        """SELECT SUM(COALESCE(match_prize.bonus * match_prize.bet + match_prize.multiplier * match_prize.bet - match_prize.bet, -match_prize.bet)) AS point, date(match.datetime) AS date, 
                            strftime('%Y', match.datetime) as year, strftime('%m', match.datetime) -1 as month, strftime('%d', match.datetime) as day 
                        FROM match 
                        LEFT JOIN match_prize ON match_prize.id = match.id 
                        WHERE unixepoch(datetime) < unixepoch(:now) AND unixepoch(datetime) {r} unixepoch(:group_evaluation_time)
                        GROUP BY date 
                        ORDER BY date """

    daily_point_parameters = {'now' : utc_now.strftime('%Y-%m-%d %H:%M'), 'group_evaluation_time' : deadline_times['group_evaluation'], 'u' : username, 'bullseye' : current_app.config['BONUS_MULTIPLIERS']['bullseye'], 'difference' : current_app.config['BONUS_MULTIPLIERS']['difference']}

    #create unique time objects
    group_deadline_time_object : datetime = time_handler.parse_datetime_string(deadline_times['register'])
    two_days_before_deadline = group_deadline_time_object - timedelta(days=2)
    one_day_before_deadline = group_deadline_time_object - timedelta(days=1)
    
    days = []

    # two days before starting show start amount, same for everyone
    amount = current_app.config['BET_VALUES']['starting_bet_amount']
    days.append({'year' : two_days_before_deadline.year, 'month' : two_days_before_deadline.month - 1, 'day' : two_days_before_deadline.day, 'point' : amount})

    # one day before starting show startin minus group+tournament betting amount
    amount -=  get_group_and_tournament_bet_amount(username)
    days.append({'year' : one_day_before_deadline.year, 'month' : one_day_before_deadline.month - 1, 'day' : one_day_before_deadline.day, 'point' : amount})

    # add the days of the group stage section
    group_query_string = text(daily_point_query_string.format(r='<'))
    result = get_db().session.execute(group_query_string, daily_point_parameters)

    for day_parameters in result.fetchall():
        day_dict = day_parameters._asdict()
        amount += day_dict['point']
        day_dict['point'] = amount
        days.append(day_dict)

    # add the group stage bonus
    group_evaluation_time_object : datetime = time_handler.parse_datetime_string(deadline_times['group_evaluation'])
    if utc_now > group_evaluation_time_object:
        group_evaluation_time_object += timedelta(days=1)
        amount += sum(group['prize'] for group in group_calculator.get_group_bet_dict_for_user(username=username).values())
        days.append({'year' : group_evaluation_time_object.year, 'month' : group_evaluation_time_object.month - 1, 'day' : group_evaluation_time_object.day, 'point' : amount})

    # add the days of the knockout stage section
    knockout_query_string = text(daily_point_query_string.format(r='>'))
    result = get_db().session.execute(knockout_query_string, daily_point_parameters)

    for day_parameters in result.fetchall():
        day_dict = day_parameters._asdict()
        amount += day_dict['point']
        day_dict['point'] = amount
        days.append(day_dict)

    tournament_end_time_object : datetime = time_handler.parse_datetime_string(deadline_times['tournament_end'])
    
    if utc_now > tournament_end_time_object:
        tournament_end_time_object += timedelta(days=1)
        tournament_bet_dict = group_calculator.get_tournament_bet_dict_for_user(username=username, language=g.user['language'])
        amount += tournament_bet_dict['prize']
        days.append({'year' : tournament_end_time_object.year, 'month' : tournament_end_time_object.month - 1, 'day' : tournament_end_time_object.day, 'point' : amount})

    return days