from flask_apscheduler import APScheduler
from flask import render_template_string
from flask import current_app
from flask.cli import with_appcontext

import click
from sqlalchemy import text, bindparam

from dateutil import tz
from datetime import timedelta

from app.db import get_db
from app import gmail_handler
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
    message = gmail_handler.create_message_with_attachment(sender='me',
        to=admin_address,
        subject=subject,
        message_text='Backing up result database at: ' + current_localtime.strftime('%Y-%m-%d %H:%M'),
        file=current_app.config['DATABASE'])
    
    #create_draft(message_body=message)

def match_reminder_once_per_day(match_ids : list):
    print('Running scheduled match reminder...')

    with scheduler.app.app_context():
        query_string = text("SELECT date(match.time || bet_user.timezone) AS date, time(match.time || bet_user.timezone) AS time, tr1.translation AS team1, tr2.translation AS team2, "                            
                            "bet_user.username, bet_user.language, bet_user.reminder, bet_user.email, match_bet.goal1, match_bet.goal2, COALESCE(match_bet.bet, 0) as bet "
                            "FROM match "
                            "LEFT JOIN match_bet ON match_bet.match_id = match.id "
                            "LEFT JOIN bet_user ON bet_user.reminder IN (0, 1) "
                            "LEFT JOIN team_translation AS tr1 ON tr1.name = match.team1 AND tr1.language = bet_user.language "
                            "LEFT JOIN team_translation AS tr2 ON tr2.name = match.team2 AND tr2.language = bet_user.language "
                            "WHERE match.id IN :match_ids "
                            "ORDER BY bet_user.username, date, time "
                            )
        query_string = query_string.bindparams(bindparam('match_ids', expanding=True))
        result = get_db().session.execute(query_string, {'match_ids' : match_ids} )

        user_map = {}

        for user in result.fetchall():
            if user.username not in user_map:
                user_map[user.username] = {'username' : user.username, 'email' : user.email, 'reminder' : user.reminder, 'language' : user.language, 'date' : user.date, 'missing' : [], 'nonmissing' : []}

            user_dict = user._asdict()
            del user_dict['username']
            del user_dict['email']
            del user_dict['language']
            del user_dict['date']

            if user.bet == 0 or user.goal1 is None or user.goal2 is None:
                user_map[user.username]['missing'].append(user_dict)
            else:
                user_map[user.username]['nonmissing'].append(user_dict)

        sendable_emails = []

        for user in user_map.values():
            # TODO solve translating
            email_object = gmail_handler.get_email_resource_by_tag('MatchReminder')
            subject = render_template_string(email_object[0], missing_bets=user['missing'], date=user['date'])
            message_text = render_template_string(email_object[1], non_missing_bets=user['nonmissing'], missing_bets=user['missing'], username=user['username'])
            sendable_emails.append(gmail_handler.create_message(sender='me', to=user['email'], subject=subject, message_text=message_text, subtype='html'))

        gmail_handler.send_messages(sendable_emails)

def update_results():
    print('Running scheduled result updater...')

    with scheduler.app.app_context():
        download_data_csv()
        #backup_sqlite_database()

def daily_standings():
    print('Running scheduled daily standings creator...')

    with scheduler.app.app_context():
        #match time in utc
        utc_now = time_determiner.get_now_time_object()

        messages = []
        email_map = {}
        standings_map = {}

        query_string = text("SELECT username, email, language, date(:now || tz_offset) AS date"
                            "FROM bet_user "
                            "WHERE summary = 1")
        result = get_db().session.execute(query_string, {'now' : time_determiner.get_now_time_string()})
        for user in result.fetchall():
            if user.langugage not in email_map:
                email_map[user.language] = gmail_handler.get_email_resource_by_tag('DailyStandings', user.language)
            
            if user.language not in standings_map:
                standings_map[user.language] = create_standings(language=user.language)

            email_object = email_map[user.language]

            subject = render_template_string(email_object[0], date=user.date)
            message_text = render_template_string(email_object[1], username=user.username, date=user.date, standings=standings_map[user.language])

            messages.append(gmail_handler.create_message(sender='me', to=user.email, subject=subject, message_text=message_text, subtype='html'))

        gmail_handler.send_messages(messages=messages)

# daily checker schedules match reminders, standing notifications and database updating if there is a match on that day
def daily_checker():
    with scheduler.app.app_context():
        print('Running daily scheduler at midnight...')

        match_time_length = configuration.match_time_length

        utc_now = time_determiner.get_now_time_object()
        #backup_sqlite_database()

        query_string = text("SELECT * "
                            "FROM match "
                            "WHERE date(time) = date(:now_date) AND unixepoch(time) > unixepoch(:now_time) "
                            "ORDER BY unixepoch(match.time)")
        result = get_db().session.execute(query_string, {'now_date' : utc_now.strftime('%Y-%m-%d'), 'now_time' : utc_now.strftime('%Y-%m-%d %H:%M'), 'language' : 'hu', 'timezone' : '-01:00'})
            
        one_hour_before_first_match = None
        time_after_last_match = None

        matches = result.fetchall()
        match_ids_today = []
        for i, match in enumerate(matches):
            match_ids_today.append(match.id)
            match_time_object = time_determiner.parse_datetime_string(match.time) 

            if i == 0:
                one_hour_before_first_match = match_time_object - timedelta(hours = 1, minutes = 0)
                if utc_now > one_hour_before_first_match:
                    one_hour_before_first_match = None                    

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
                time_after_last_match = match_time_object + timedelta(hours=match_time_length.extra_time, minutes=5)
                
        # send out first
        if one_hour_before_first_match is not None:
            print('Scheduled match reminder at: ' + one_hour_before_first_match.strftime('%Y-%m-%d %H:%M'))
            scheduler.add_job(id = 'Daily match reminder', func=match_reminder_once_per_day, trigger='date', run_date=one_hour_before_first_match, args=[match_ids_today])

        #schedule sending daily standings
        if time_after_last_match is not None:
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
    scheduler.add_job(id = 'Daily Task', func = daily_checker, trigger = 'cron', hour = 0, minute = 0, second = 0)

    app.cli.add_command(manual_daily_checker)
    app.cli.add_command(manual_daily_standings)

    scheduler.start()