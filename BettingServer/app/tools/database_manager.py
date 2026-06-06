from flask import current_app

from datetime import datetime
import urllib.request
import csv

from sqlalchemy import text

from app.tools.db_handler import get_db

def initialize_teams(team_file_name, translation_file_name):
    try:
        with current_app.open_resource(team_file_name, 'rb') as team_file: 
            data_reader = csv.reader(team_file.read().decode('utf-8').splitlines(), delimiter='|')

            fields = next(data_reader)
            for i, row in enumerate(data_reader):
                position = i % 4 + 1
                query_string = text('INSERT INTO team (name, group_id, position, top1, top2, top4, top8, top16) VALUES (:n, :g, :p, :t1, :t2, :t4, :t8, :t16)')
                get_db().session.execute(query_string, {'n' : row[0], 'g' : row[1], 'p' : position, 't1' : row[2], 't2' : row[3], 't4' : row[4], 't8' : row[5], 't16' : row[6]})

            get_db().session.commit()

        with current_app.open_resource(translation_file_name, 'rb') as translation_file:
            data_reader = csv.reader(translation_file.read().decode('utf-8').splitlines(), delimiter='|')

            fields = next(data_reader)

            for i, row in enumerate(data_reader):
                for j, column in enumerate(row):
                    if j == 0:
                        continue

                    query_string = text('INSERT INTO team_translation (name, language, translation) VALUES (:n, :l, :t)')
                    get_db().session.execute(query_string, {'n' : row[0], 'l' : fields[j], 't' : column})

            get_db().session.commit()
    except Exception as error:
        current_app.logger.info('Error while initializing teams: ' + str(error))
        return False

    return True

def initialize_matches():
    try:
        bet_values = current_app.config['BET_VALUES']
        
        url = current_app.config['MATCH_URL']
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        response = urllib.request.urlopen(req)
        data = response.read()
        decoded_text = data.decode("utf-8")

        data_reader = csv.reader(decoded_text.splitlines(), delimiter=',')
        fields = next(data_reader)

        for row in data_reader:        
            time_object = datetime.strptime(row[2], "%d/%m/%Y %H:%M")
            time_string = time_object.strftime("%Y-%m-%d %H:%M")
            query_string = text('INSERT INTO match (id, team1, team2, datetime, round, max_bet) VALUES (:id, :t1, :t2, :t, :r, :m)')
            get_db().session.execute(query_string, {'id' : row[0], 't1' : row[4], 't2' : row[5], 't' : time_string, 'r' : row[1], 'm' : bet_values['default_max_bet_per_match']})

        get_db().session.commit()
    except Exception as error:
        get_db().session.rollback()
        current_app.logger.info('Error while initializing matches: ' + str(error))
        return False

    return True

def update_match_data_from_fixture():
    try:
        url = current_app.config['MATCH_URL']
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        response = urllib.request.urlopen(req)
        data = response.read()
        file_text = data.decode("utf-8")

        data_reader = csv.reader(file_text.splitlines(), delimiter=',')
        fields = next(data_reader)

        for row in data_reader:
            goal1 = None
            goal2 = None

            goals = row[7]
            if goals is not None and goals != '':
                goals = goals.replace(" ", "")                
                goals = goals.split("-")

                try:
                    goal1 = int(goals[0])
                    goal2 = int(goals[1])
                except (IndexError, ValueError):
                    current_app.logger.warning(f"Skipping row due to invalid score format: {row[7]}")
                    continue

            try:
                with get_db().session.begin_nested():
                    query_string = text('UPDATE match SET team1=:t1, team2=:t2, goal1=:g1, goal2=:g2 WHERE id=:id AND goal1 IS NULL AND goal2 IS NULL')
                    get_db().session.execute(query_string, {'t1' : row[4], 't2' : row[5], 'g1' : goal1, 'g2' : goal2, 'id' : row[0]})
            except Exception as row_error:
                current_app.logger.error(f"Row match ID {row[0]} failed constraint/DB validation: {row_error}")

        get_db().session.commit()
        current_app.logger.info('Match db successfully updated from remote CSV!')
    except Exception as error:
        get_db().session.rollback()
        current_app.logger.info('Error updating match database: ' + str(error))
        return False

    return True
