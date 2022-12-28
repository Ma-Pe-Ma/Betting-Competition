from flask import current_app

from datetime import datetime
import urllib.request
import csv

from app.db import get_db
from app.configuration import default_max_bet_per_match, match_url

url = match_url

def initialize_teams(team_file_name, translation_file_name):
    with current_app.open_resource(team_file_name, 'rb') as team_file: 
        data_reader = csv.reader(team_file.read().decode('utf-8').splitlines(), delimiter='|')

        fields = next(data_reader)
        for i, row in enumerate(data_reader):
            position = i % 4 + 1
            get_db().cursor().execute('INSERT INTO team (name, group_id, position, top1, top2, top4, top16) VALUES (%s, %s, %s, %s, %s, %s, %s)',(row[0], row[1], position, row[2], row[3], row[4], row[5]))

        get_db().commit()
    
    with current_app.open_resource(translation_file_name, 'rb') as translation_file:
        data_reader = csv.reader(translation_file.read().decode('utf-8').splitlines(), delimiter='|')

        fields = next(data_reader)

        for field in fields:
            print('field: ' + field)

        for i, row in enumerate(data_reader):
            for j, column in enumerate(row):
                if j == 0:
                    continue                

                get_db().cursor().execute('INSERT INTO team_translation (name, language, translation) VALUES (%s, %s, %s)',(row[0], fields[j], column))

        get_db().commit()

def initialize_matches():
    try:
        response = urllib.request.urlopen(url)
        data = response.read()
        text = data.decode("utf-8")

        data_reader = csv.reader(text.splitlines(), delimiter=',')
        fields = next(data_reader)

        for row in data_reader:        
            time_object = datetime.strptime(row[2], "%d/%m/%Y %H:%M")
            time_string = time_object.strftime("%Y-%m-%d %H:%M")
            get_db().cursor().execute("INSERT INTO match (id, team1, team2, time, round, max_bet) VALUES (%s, %s, %s, %s, %s, %s)", (row[0], row[4], row[5], time_string, row[1], default_max_bet_per_match))
    except:
        print("Error initializing matches.")

    get_db().commit()

def download_data_csv():
    try:
        response = urllib.request.urlopen(url)
        data = response.read()
        text = data.decode("utf-8")

        data_reader = csv.reader(text.splitlines(), delimiter=',')
        fields = next(data_reader)

        for row in data_reader:
            goal1 = None
            goal2 = None

            goals = row[7]
            if goals is not None and goals != '':
                goals = goals.replace(" ", "")
                
                goals.split("-")

                goal1 = goals[0]
                goal2 = goals[2]

            get_db().cursor().execute("UPDATE match SET team1=%s, team2=%s, goal1=%s, goal2=%s WHERE id=%s", (row[4], row[5], goal1, goal2, row[0]))
        
        get_db().commit()
    except:
        print("Error updating match database.")
        return False

    return True