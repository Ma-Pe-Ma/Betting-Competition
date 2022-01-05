from flask_apscheduler import APScheduler
from app import file_request
from app.db import get_db
from pytz import utc
from dateutil import tz
from datetime import datetime, timedelta, date
from app.tools.ordering import order_matches2
from app.file_request import download_data_csv
from app.configuration import match_base_time, match_extra_time
scheduler = APScheduler()

from collections import namedtuple
Match=namedtuple("Match", "local1, local2, goal1, goal2, time")

def backup_sqlite_database():
    #TODO
    pass

def match_reminder_per_match(match):
    with scheduler.app.app_context():
        email_addresses = []
        
        for user in get_db().execute("SELECT username, email FROM user WHERE user.reminder = ?", (0,)).fetchall():
            if get_db().execute("SELECT * FROM match_bet WHERE username=? AND match_id=?", (user["username"], match["id"])).fetchone() is None:
                email_addresses.append(user["email"])

        print("emails permatch: " + str(email_addresses))

        #TODO: Send email

def match_reminder_once_per_day(matches):
    with scheduler.app.app_context():
        previous_bets = {}

        for user in get_db().execute("SELECT email, username FROM user WHERE user.reminder = ?", (1,)).fetchall():
            match_bets = []

            goal1 = None
            goal2 = None

            for match in matches:
                match_bet = get_db().execute("SELECT goal1, goal2 from match_bet WHERE match_id=? AND username=?", (match["id"], user["username"])).fetchone()

                if match_bet is not None:
                    goal1 = match_bet["goal1"]
                    goal2 = match_bet["goal2"]

                team1_local = get_db().execute("SELECT local_name FROM team WHERE name=?", (match["team1"],)).fetchone()
                team2_local = get_db().execute("SELECT local_name FROM team WHERE name=?", (match["team2"],)).fetchone()

                match_bets.append(Match(local1=team1_local["local_name"], local2=team2_local["local_name"], goal1=goal1, goal2=goal2, time=match["time"]))


            previous_bets[user["email"]] = match_bets
        
        for previous_bet in previous_bets:
            print("emails perday: " + previous_bet)

        #TODO SEND EMAIL

def update_results():
    with scheduler.app.app_context():
        download_data_csv()

def daily_standings():
    with scheduler.app.app_context():
        for user in get_db().execute("SELECT username, email from user WHERE summary=?", (1,)).fetchall():
            pass
            #TODO SEND EMAIL
        
        #TODO SEND SQLITE HERE?

def daily_checker():
    print("daily checker...")
    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))

    with scheduler.app.app_context():
        backup_sqlite_database()

        matches = get_db().execute("SELECT * FROM match WHERE DATE(time) == ?", (utc_now.strftime("%Y-%m-%d"),)).fetchall()

        if matches is not None and len(matches) > 0:
            matches.sort(key=order_matches2)

            for i, match in enumerate(matches):
                match_time_object = datetime.strptime(match["time"], "%Y-%m-%d %H:%M")
                match_time_object = match_time_object.replace(tzinfo=tz.gettz('UTC'))

                hour_before_match = match_time_object - timedelta(hours=1, minutes=0)
                match_before_task_id = str(match["id"]) + ". match before"

                scheduler.add_job(id = match_before_task_id, func=match_reminder_per_match, trigger="date", run_date=hour_before_match, args=[match])
                if i == 0:
                    scheduler.add_job(id = "Daily match reminder", func=match_reminder_once_per_day, trigger="date", run_date=hour_before_match, args=[matches])
    
                after_base_time = match_time_object + timedelta(hours=match_base_time)
                match_after_base_task_id = str(match["id"]) + ". match after base"
                scheduler.add_job(id = match_after_base_task_id, func=update_results, trigger="date", run_date=after_base_time)

                after_extra_time = match_time_object + timedelta(hours=match_extra_time)
                match_after_extra_task_id = str(match["id"]) + ". match after extra"
                scheduler.add_job(id = match_after_extra_task_id, func=update_results, trigger="date", run_date=after_extra_time)

                if i == len(matches) - 1:
                    scheduler.add_job(id = "Daily standings reminder", func=daily_standings, trigger="date", run_date=after_extra_time+timedelta(minutes=1))

def init_scheduler(app):    
    # if you don't wanna use a config, you can set options here:
    scheduler.api_enabled = True
    scheduler.init_app(app)

    scheduler.add_job(id = 'Daily Task', func=daily_checker, trigger="cron", hour=0, minute=0)
    #daily_checker()

    scheduler.start()