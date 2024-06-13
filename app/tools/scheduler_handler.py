from flask import render_template_string
from flask import current_app
from flask_apscheduler import APScheduler
from flask_babel import force_locale
from sqlalchemy import text, bindparam

from app.tools.db_handler import get_db
from app.tools import database_manager
from app.tools import time_handler
from app.notification import notification_handler
from app import standings

from dateutil import tz
from datetime import timedelta
import shutil
import os

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
    utc_now = time_handler.get_now_time_object()
    current_localtime = utc_now.astimezone(tz.gettz('Europe/Budapest'))
    subject = 'Backup at: ' + current_localtime.strftime('%Y-%m-%d %H:%M')
    
    #create draft with the attached sqlite database file
    message = notification_handler.get_notifier().create_message_with_attachment(sender='me',
        to=admin_address,
        subject=subject,
        message_text='Backing up result database at: ' + current_localtime.strftime('%Y-%m-%d %H:%M'),
        file=current_app.config['DATABASE'])
    
    #create_draft(message_body=message)

def backup_sqlite_locally(timestamp : str):
    db_path = os.path.join(current_app.instance_path, 'flaskr.sqlite')
    backup_path = os.path.join(current_app.instance_path, 'flaskr_{date}.sqlite'.format(date=timestamp))
    shutil.copyfile(db_path, backup_path)

def match_reminder_once_per_day(match_ids : list):
    with scheduler.app.app_context():
        current_app.logger.info('Running scheduled match reminder...')

        query_string = text("SELECT date(match.datetime || bet_user.timezone) AS date, time(match.datetime || bet_user.timezone) AS time, tr1.translation AS team1, tr2.translation AS team2, "                            
                                "bet_user.username, bet_user.language, bet_user.reminder, bet_user.email, match_bet.goal1, match_bet.goal2, COALESCE(match_bet.bet, 0) as bet "
                            "FROM match "
                            "RIGHT JOIN bet_user ON bet_user.reminder IN (1, 2) "
                            "LEFT JOIN match_bet ON match_bet.match_id = match.id AND bet_user.username = match_bet.username "
                            "LEFT JOIN team_translation AS tr1 ON tr1.name = match.team1 AND tr1.language = bet_user.language "
                            "LEFT JOIN team_translation AS tr2 ON tr2.name = match.team2 AND tr2.language = bet_user.language "
                            "WHERE match.id IN :match_ids "
                            "ORDER BY bet_user.username, date, time "
                            )
        query_string = query_string.bindparams(bindparam('match_ids', expanding=True))
        result = get_db().session.execute(query_string, {'match_ids' : match_ids})

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

        sendable_messages = []

        for user in user_map.values():
            if user['reminder'] == 1 and len(user['missing']) == 0:
                continue

            message_object = notification_handler.get_notifier().get_notification_resource_by_tag('match-reminder')

            with force_locale(user['language']):
                message_subject = render_template_string(message_object[0], missing_bets=user['missing'], date=user['date'])
                message_text = render_template_string(message_object[1], non_missing_bets=user['nonmissing'], missing_bets=user['missing'], username=user['username'])
                sendable_messages.append(notification_handler.get_notifier().create_message(sender='me', user=user, subject=message_subject, message_text=message_text, subtype='html'))

        notification_handler.get_notifier().send_messages(sendable_messages)

def update_results():
    with scheduler.app.app_context():
        current_app.logger.info('Running scheduled result updater...')
        database_manager.update_match_data_from_fixture()
        #backup_sqlite_database()

def daily_standings():
    try:
        #TODO
        with scheduler.app.app_context():
            current_app.logger.info('Running scheduled daily standings creator...')

            messages = []
            notification_map = {}
            standings_map = {}

            query_string = text("SELECT username, email, language, date(:now || timezone) AS date "
                                "FROM bet_user "
                                "WHERE summary = 1")
            result = get_db().session.execute(query_string, {'now' : time_handler.get_now_time_string()})
            for user in result.fetchall():
                if user.language not in notification_map:
                    notification_map[user.language] = notification_handler.get_notifier().get_notification_resource_by_tag('standings')
                
                if user.language not in standings_map:
                    standings_map[user.language] = standings.create_standings(language=user.language)

                notification_object = notification_map[user.language]

                subject = render_template_string(notification_object[0], date=user.date)
                message_text = render_template_string(notification_object[1], username=user.username, date=user.date, standings=standings_map[user.language])

                messages.append(notification_handler.get_notifier().create_message(sender='me', user=user._asdict(), subject=subject, message_text=message_text, subtype='html'))

            notification_handler.get_notifier().send_messages(messages=messages)
    except Exception as error:
        current_app.logger.info('Error while sending daily standings: ' + str(error))
        return False
    
    return True

# daily checker schedules match reminders, standing notifications and database updating if there is a match on that day
def daily_checker():
    with scheduler.app.app_context():
        current_app.logger.info('Running daily scheduler at midnight...')

        match_time_length = current_app.config['MATCH_TIME_LENGTH']

        utc_now = time_handler.get_now_time_object()
        backup_sqlite_locally(utc_now.strftime('%Y-%m-%d'))

        query_string = text("SELECT * "
                            "FROM match "
                            "WHERE date(match.datetime) = date(:now_date) AND unixepoch(match.datetime) > unixepoch(:now_time) "
                            "ORDER BY unixepoch(match.datetime)")
        result = get_db().session.execute(query_string, {'now_date' : utc_now.strftime('%Y-%m-%d'), 'now_time' : utc_now.strftime('%Y-%m-%d %H:%M')})
            
        one_hour_before_first_match = None
        time_after_last_match = None

        matches = result.fetchall()
        match_ids_today = []
        for i, match in enumerate(matches):
            match_ids_today.append(match.id)
            match_time_object = time_handler.parse_datetime_string(match.datetime)

            if i == 0:
                one_hour_before_first_match = match_time_object - timedelta(hours = 1, minutes = 0)
                if utc_now > one_hour_before_first_match:
                    one_hour_before_first_match = None                    

            after_base_time = match_time_object + timedelta(hours=match_time_length['base_time'])
            match_after_base_task_id = str(match.id) + '. match after base'
            # schedule database update
            current_app.logger.info('Scheduled database update after match (base time) : ' + after_base_time.strftime('%Y-%m-%d %H:%M'))
            scheduler.add_job(id = match_after_base_task_id, func=update_results, trigger='date', run_date=after_base_time)

            after_extra_time = match_time_object + timedelta(hours=match_time_length['extra_time'])
            match_after_extra_task_id = str(match.id) + '. match after extra'
            # schedule database update
            current_app.logger.info('Scheduled database update after match (extra time) : ' + after_extra_time.strftime('%Y-%m-%d %H:%M'))
            scheduler.add_job(id = match_after_extra_task_id, func=update_results, trigger='date', run_date=after_extra_time)

            if i == len(matches) - 1:
                time_after_last_match = match_time_object + timedelta(hours=match_time_length['extra_time'], minutes=5)

        # send out first
        if one_hour_before_first_match is not None:
            current_app.logger.info('Scheduled match reminder at: ' + one_hour_before_first_match.strftime('%Y-%m-%d %H:%M'))
            scheduler.add_job(id = 'Daily match reminder', func=match_reminder_once_per_day, trigger='date', run_date=one_hour_before_first_match, args=[match_ids_today])

        #schedule sending daily standings
        if time_after_last_match is not None:
            current_app.logger.info('Scheduled standings reminder at: ' + (after_extra_time + timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M'))
            scheduler.add_job(id = 'Daily standings reminder', func=daily_standings, trigger='date', run_date=after_extra_time + timedelta(minutes=5))

def init_scheduler(app):    
    # if you don't wanna use a config, you can set options here:
    scheduler.api_enabled = True
    scheduler.init_app(app)

    #schedule checker to run at every day at midnight
    scheduler.add_job(id = 'Daily Task', func = daily_checker, trigger = 'cron', hour = 0, minute = 0, second = 0)

    scheduler.start()
