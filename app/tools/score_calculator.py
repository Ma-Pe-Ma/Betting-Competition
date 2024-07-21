from app.tools.db_handler import get_db
from flask import g
from flask import current_app

from app.tools import time_handler

from sqlalchemy import text

daily_point_parameters = {}

def init_calculator(app):
    global daily_point_parameters
    daily_point_parameters = app.config['DEADLINE_TIMES'].copy()
    daily_point_parameters.update(app.config['GROUP_BET_HIT_MAP'])
    daily_point_parameters.update(app.config['BONUS_MULTIPLIERS'])
    daily_point_parameters.update(app.config['BET_VALUES'])
    daily_point_parameters.update({'starting_bet_amount' : app.config['BET_VALUES']['starting_bet_amount']})
    daily_point_parameters.update({'s' : app.config['IDENT_URL']})

def get_daily_point_parameters():
    return daily_point_parameters.copy()

group_and_tournament_bet_query_string = '''SELECT COALESCE(SUM(group_bet.bet), 0) + COALESCE(tournament_bet.bet, 0) AS total_bet, bet_user.username
                                        FROM bet_user 
                                        LEFT JOIN group_bet ON group_bet.username = bet_user.username 
                                        LEFT JOIN tournament_bet ON tournament_bet.username = bet_user.username 
                                        {filter}
                                        GROUP BY group_bet.username'''

match_evaluation_query_string = '''SELECT match.id, match.outcome AS match_outcome, match_bet.outcome AS bet_outcome, (match.outcome = match_bet.outcome) AS success, 
                                match_bet.goal1, match_bet.goal2, bet_user.username AS username, match.datetime, match.max_bet, match.team1, match.team2,
                                    CASE match.outcome = match_bet.outcome 
                                        WHEN 1 THEN CASE match.outcome 
                                            WHEN 1 THEN match.odd1 
                                            WHEN 0 THEN match.oddX 
                                            WHEN -1 THEN match.odd2 
                                            ELSE 0 END 
                                        ELSE 0 
                                    END AS multiplier, 
                                    CASE match.outcome = match_bet.outcome 
                                        WHEN 1 THEN CASE WHEN match.goal1 = match_bet.goal1 AND match.goal2 = match_bet.goal2 
                                            THEN :bullseye 
                                            ELSE CASE WHEN (match.goal1 - match.goal2) = (match_bet.goal1 - match_bet.goal2) AND (match.outcome != 0) 
                                                THEN :difference 
                                                ELSE 0 
                                                END 
                                            END 
                                        ELSE 0 
                                    END AS bonus, 
                                    COALESCE(match_bet.bet, 0) AS bet 
                                FROM (SELECT match.*, SIGN(match.goal1 - match.goal2) AS outcome FROM match) AS match 
                                LEFT JOIN bet_user
                                LEFT JOIN (SELECT match_bet.*, SIGN(match_bet.goal1 - match_bet.goal2) AS outcome FROM match_bet) AS match_bet ON match_bet.match_id = match.id AND match_bet.username = bet_user.username'''

tournament_dict = '''SELECT t_bet.*, 
                            CASE t_bet.success WHEN 1 THEN COALESCE(t_bet.bet, 0) * (t_bet.multiplier) ELSE 0 END AS prize, 
                            COALESCE(t_bet.bet, 0) * (t_bet.multiplier) AS expected_prize 
                        FROM bet_user 
                        LEFT JOIN (
                            SELECT tournament_bet.*, COALESCE(tournament_bet.bet, 0) AS bet, tr.translation AS local_name, 
                                CASE tournament_bet.result WHEN 0 THEN team.top1 WHEN 1 THEN team.top2 WHEN 2 THEN team.top4 WHEN 3 THEN team.top8 ELSE 0 END AS multiplier 
                            FROM tournament_bet 
                            LEFT JOIN team ON team.name = tournament_bet.team 
                            LEFT JOIN team_translation AS tr ON tr.name = tournament_bet.team AND tr.language = :l 
                        ) AS t_bet ON t_bet.username = bet_user.username
                        {filter}
                    '''

group_dict = '''SELECT ts2.*, COALESCE(ts2.multiplier * ts2.bet, 0) AS prize, (ts2.multiplier - 1) * ts2.bet AS credit_diff 
            FROM (
                SELECT ts1.*, CASE ts1.hit_number WHEN 1 THEN :h1 WHEN 2 THEN :h2 WHEN 4 THEN :h4 ELSE 0 END AS multiplier 
                FROM (SELECT team.*, (team.name = tb.team) AS hit, tr1.translation AS local_name, COALESCE(group_bet.bet, 0) AS bet, 
                    COALESCE(tb.team, team.name) AS bname, COALESCE(tr2.translation, tr1.translation) AS blocal_name, 
                    SUM(team.name = tb.team) OVER (PARTITION BY team.group_id, tb.username) AS hit_number, tb.username
                    FROM team 
                    LEFT JOIN ( 
                        SELECT team_bet.position, team.group_id, team_bet.team, bet_user.username
                        FROM team_bet 
                        LEFT JOIN team ON team_bet.team = team.name
                        LEFT JOIN bet_user ON bet_user.username = team_bet.username
                        {filter}
                    ) AS tb ON tb.position = team.position AND tb.group_id = team.group_id 
                    LEFT JOIN group_bet ON group_bet.group_id = team.group_id AND group_bet.username = tb.username
                    LEFT JOIN team_translation AS tr1 ON tr1.name = team.name AND tr1.language = :l
                    LEFT JOIN team_translation AS tr2 ON tr2.name = tb.team AND tr2.language = :l
                    ORDER BY team.group_id, team.position 
                ) AS ts1 
            ) AS ts2'''

def get_daily_points_by_current_time_query(users : str) -> str:
    simple_entry_query = '''SELECT date_values.*
                    FROM (SELECT strftime('%Y', date.datetime) AS year, strftime('%m', date.datetime) -1 AS month, strftime('%d', date.datetime) AS day, date.datetime, date(date.datetime) AS date, NULL AS id
                            FROM (SELECT DATE('{st}', '{days}' || ' days') AS datetime) AS date
                            {filter}) AS date_values
                    UNION ALL '''

    match_query = '''SELECT * FROM 
                        (SELECT strftime('%Y', match.datetime) AS year, strftime('%m', match.datetime) -1 AS month, strftime('%d', match.datetime) AS day, match.datetime AS datetime, date(match.datetime) AS date, match.id AS id
                        FROM match
                        WHERE unixepoch(datetime) < unixepoch(:now) AND unixepoch(datetime) {r} unixepoch(:group_evaluation)
                        ORDER BY datetime)
                    UNION ALL '''

    deadline_times = current_app.config['DEADLINE_TIMES']

    # add starting credit
    complete_query = simple_entry_query.format(st=deadline_times['register'], days=-2, filter='')
    # subtract group + tournament bet credits
    complete_query += simple_entry_query.format(st=deadline_times['register'], days=-1, filter='')
    # calculate group stage results
    complete_query += match_query.format(r='<')
    # # add group stage bonus
    complete_query += simple_entry_query.format(st=deadline_times['group_evaluation'], days=1, filter='WHERE unixepoch(date.datetime) < unixepoch(:now)')
    # # calculate knock-out stage results
    complete_query += match_query.format(r='>')
    # # add tournament bonus
    complete_query += simple_entry_query.format(st=deadline_times['tournament_end'], days=1, filter='WHERE unixepoch(date.datetime) < unixepoch(:now)')
    # add empty SELECT after UNION ALL
    complete_query += 'SELECT 1, 2, 3, 4, 5, 6 WHERE 0 = 1'

    complete_query = '''WITH
        match_prize AS (''' + match_evaluation_query_string + '''),
        gt_bet_amount AS (''' + group_and_tournament_bet_query_string.format(filter='') +'''),
        group_dict AS (''' + group_dict.format(filter='') + '''),
        tournament_dict AS (''' + tournament_dict.format(filter='') + ''')

    SELECT point_entries.*, bet_user.username, 
        CASE point_entries.date
            WHEN date(:register, '-2 days') THEN :starting_bet_amount
            WHEN date(:register, '-1 days') THEN -gt_bet_amount.total_bet
            WHEN date(:group_evaluation, '1 days') THEN group_bonus.prize
            WHEN date(:tournament_end, '1 days') THEN tournament_bonus.prize
            ELSE SUM(COALESCE(match_prize.bonus * match_prize.bet + match_prize.multiplier * match_prize.bet - match_prize.bet, -match_prize.bet, 0))
        END AS diff
    FROM (''' + complete_query + ''') AS point_entries
    LEFT JOIN bet_user ON bet_user.username IN({users})
    LEFT JOIN match_prize ON match_prize.username = bet_user.username AND point_entries.id = match_prize.id
    LEFT JOIN gt_bet_amount ON bet_user.username = gt_bet_amount.username
    LEFT JOIN (SELECT username, SUM(prize) AS prize FROM (SELECT * FROM group_dict GROUP BY username, group_id) GROUP BY username) AS group_bonus ON group_bonus.username = bet_user.username
    LEFT JOIN tournament_dict AS tournament_bonus ON tournament_bonus.username = bet_user.username
    GROUP BY bet_user.username, point_entries.date'''.format(users=users)
    
    # calculate the player's points at the end of the days
    complete_query = '''
    SELECT days.username, date(days.datetime) AS date, days.year, days.month, days.day,
        diff + COALESCE(SUM(diff) OVER (PARTITION BY username ORDER BY username ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0) AS point,
        diff AS diff,
        COALESCE(SUM(diff) OVER (PARTITION BY username ORDER BY username ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0) as penultimate
    FROM (''' + complete_query + ''') AS days '''
    return complete_query

# this method returns the sum of group bets and the tournament bet of a user
def get_group_and_tournament_bet_amount(username : str) -> int:
    query_string  = group_and_tournament_bet_query_string.format(filter='WHERE group_bet.username = :u')
    query_string = " SELECT * FROM ({q})".format(q=query_string)
    result = get_db().session.execute(text(query_string), {'u' : username})

    return result.fetchone()._asdict()['total_bet']

# get's user's tournament bet, or create default if it does not exist
def get_tournament_bet_dict_for_user(username : str, language = None) -> dict:
    query_string = text(tournament_dict.format(filter="WHERE bet_user.username = :u"))
    return get_db().session.execute(query_string, {'u' : username, 'l' : language or g.user['language']}).fetchone()._asdict()

# get group object which contains both the results and both the user bets (used in every 3 contexts)
def get_group_bet_dict_for_user(username : str, language = None):
    query_string = text(group_dict.format(filter="WHERE team_bet.username = :u"))

    hit_map = current_app.config['GROUP_BET_HIT_MAP']

    result = get_db().session.execute(query_string, {'u' : username, 'l' : language or g.user['language'], 'h1' : hit_map['h1'], 'h2' : hit_map['h2'], 'h4' : hit_map['h4']})
    team_rows = result.fetchall()

    groups = {}
    for team_row in team_rows:
        if team_row.group_id not in groups:
            groups[team_row.group_id] = {'hit_number' : team_row.hit_number, 'bet' : team_row.bet, 'prize' : team_row.prize, 'credit_diff' : team_row.credit_diff, 'teams' : [], 'multiplier' : team_row.multiplier}
        
        team_dict = team_row._asdict()
        del team_dict['hit_number']
        del team_dict['bet']
        del team_dict['prize']
        del team_dict['multiplier']

        groups[team_row.group_id]['teams'].append(team_dict)

    return groups
