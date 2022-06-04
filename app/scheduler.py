from flask_apscheduler import APScheduler
from flask import render_template_string
from flask import current_app
from flask.cli import with_appcontext
import click

from dateutil import tz
from datetime import datetime, timedelta

from app.db import get_db
from app.gmail_handler import create_message, create_message_with_attachment, send_messages, get_email_resource_by_tag
from app.database_manager import download_data_csv
from app.configuration import match_base_time, match_extra_time, local_zone, supported_languages
from app.standings import create_standings

scheduler = APScheduler()

from collections import namedtuple
Match = namedtuple('Match', 'local1, local2, goal1, goal2, time')
Bet = namedtuple('Bet', 'team1, team2, date, goal1, goal2')

def backup_sqlite_database():
    #find admin adresses
    admin_address = ''

    cursor = get_db().cursor()
    cursor.execute('SELECT email FROM bet_user WHERE bet_user.admin = TRUE', ())

    for admin in cursor.fetchall():
        admin_address += admin['email'] + ', '

    #create string from current local date and add it to subject
    current_localtime = datetime.utcnow().replace(tzinfo=tz.gettz('UTC')).astimezone(local_zone)  
    subject = 'Backup at: ' + current_localtime.strftime('%Y-%m-%d %H:%M')
    
    #create draft with the attached sqlite database file
    message = create_message_with_attachment(sender='me',
        to=admin_address,
        subject=subject,
        message_text='Backing up result database at: ' + current_localtime.strftime('%Y-%m-%d %H:%M'),
        file=current_app.config['DATABASE'])
    
    #create_draft(message_body=message)

#in the end this is not used
def match_reminder_per_match(match):
    with scheduler.app.app_context():        
        #get team properties

        cursor1 = get_db().cursor()
        cursor1.execute('SELECT local_name FROM team WHERE name=%s', (match['team1'],))
        team1_local = cursor1.fetchone()

        cursor2 = get_db().cursor()
        cursor2.execute('SELECT local_name FROM team WHERE name=%s', (match['team2'],))
        team2_local = cursor2.fetchone()
        
        match_time_utc = datetime.strptime(match['time'], '%Y-%m-%d %H:%M')
        match_time_utc = match_time_utc.replace(tzinfo=tz.gettz('UTC'))
        
        #object holding the correct time adjusted to timezone
        match_time_local = match_time_utc.astimezone(local_zone)
        match_time = match_time_local.strftime('%H:%M')

        email_map = {}

        #read email resource from file
        for lan in supported_languages:
            email_map[lan] = get_email_resource_by_tag('MatchReminder', lan)

        notifiable_users = []
        #find users who must be notified

        cursor3 = get_db().cursor()
        cursor3.execute('SELECT username, email, language FROM bet_user WHERE user.reminder=%s', (0,))

        for user in cursor3.fetchall():
            cursor4 = get_db().cursor()
            cursor4.execute('SELECT * FROM match_bet WHERE username=%s AND match_id=%s', (user['username'], match['id']))
            if cursor4.fetchone() is None:
                notifiable_users.append((user['email'], user['username']))

        sendable_emails = []

        #create proper emails
        for notifiable_user in notifiable_users:
            #format subject by match info
            email_object = email_map[notifiable_user['language']]

            subject = email_object[0].format(team1_local, team2_local, match_time)
            message_text = email_object[1].format(notifiable_user[1], team1_local, team2_local, match_time)

            sendable_emails.append(create_message(sender='me', to=notifiable_user[0], subject=subject, message_text=message_text))

        send_messages(sendable_emails)

def match_reminder_once_per_day(matches):
    with scheduler.app.app_context():
        sendable_emails = []

        cursor = get_db().cursor()
        cursor.execute('SELECT email, username, reminder, language FROM bet_user WHERE (user.reminder = %s OR user.reminder = %s)', (0,1))

        for user in cursor.fetchall():
            missing_bets = []
            non_missing_bets = []

            for match in matches:
                cursor1 = get_db().cursor()
                cursor1.execute('SELECT local_name FROM team WHERE name=%s', (match['team1'],))
                team1_local = cursor1.fetchone()

                cursor2 = get_db().cursor()
                cursor2.execute('SELECT local_name FROM team WHERE name=%s', (match['team2'],))
                team2_local = cursor2.fetchone()

                #match time in utc
                match_time_utc = datetime.strptime(match['time'], '%Y-%m-%d %H:%M')
                match_time_utc = match_time_utc.replace(tzinfo=tz.gettz('UTC'))
        
                #object holding the correct time adjusted to timezone
                match_time_local = match_time_utc.astimezone(local_zone)
                match_time = match_time_local.strftime('%H:%M')

                cursor3 = get_db().cursor()
                cursor3.execute('SELECT goal1, goal2 from match_bet WHERE match_id=%s AND username=%s', (match['id'], user['username']))
                match_bet = cursor3.fetchone()

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
            email_object = get_email_resource_by_tag('MatchReminder', user['language'])

            subject = render_template_string(email_object[0], missing_bets=missing_bets)
            message_text = render_template_string(email_object[1], non_missing_bets=non_missing_bets, missing_bets=missing_bets)
            
            sendable_emails.append(create_message(sender='me', to=user['email'], subject=subject, message_text=message_text))

        send_messages(sendable_emails)

def update_results():
    with scheduler.app.app_context():
        download_data_csv()
        #backup_sqlite_database()

@click.command('standings-manual')
@with_appcontext
def daily_standings():
    with scheduler.app.app_context():
        #match time in utc
        utc_now = datetime.utcnow()
        utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))
        
        #object holding the correct date adjusted to timezone
        local_date = utc_now.astimezone(local_zone).strftime('%Y. %m. %d')

        messages = []

        email_map = {}

        for lan in supported_languages:
            email_map[lan] = get_email_resource_by_tag('DailyStandings', lan)

        standings = create_standings()

        cursor = get_db().cursor()
        cursor.execute('SELECT username, email, language from bet_user WHERE summary=%s', (1,))

        for user in cursor.fetchall():
            #create email message
            email_object = email_map[user['language']]

            subject = render_template_string(email_object[0], date=local_date)
            message_text = render_template_string(email_object[1], username=user['username'], date=local_date, standings=standings[1])

            messages.append(create_message(sender='me', to=user['email'], subject=subject, message_text=message_text, subtype='html'))

        send_messages(messages=messages)

# daily checker schedules match reminders, standing notifications and database updating if there is a match on that day
@click.command('checker-manual')
@with_appcontext
def daily_checker():    
    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))

    with scheduler.app.app_context():
        #backup_sqlite_database()

        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM match WHERE time::date = %s::date AND time::timestamp > %s::timestamp', (utc_now.strftime('%Y-%m-%d'), utc_now.strftime('%Y-%m-%d %H:%M'),))
        matches = cursor.fetchall()

        if matches is not None and len(matches) > 0:
            matches.sort(key=lambda match : datetime.strptime(match['time'], '%Y-%m-%d %H:%M'))

            for i, match in enumerate(matches):
                match_time_object = datetime.strptime(match['time'], '%Y-%m-%d %H:%M')
                match_time_object = match_time_object.replace(tzinfo=tz.gettz('UTC'))

                hour_before_match = match_time_object - timedelta(hours=1, minutes=0)
                match_before_task_id = str(match['id']) + '. match before'

                #schedule reminder about missing betting
                #scheduler.add_job(id = match_before_task_id, func=match_reminder_per_match, trigger="date", run_date=hour_before_match, args=[match])
                if i == 0:
                    #schedule reminder about matches once before first match

                    # if starting server midday, and time > (first match - 1h) then send email immidiately
                    if hour_before_match < utc_now:
                        hour_before_match = utc_now

                    scheduler.add_job(id = 'Daily match reminder', func=match_reminder_once_per_day, trigger='date', run_date=hour_before_match, args=[matches])
    
                after_base_time = match_time_object + timedelta(hours=match_base_time)
                match_after_base_task_id = str(match['id']) + '. match after base'
                # schedule database update
                scheduler.add_job(id = match_after_base_task_id, func=update_results, trigger='date', run_date=after_base_time)

                after_extra_time = match_time_object + timedelta(hours=match_extra_time)
                match_after_extra_task_id = str(match['id']) + '. match after extra'
                # schedule database update
                scheduler.add_job(id = match_after_extra_task_id, func=update_results, trigger='date', run_date=after_extra_time)

                if i == len(matches) - 1:
                    #schedule sending daily standings
                    scheduler.add_job(id = 'Daily standings reminder', func=daily_standings, trigger='date', run_date=after_extra_time + timedelta(minutes=1))

def init_scheduler(app):    
    # if you don't wanna use a config, you can set options here:
    scheduler.api_enabled = True
    scheduler.init_app(app)

    #schedule checker to run at every day at midnight
    scheduler.add_job(id = 'Daily Task', func=daily_checker, trigger='cron', hour=0, minute=0)

    app.cli.add_command(daily_checker)
    app.cli.add_command(daily_standings)

    scheduler.start()