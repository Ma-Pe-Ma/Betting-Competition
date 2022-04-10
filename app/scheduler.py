from fileinput import filename
from flask_apscheduler import APScheduler
from flask import render_template_string
from app.db import get_db
from pytz import utc
from dateutil import tz
from datetime import datetime, timedelta
from app.gmail_handler import create_draft, create_message, create_message_with_attachment, send_messages, get_email_resource_by_tag
from app.database_manager import download_data_csv
from app.configuration import match_base_time, match_extra_time, local_zone
from flask import current_app
scheduler = APScheduler()

from collections import namedtuple
Match=namedtuple("Match", "local1, local2, goal1, goal2, time")
Bet = namedtuple("Bet", 'team1, team2, date, goal1, goal2')

def backup_sqlite_database():
    #find admin adresses
    admin_address = ''
    for admin in get_db().execute("SELECT email FROM user WHERE user.admin = TRUE", ()).fetchall():
        admin_address += admin['email'] + ', '

    #create string from current local date and add it to subject
    current_localtime = datetime.utcnow().replace(tzinfo=tz.gettz('UTC')).astimezone(local_zone)  
    subject = 'Backup at: ' + current_localtime.strftime("%Y-%m-%d %H:%M")
    
    #create draft with the attached sqlite database file
    message = create_message_with_attachment(sender='me',
        to=admin_address,
        subject=subject,
        message_text='Backing up result database at: ' + current_localtime.strftime("%Y-%m-%d %H:%M"),
        file=current_app.config['DATABASE'])
    
    create_draft(message_body=message)

#in the end this is not used
def match_reminder_per_match(match):
    with scheduler.app.app_context():        
        #get team properties
        team1_local = get_db().execute("SELECT local_name FROM team WHERE name=?", (match['team1'],)).fetchone()
        team2_local = get_db().execute("SELECT local_name FROM team WHERE name=?", (match['team2'],)).fetchone()
        
        match_time_utc = datetime.strptime(match["time"], "%Y-%m-%d %H:%M")
        match_time_utc = match_time_utc.replace(tzinfo=tz.gettz('UTC'))
        
        #object holding the correct time adjusted to timezone
        match_time_local = match_time_utc.astimezone(local_zone)
        match_time = match_time_local.strftime("%H:%M")

        #read email resource from file
        email_object = get_email_resource_by_tag('MatchReminder').format(notifiable_user[1], team1_local, team2_local, match_time)

        #format subject by match info
        subject = email_object[0].format(team1_local, team2_local, match_time)

        notifiable_users = []
        #find users who must be notified
        for user in get_db().execute("SELECT username, email FROM user WHERE user.reminder = ?", (0,)).fetchall():
            if get_db().execute("SELECT * FROM match_bet WHERE username=? AND match_id=?", (user['username'], match['id'])).fetchone() is None:
                notifiable_users.append((user['email'], user['username']))

        sendable_emails = []

        #create proper emails
        for notifiable_user in notifiable_users:
            message_text = email_object[1].format(notifiable_user[1], team1_local, team2_local, match_time)
            sendable_emails.append(create_message(sender='me', to=notifiable_user[0], subject=subject, message_text=message_text))

        send_messages(sendable_emails)

def match_reminder_once_per_day(matches):
    with scheduler.app.app_context():
        sendable_emails = []

        for user in get_db().execute("SELECT email, username, reminder FROM user WHERE (user.reminder = ? OR user.reminder = ?)" , (0,1)).fetchall():
            missing_bets = []
            non_missing_bets = []

            for match in matches:
                team1_local = get_db().execute("SELECT local_name FROM team WHERE name=?", (match["team1"],)).fetchone()['local_name']
                team2_local = get_db().execute("SELECT local_name FROM team WHERE name=?", (match["team2"],)).fetchone()['local_name']

                #match time in utc
                match_time_utc = datetime.strptime(match["time"], "%Y-%m-%d %H:%M")
                match_time_utc = match_time_utc.replace(tzinfo=tz.gettz('UTC'))
        
                #object holding the correct time adjusted to timezone
                match_time_local = match_time_utc.astimezone(local_zone)
                match_time = match_time_local.strftime("%H:%M")

                match_bet = get_db().execute("SELECT goal1, goal2 from match_bet WHERE match_id=? AND username=?", (match["id"], user["username"])).fetchone()

                # find matches with missing bets
                if match_bet is None or match_bet['goal1'] is None or match_bet['goal2'] is None:
                    missing_bets.append(Bet(team1=team1_local, team2=team2_local, date=match_time, goal1=None, goal2=None))
                # find matches with valid bets
                else:
                    goal1 = match_bet['goal1']
                    goal2 = match_bet['goal2']
                    non_missing_bets.append(Bet(team1=team1_local, team2=team2_local, date=match_time, goal1=goal1, goal2=goal2))
            
            # if user only cares about missing bets then continue to next user
            if user['reminder'] == 0:
                if len(missing_bets) == 0:
                    continue
                
            #create email message
            email_object = get_email_resource_by_tag('MatchReminder')

            subject = render_template_string(email_object[0], missing_bets=missing_bets)
            message_text = render_template_string(email_object[1], non_missing_bets=non_missing_bets, missing_bets=missing_bets)
            
            sendable_emails.append(create_message(sender='me', to=user['email'], subject=subject, message_text=message_text))

        send_messages(sendable_emails)

def update_results():
    with scheduler.app.app_context():
        download_data_csv()
        backup_sqlite_database()

def daily_standings():
    with scheduler.app.app_context():
        for user in get_db().execute("SELECT username, email from user WHERE summary=?", (1,)).fetchall():
            pass
            #TODO SEND EMAIL

# daily checker schedules match reminders, standing notifications and database updating if there is a match on that day
def daily_checker():
    print("daily checker...")
    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))

    with scheduler.app.app_context():
        backup_sqlite_database()

        matches = get_db().execute("SELECT * FROM match WHERE DATE(time) == ?", (utc_now.strftime("%Y-%m-%d"),)).fetchall()

        if matches is not None and len(matches) > 0:
            matches.sort(key=lambda match : datetime.strptime(match["time"], "%Y-%m-%d %H:%M"))

            for i, match in enumerate(matches):
                match_time_object = datetime.strptime(match["time"], "%Y-%m-%d %H:%M")
                match_time_object = match_time_object.replace(tzinfo=tz.gettz('UTC'))

                hour_before_match = match_time_object - timedelta(hours=1, minutes=0)
                match_before_task_id = str(match["id"]) + ". match before"

                #schedule reminder about missing betting
                #scheduler.add_job(id = match_before_task_id, func=match_reminder_per_match, trigger="date", run_date=hour_before_match, args=[match])
                if i == 0:
                    #schedule reminder about matches once before first match
                    scheduler.add_job(id = "Daily match reminder", func=match_reminder_once_per_day, trigger="date", run_date=hour_before_match, args=[matches])
    
                after_base_time = match_time_object + timedelta(hours=match_base_time)
                match_after_base_task_id = str(match["id"]) + ". match after base"
                # schedule database update
                scheduler.add_job(id = match_after_base_task_id, func=update_results, trigger="date", run_date=after_base_time)

                after_extra_time = match_time_object + timedelta(hours=match_extra_time)
                match_after_extra_task_id = str(match["id"]) + ". match after extra"
                # schedule database update
                scheduler.add_job(id = match_after_extra_task_id, func=update_results, trigger="date", run_date=after_extra_time)

                if i == len(matches) - 1:
                    #schedule sending daily standings
                    scheduler.add_job(id = "Daily standings reminder", func=daily_standings, trigger="date", run_date=after_extra_time + timedelta(minutes=1))

def init_scheduler(app):    
    # if you don't wanna use a config, you can set options here:
    scheduler.api_enabled = True
    scheduler.init_app(app)

    #schedule checker to run at every day at midnight
    scheduler.add_job(id = 'Daily Task', func=daily_checker, trigger="cron", hour=0, minute=0)
    #daily_checker()

    scheduler.start()