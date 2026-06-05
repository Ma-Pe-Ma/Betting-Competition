from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
from flask import session
from flask import render_template_string
from flask import current_app
from enum import Enum

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import functools
import hashlib
import random
import string

from datetime import datetime, timedelta, UTC

from sqlalchemy import text
from flask_babel import gettext

from app.tools.db_handler import get_db
from app.tools.cache_handler import cache
from app.tools import time_handler
from app.notification import notification_handler

bp = Blueprint('auth', __name__, '''url_prefix="/auth"''')

@bp.before_app_request
def load_signed_in_user() -> None:
    session.permanent = True

    username = session.get('username')

    if username is None:
        g.user = None
    else:
        if 'last' in session:
            now = datetime.now(UTC)

            if now - session.get('last') >= timedelta(minutes=current_app.config['SESSION_LIFE_TIME']):
                session['username'] = None
                return '', 401
        
            session['last'] = now
            session.modified = True

        query_string = text('SELECT * FROM bet_user WHERE username = :username')
        result = get_db().session.execute(query_string, {'username' : username})

        user_row = result.fetchone()

        if user_row is None:
            session['username'] = None
            return '', 401

        g.user = (
            user_row._asdict()
        )

class Role(Enum):
    USER = 0,
    ADMIN = 1

def sign_in_required(role : Role = Role.USER):
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):
            if g.user is None:
                return '', 401

            if role == Role.ADMIN:
                if g.user['admin'] != 1:
                    return render_template('/error-handling/page-404.html'), 404
            elif cache.get('maintenance'):
                return render_template('/error-handling/page-503.html'), 503

            return view(*args, **kwargs)

        return wrapped_view
    
    return decorator

@bp.route('/register-message')
def introduction():
    introduction_query = text('SELECT message FROM messages WHERE id = 0')
    return get_db().session.execute(introduction_query).fetchone().message

@bp.route('/register', methods=['POST'])
def register() -> str:
    utc_now : datetime = time_handler.get_now_time_object()
    register_deadline : datetime = time_handler.parse_datetime_string(current_app.config['DEADLINE_TIMES']['register'])

    if utc_now > register_deadline:
        return gettext('Registering is not available anymore as the tournament has begun!.'), 400

    if g.user is not None:
        return '', 409

    user_data = request.json

    if 'language' not in user_data or user_data['language'] not in current_app.config['SUPPORTED_LANGUAGES']:
        best_language = (lambda keys : request.accept_languages.best_match(keys) or list(keys)[0])([language['key'] for language in current_app.config['SUPPORTED_LANGUAGES']])
        user_data['language'] = best_language

    db = get_db()
    error = None

    try:
        user_data['reminder'] = 1 if 'reminder' not in user_data else int(user_data['reminder'])
        user_data['summary'] = 0 if 'summary' not in user_data else int(user_data['summary'])
    except ValueError:
        error = gettext('Invalid reminder/summary value.')
    else:
        if 'username' not in user_data or len(str(user_data['username'])) < 3:
            error = gettext('Chosen nickname is too short (min. 3 characters).')
        elif len(str(user_data['username'])) > 20:
            error = gettext('Chosen nickname is too long (max. 20 characters).')
        elif 'email' not in user_data:
            error = gettext('E-mail address is required.')
        elif 'password1' not in user_data or 'password2' not in user_data or len(user_data['password1']) < 8:
            error = gettext('The given password is too short (min. 8 characters).')
        elif user_data['password1'] != user_data['password2']:
            error = gettext('The two passwords are not identical.')
        elif user_data['key'] != current_app.config['INVITATION_KEYS']['user'] and user_data['key'] != current_app.config['INVITATION_KEYS']['admin']:
            error = gettext('The invitation key is not valid.')
        else:
            query_string = text('SELECT * FROM bet_user WHERE username = :username')
            result = db.session.execute(query_string, {'username' : user_data['username'] })
            if result.fetchone() is not None:
                error = gettext('The chosen nickname is already taken.')
            else:
                query_string = text('SELECT * FROM bet_user WHERE email = :email')
                result = db.session.execute(query_string, {'email' : user_data['email']})
                if result.fetchone() is not None:
                    error = gettext('The chosen email address is already taken.')

    if error is not None:
        return error, 400

    user_data['password1'] = generate_password_hash(user_data['password1'])
    user_data['admin'] = user_data['key'] == current_app.config['INVITATION_KEYS']['admin']
    # TODO CHECK AND ADD TIMEZONE!
    user_data['timezone'] = 'Europe/Budapest'

    if 'reminder' not in user_data or 'summary' not in user_data:
        user_data['reminder'] = 1
        user_data['summary'] = 0

    user_data['email_hash'] = hashlib.md5(user_data['email'].lower().encode('utf-8')).hexdigest()

    query_string = text("INSERT INTO bet_user (username, password, email, reminder, summary, language, admin, timezone, email_hash) " 
                        "VALUES (TRIM(:username), :password1, TRIM(:email), TRIM(:reminder), TRIM(:summary), TRIM(:language), :admin, TRIM(:timezone), :email_hash)")
    result = db.session.execute(query_string, user_data)
    db.session.commit()

    session['username'] = user_data['username']
    session.permanent = True

    # sending welcome notification
    messages = []
    message_object = notification_handler.get_notifier().get_notification_resource_by_tag('welcome')
    message_subject = render_template_string(message_object[0])
    message_text = render_template_string(message_object[1], username=user_data['username'])
    messages.append(notification_handler.get_notifier().create_message(sender='me', user=user_data, subject=message_subject, message_text=message_text, subtype='html'))

    notification_handler.get_notifier().send_messages(messages)

    # if first time sign in upload team data
    result = db.session.execute(text('SELECT * FROM bet_user'))

    return gettext('Registering successful'), 200

@bp.route('/sign-in', methods=['POST'])
def sign_in() -> str:
    # Redirect to homepage if user is already signed in
    if g.user is not None:
        return '', 409

    if 'username' not in request.json or 'password1' not in request.json:
        return gettext('Username or password is not specified!'), 400

    username = request.json['username']
    password = request.json['password1']
    
    query_string = text('SELECT * FROM bet_user WHERE username = :username')
    result = get_db().session.execute(query_string, {'username' : username})
    user = result.fetchone()

    error = None

    if user is None:
        error = gettext('Invalid username!')
    elif not check_password_hash(user.password, password):
        error = gettext('Invalid password!')

    if error is not None:        
        return error, 400

    session['username'] = user.username
    session.permanent = True

    if 'keepSignedIn' not in request.json or request.json['keepSignedIn'] == False:
        session['last'] = datetime.now(UTC)

    return gettext('Successful sign in'), 200

@bp.route('/sign-out')
@sign_in_required()
def sign_out() -> str:
    session['username'] = None
    return gettext('Successful sign out'), 200

@bp.route('/profile-get', methods=['GET'])
@sign_in_required()
def get_profile():
    query_string = text('SELECT username, email, reminder, summary, language FROM bet_user WHERE username=:username')
    result = get_db().session.execute(query_string, {'username' : g.user['username']})
    user_data = result.fetchone()._asdict()

    return user_data

@bp.route('/profile-set', methods=['POST'])
@sign_in_required()
def post_profile() -> str:
    user_data = request.json

    try:
        user_data['reminder'] = 1 if 'reminder' not in user_data else int(user_data['reminder'])
        user_data['summary'] = 0 if 'summary' not in user_data else int(user_data['summary'])
    except:
        user_data['reminder'] = 1
        user_data['summary'] = 0

    query_string = text('UPDATE bet_user SET reminder=:r, summary=:s WHERE username=:u')
    get_db().session.execute(query_string, {'r' : user_data['reminder'], 's' : user_data['summary'], 'u' : g.user['username']})
    get_db().session.commit()

    return gettext('Settings were successfully modified'), 200

@bp.route('/forgotten-password', methods=['POST'])
def forgotten_password():
    if g.user is not None:
        return '', 409

    user_data = request.json

    if 'email' not in user_data:
        return gettext('Email is not specified'), 400

    db = get_db()
    query_string = text('SELECT * FROM bet_user WHERE email = :email')
    result = db.session.execute(query_string, user_data)

    if result.fetchone() is None:
        return gettext('Email is not registered'), 400
    
    reset_keys = cache.get('password_reset_keys')

    if reset_keys is None:
        reset_keys = []

    current_reset_key = None

    for r in reset_keys:
        if r['email'] == user_data['email']:
            current_reset_key = r
            break

    if current_reset_key == None:
        current_reset_key = {'email' : user_data['email']}
        reset_keys.append(current_reset_key)
          
    current_reset_key.update({
        'date' : time_handler.stringify_datetime_object(time_handler.get_now_time_object() + timedelta(hours=24)),
        'key' : ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20)) 
    })

    cache.set('password_reset_keys', reset_keys, 3600 * 24)

    message = gettext('New password requested! Please contact one of the admins for further actions!')
    if current_app.config['DIRECT_MESSAGING'] == 1:
        message = gettext('New password requested! Check your email for further actions!')              

    return message, 200

@bp.route('/reset-password', methods=['POST'])
def reset_password() -> str:
    if g.user is not None:
        return '', 409

    user_data = request.json

    db = get_db()
    error = None
    user = None

    if 'email' not in user_data:
        error = gettext('Email is not specified.')
    elif 'key' not in user_data:
        error = gettext('Reset key is not specified.')
    elif 'password1' not in user_data or len(user_data['password1']) < 8:
        error = gettext('The given password is too short (min. 8 characters).')
    elif user_data['password1'] != user_data['password2']:
        error = gettext('The two passwords are not identical.')
    else:
        query_string = text('SELECT * FROM bet_user WHERE email = :email')
        result = db.session.execute(query_string, user_data)
        user = result.fetchone()
        if user is None:
            error = gettext('The given nickname does not exist.')
        else:
            reset_keys = cache.get('password_reset_keys')
            current_key = None

            for key in (reset_keys or []):
                if key['email'] == user.email:
                    current_key = key

            if not reset_keys or not current_key or time_handler.get_now_time_object() > time_handler.parse_datetime_string(current_key['date']):
                error = gettext('No password reset key has been requested.')
            elif current_key['key'] != user_data['key']:
                error = gettext('The given reset key is invalid.')

    if error is not None:
        return error, 400
    
    reset_keys.remove(current_key)

    cache.set('password_reset_keys', reset_keys, 3600 * 24)

    password_change_query_string = text('UPDATE bet_user SET password=:password1 WHERE email=:email')
    user_data['password1'] = generate_password_hash(user_data['password1'])
    result = db.session.execute(password_change_query_string, user_data)
    db.session.commit()

    session['username'] = user.username
    session.permanent = True

    return gettext('Password was reset successfully!'), 200

@bp.route('/status', methods=['GET'])
def check_auth_status():
    session['language'] = request.args.get('lan', current_app.config['SUPPORTED_LANGUAGES'][0]['key'])
    session.permanent = True
    session.modified = True

    if g.user is not None:
        if session['language'] != g.user['language']:
            query_string = text('UPDATE bet_user SET language=:l WHERE username=:u')
            get_db().session.execute(query_string, {'l' : session['language'], 'u' : g.user['username']})
            get_db().session.commit()

        query_string = text('SELECT * FROM messages WHERE id > 0')
        messages = []
        
        for row in get_db().session.execute(query_string).fetchall():
            if row.message is not None and row.message != '':
                messages.append({'message' : row.message, 'type' : 'info'})        

        return {
            'role' : (1 if g.user['admin'] else 0),
            'hash' : current_app.config['IDENT_URL'].format(email_hash=g.user['email_hash']),
            'username' : g.user['username'],
            'messages' : messages,
            'timezone' : g.user['timezone']
        }

    session['username'] = None

    return {'role' : None}
