from app.db import get_db
import urllib
from flask import app

import requests
import csv

url = 'https://fixturedownload.com/download/uefa-euro-2020-UTC.csv'


def download_data_csv():
    r = requests.get(url)

    data_readear = csv.reader(r.content.decode("utf-8").splitlines(), delimiter=',')
    
    for idx, row in enumerate(data_readear):        
        if idx != 0:
            goals = row[7].split("-")
            
            for goal in goals:
                goal.replace(" ", "")

            #get_db.execute("UPDATE match SET team1 = ?, team2 = ?, goal1 =?, goal2=?", (row[4], row[5], goals[0], goals[1]))
    
    #get_db().commit()