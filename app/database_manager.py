from datetime import datetime
from app.db import get_db, init_db
import urllib.request
import csv
from flask import current_app
import click
from flask.cli import with_appcontext
from app.configuration import default_max_bet_per_match

url = 'https://fixturedownload.com/download/fifa-world-cup-2022-UTC.csv'

def initialize_teams():
    with current_app.open_resource("teams.csv", 'r') as team_file:
        data_reader = csv.reader(team_file, delimiter='|')

        fields = next(data_reader)

        for i, row in enumerate(data_reader):
            position = i % 4 + 1
            get_db().execute("INSERT INTO team (name, local_name, group_id, position, top1, top2, top4, top16) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(row[0], row[1], row[2], position, row[3], row[4], row[5], row[6]))

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
            get_db().execute("INSERT INTO match (id, team1, team2, time, round, max_bet) VALUES (?, ?, ?, ?, ?, ?)", (row[0], row[4], row[5], time_string, row[1], default_max_bet_per_match))
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
                goals.split("-")
        
                for goal in goals:
                    goal.replace(" ", "")

                goal1 = goal[0]
                goal2 = goal[1]

            get_db().execute("UPDATE match SET team1 = ?, team2 = ?, goal1 =?, goal2=? WHERE id=?", (row[4], row[5], goal1, goal2, row[0]))
        
        get_db().commit()
    except:
        print("Error updating matches.da")

@click.command("init-db-with-data")
@with_appcontext
def init_db_with_data_command():
    """Clear existing data and create new tables."""
    init_db()
    initialize_teams()
    initialize_matches()
    click.echo("Initialized the database.")