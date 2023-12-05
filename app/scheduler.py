from flask_apscheduler import APScheduler
from flask import render_template_string
from flask import current_app
from flask.cli import with_appcontext

import click
from sqlalchemy import text

from dateutil import tz
from datetime import datetime, timedelta

from app.db import get_db
from app.gmail_handler import create_message, create_message_with_attachment, send_messages, get_email_resource_by_tag
from app.database_manager import download_data_csv
from app.configuration import configuration
from app.standings import create_standings
from app.tools import time_determiner

scheduler = APScheduler()

# obsoleted
def backup_sqlite_database():
    #find admin adresses
    admin_address = ''

    query_string = text('SELECT email FROM bet_user WHERE bet_user.admin = TRUE')
    result = get_db().session.execute(query_string)

    for admin in result.fetchall():
        admin_address += admin.email + ', '

    #create string from current local date and add it to subject
    utc_now = time_determiner.get_now_time_object()
    current_localtime = utc_now.astimezone(tz.gettz('Europe/Budapest'))  
    subject = 'Backup at: ' + current_localtime.strftime('%Y-%m-%d %H:%M')
    
    #create draft with the attached sqlite database file
    message = create_message_with_attachment(sender='me',
        to=admin_address,
        subject=subject,
        message_text='Backing up result database at: ' + current_localtime.strftime('%Y-%m-%d %H:%M'),
        file=current_app.config['DATABASE'])
    
    #create_draft(message_body=message)

def match_reminder_once_per_day(matches):
    print('Running scheduled match reminder...')

    with scheduler.app.app_context():
        utc_now = time_determiner.get_now_time_object()
        
        #object holding the correct date adjusted to timezone
        local_date = utc_now.astimezone(tz.gettz('Europe/Budapest')).strftime('%Y. %m. %d')

        sendable_emails = []

        query_string = text('SELECT email, username, reminder, language FROM bet_user WHERE (user.reminder = 0 OR user.reminder = 1)')
        result = get_db().session.execute(query_string)
        for user in result.fetchall():
            missing_bets = []
            non_missing_bets = []

            for match in matches:
                query_string = text('SELECT translation FROM team_translation WHERE name=:teamname AND language=:language')

                result1 = get_db().session.execute(query_string, {'teamname' : match.team1, 'language' :  user.language})
                team1_local = result1.fetchone()

                result2 = get_db().session.execute(query_string, {'teamname' : match.team2, 'language' : user.language})
                team2_local = result2.fetchone()

                #match time in utc
                match_time_utc = datetime.strptime(match.time, '%Y-%m-%d %H:%M')
                match_time_utc = match_time_utc.replace(tzinfo=tz.gettz('UTC'))
        
                #object holding the correct time adjusted to timezone
                match_time_local = match_time_utc.astimezone(local_zone)
                match_time = match_time_local.strftime('%H:%M')

                query_string = text('SELECT goal1, goal2 from match_bet WHERE match_id=:match_id AND username=:username')
                result3 = get_db().session.execute(query_string, {'match_id' : match.id, 'username' : user.username})
                match_bet = result3.fetchone()

                # find matches with missing bets
                if match_bet is None or match_bet.goal1 is None or match_bet.goal2 is None:
                    missing_bets.append( {'team1' : team1_local.translation, 'team2' : team2_local.translation, 'date' : match_time, 'goal1' : None, 'goal2' : None} )
                # find matches with valid bets
                else:
                    goal1 = match_bet.goal1
                    goal2 = match_bet.goal2
                    non_missing_bets.append({'team1' : team1_local.translation, 'team2' : team2_local.translation, 'date' : match_time, 'goal1' : goal1, 'goal2' : goal2})
            
            # if user only cares about missing bets then continue to next user
            if user.reminder == 0:
                if len(missing_bets) == 0:
                    continue
                
            #create email message
            email_object = get_email_resource_by_tag('MatchReminder', user['language'])

            subject = render_template_string(email_object[0], missing_bets=missing_bets, date=local_date)
            message_text = render_template_string(email_object[1], non_missing_bets=non_missing_bets, missing_bets=missing_bets, username=user.username)
            
            sendable_emails.append(create_message(sender='me', to=user.email, subject=subject, message_text=message_text, subtype='html'))

        send_messages(sendable_emails)

def update_results():
    print('Running scheduled result updater...')

    with scheduler.app.app_context():
        download_data_csv()
        #backup_sqlite_database()

def daily_standings():
    local_zone =  tz.gettz(configuration.local_zone)
    print('Running scheduled daily standings creator...')

    with scheduler.app.app_context():
        #match time in utc
        utc_now = time_determiner.get_now_time_object()
        
        #object holding the correct date adjusted to timezone
        local_date = utc_now.astimezone(local_zone).strftime('%Y. %m. %d')

        messages = []
        email_map = {}

        for lan in configuration.supported_languages:
            email_map[lan] = get_email_resource_by_tag('DailyStandings', lan)

        # TODO: use users' chosen language
        standings = create_standings(language=configuration.supported_languages[0])

        query_string = text('SELECT username, email, language from bet_user WHERE summary=1')
        result = get_db().session.execute(query_string)
        for user in result.fetchall():
            #create email message
            email_object = email_map[user.language]

            subject = render_template_string(email_object[0], date=local_date)
            message_text = render_template_string(email_object[1], username=user.username, date=local_date, standings=standings[1])

            messages.append(create_message(sender='me', to=user.email, subject=subject, message_text=message_text, subtype='html'))

        send_messages(messages=messages)

# daily checker schedules match reminders, standing notifications and database updating if there is a match on that day
def daily_checker():
    with scheduler.app.app_context():
        print('Running daily scheduler at midnight...')

        match_time_length = configuration.match_time_length

        utc_now = time_determiner.get_now_time_object()
        #backup_sqlite_database()

        query_string = text('SELECT * FROM match WHERE date(time) = date(:now_date) AND unixepoch(time) > unixepoch(:now_time)')
        result = get_db().session.execute(query_string, {'now_date' : utc_now.strftime('%Y-%m-%d'), 'now_time' : utc_now.strftime('%Y-%m-%d %H:%M')})
        matches = result.fetchall()

        if matches is not None and len(matches) > 0:
            matches.sort(key=lambda match : datetime.strptime(match['time'], '%Y-%m-%d %H:%M'))

            for i, match in enumerate(matches):
                match_time_object = datetime.strptime(match.time, '%Y-%m-%d %H:%M')
                match_time_object = match_time_object.replace(tzinfo=tz.gettz('UTC'))

                hour_before_match = match_time_object - timedelta(hours=1, minutes=0)

                #schedule reminder about missing betting
                if i == 0:
                    #schedule reminder about matches once before first match

                    # if starting server midday, and time > (first match - 1h) then send email immidiately
                    if hour_before_match < utc_now:
                        hour_before_match = utc_now

                    print('Scheduled match reminder at: ' + hour_before_match.strftime('%Y-%m-%d %H:%M'))
                    scheduler.add_job(id = 'Daily match reminder', func=match_reminder_once_per_day, trigger='date', run_date=hour_before_match, args=[matches])
    
                after_base_time = match_time_object + timedelta(hours=match_time_length.base_time)
                match_after_base_task_id = str(match.id) + '. match after base'
                # schedule database update
                print('Scheduled database update after match (base time) : ' + after_base_time.strftime('%Y-%m-%d %H:%M'))
                scheduler.add_job(id = match_after_base_task_id, func=update_results, trigger='date', run_date=after_base_time)

                after_extra_time = match_time_object + timedelta(hours=match_time_length.extra_time)
                match_after_extra_task_id = str(match.id) + '. match after extra'
                # schedule database update
                print('Scheduled database update after match (extra time) : ' + after_extra_time.strftime('%Y-%m-%d %H:%M'))
                scheduler.add_job(id = match_after_extra_task_id, func=update_results, trigger='date', run_date=after_extra_time)

                if i == len(matches) - 1:
                    #schedule sending daily standings
                    print('Scheduled standings reminder at: ' + (after_extra_time + timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M'))
                    scheduler.add_job(id = 'Daily standings reminder', func=daily_standings, trigger='date', run_date=after_extra_time + timedelta(minutes=5))

@click.command('checker-manual')
@with_appcontext
def manual_daily_checker():
    daily_checker()

@click.command('standings-manual')
@with_appcontext
def manual_daily_standings():
    daily_standings()

def init_scheduler(app):    
    # if you don't wanna use a config, you can set options here:
    scheduler.api_enabled = True
    scheduler.init_app(app)

    #schedule checker to run at every day at midnight
    scheduler.add_job(id = 'Daily Task', func=daily_checker, trigger='cron', hour=0, minute=0, second=0)

    app.cli.add_command(manual_daily_checker)
    app.cli.add_command(manual_daily_standings)

    scheduler.start()