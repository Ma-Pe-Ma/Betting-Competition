from flask import Blueprint
from flask import redirect
from flask import g
from flask import flash
from flask import render_template
from flask import request
from flask import session
from flask import url_for
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
from flask_babel import force_locale

from app.tools.db_handler import get_db
from app.tools.cache_handler import cache
from app.tools import time_handler
from app.notification import notification_handler

bp = Blueprint('auth', __name__, '''url_prefix="/auth"''')

@bp.before_app_request
def load_signed_in_user() -> None:
    session.permanent = True
    
    if 'last' in session:
        now = datetime.now(UTC)

        if now - session.get('last') >= timedelta(minutes=current_app.config['SESSION_LIFE_TIME']):
            session.clear()
            return redirect(url_for('auth.sign_in'))
        
        session['last'] = now
        session.modified = True

    username = session.get('username')

    if username is None:
        g.user = None
    else:
        query_string = text('SELECT * FROM bet_user WHERE username = :username')
        result = get_db().session.execute(query_string, {'username' : username})

        user_row = result.fetchone()

        if user_row is None:
            session.clear()
            return redirect(url_for('auth.sign_in'))

        g.user = (
            user_row._asdict()
        )

class Role(Enum):
    USER = 0,
    ADMIN = 1

def sign_in_required(role : Role = Role.USER):
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                return redirect(url_for('auth.sign_in'))
            
            if role == Role.ADMIN and g.user['admin'] != 1:
                return render_template('/error-handling/page-404.html'), 404

            return view(**kwargs)

        return wrapped_view
    
    return decorator

@bp.route('/register', methods=('GET', 'POST'))
def register() -> str:
    utc_now : datetime = time_handler.get_now_time_object()
    register_deadline : datetime = time_handler.parse_datetime_string(current_app.config['DEADLINE_TIMES']['register'])
    best_language = request.accept_languages.best_match(current_app.config['SUPPORTED_LANGUAGES'].keys())

    if utc_now > register_deadline:
        return render_template('/auth/register-fail.html')

    if g.user is not None:
        return redirect(url_for('home.homepage'))
    
    introduction_query = text('SELECT message FROM messages WHERE id = 0')
    introduction = get_db().session.execute(introduction_query).fetchone().message

    if request.method == 'POST':
        user_data = request.form.to_dict(flat=True)

        if user_data['language'] not in current_app.config['SUPPORTED_LANGUAGES']:
            user_data['language'] = best_language
        
        user_data['language_number'] = list(current_app.config['SUPPORTED_LANGUAGES'].keys()).index(user_data['language'])

        db = get_db()
        error = None
        if not user_data['username'] or len(str(user_data['username'])) < 3:
            error = (gettext('Chosen nickname is too short (min. 3 characters).'), 'danger')
        elif len(str(user_data['username'])) > 20:
            error = (gettext('Chosen nickname is too long (max. 20 characters).'), 'danger')
        elif not user_data['email']:
            error = (gettext('E-mail address is required.'), 'danger')
        elif not user_data['password1'] or len(user_data['password1']) < 8:
            error = (gettext('The given password is too short (min. 8 characters).'), 'danger')
        elif user_data['password1'] != user_data['password2']:
            error = (gettext('The two passwords are not identical.'), 'danger')
        elif user_data['key'] != current_app.config['INVITATION_KEYS']['user'] and user_data['key'] != current_app.config['INVITATION_KEYS']['admin']:
            error = (gettext('The invitation key is not valid.'), 'danger')
        else:
            try:
                user_data['reminder'] = 0 if 'reminder' not in user_data else int(user_data['reminder'])
                user_data['summary'] = 0 if 'summary' not in user_data else int(user_data['summary'])
            except ValueError:
                error = (gettext('Invalid reminder/summary value.'), 'danger')
            else:
                query_string = text('SELECT * FROM bet_user WHERE username = :username')
                result = db.session.execute(query_string, {'username' : user_data['username'] })
                if result.fetchone() is not None:
                    error = (gettext('The chosen nickname is already taken.'), 'danger')
                else:
                    query_string = text('SELECT * FROM bet_user WHERE email = :email')
                    result = db.session.execute(query_string, {'email' : user_data['email']})
                    if result.fetchone() is not None:
                        error = (gettext('The chosen email address is already taken.'), 'danger')

        if error is not None:
            flash(error[0], error[1])
            with force_locale(user_data['language']):
                return render_template('/auth/register.html', user_data = user_data, introduction=introduction)

        user_data['password1'] = generate_password_hash(user_data['password1'])
        user_data['admin'] = user_data['key'] == current_app.config['INVITATION_KEYS']['admin']
        # TODO CHECK AND ADD TIMEZONE!
        user_data['timezone'] = '-01:00'

        if 'reminder' not in user_data or 'summary' not in user_data:
            user_data['reminder'] = 0
            user_data['summary'] = 0

        user_data['email_hash'] = hashlib.md5(user_data['email'].lower().encode('utf-8')).hexdigest()

        query_string = text("INSERT INTO bet_user (username, password, email, reminder, summary, language, admin, timezone, email_hash) " 
                            "VALUES (:username, :password1, :email, :reminder, :summary, :language, :admin, :timezone, :email_hash)")
        result = db.session.execute(query_string, user_data)
        db.session.commit()

        session.clear()
        session['username'] = user_data['username']
        session.permanent = True

        # sending welcome notification
        messages = []
        message_object = notification_handler.notifier.get_notification_resource_by_tag('welcome')
        message_subject = render_template_string(message_object[0])
        message_text = render_template_string(message_object[1], username=user_data['username'])
        messages.append(notification_handler.notifier.create_message(sender='me', user=user_data, subject=message_subject, message_text=message_text, subtype='html'))

        notification_handler.notifier.send_messages(messages)

        # if first time sign in upload team data
        result = db.session.execute(text('SELECT * FROM bet_user'))

        if len(result.fetchall()) <= 1:
            return redirect(url_for('admin.admin_page'))

        return redirect(url_for('group.group_order'))

    best_language_number = list(current_app.config['SUPPORTED_LANGUAGES'].keys()).index(best_language)

    user_data = {
        'reminder' : 0,
        'summary' : 0,
        'language' : best_language,
        'language_number': best_language_number
    }

    # TODO: 
    if current_app.debug:
        user_data = {
            'username' : 'MPM',
            'email' : 'mpm@mpm.mpm',
            'password1' : 'aaaaaaaa',
            'password2' : 'aaaaaaaa',
            'key' : current_app.config['INVITATION_KEYS']['admin'],
            'reminder' : 0,
            'summary' : 0,        
            'language' : best_language,
            'language_number': best_language_number
        }

    with force_locale(user_data['language']):
        return render_template('/auth/register.html', user_data=user_data, introduction=introduction)

@bp.route('/sign-in', methods=('GET', 'POST'))
def sign_in() -> str:
    # Redirect to homepage if user is already signed in
    if g.user is not None:
        return redirect(url_for('home.homepage'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        query_string = text('SELECT * FROM bet_user WHERE username = :username')
        result = get_db().session.execute(query_string, {'username' : username})
        user = result.fetchone()

        error = None

        if user is None:
            error = (gettext('Invalid username!'), 'danger')
        elif not check_password_hash(user.password, password):
            error = (gettext('Invalid password!'), 'danger')

        if error is not None:
            flash(error[0], error[1])
            return render_template('/auth/sign-in.html', username_form=username)

        session.clear()
        session['username'] = user.username
        session.permanent = True

        if 'stay' not in request.form:
            session['last'] = datetime.now(UTC)

        return redirect(url_for('home.homepage'))

    return render_template('/auth/sign-in.html')

@bp.route('/sign-out')
def sign_out() -> str:
    session.clear()
    return redirect(url_for('auth.sign_in'))

@bp.route('/profile', methods=('GET', 'POST'))
@sign_in_required()
def page_profile() -> str:
    if request.method == 'POST':
        user_data = request.form.to_dict(flat=True)

        if user_data['language'] not in current_app.config['SUPPORTED_LANGUAGES']:
            user_data['language'] = request.accept_languages.best_match(current_app.config['SUPPORTED_LANGUAGES'].keys())

        try:
            user_data['reminder'] = 0 if 'reminder' not in user_data else int(user_data['reminder'])
            user_data['summary'] = 0 if 'summary' not in user_data else int(user_data['summary'])
        except:
            user_data['reminder'] = 0
            user_data['summary'] = 0

        query_string = text('UPDATE bet_user SET reminder=:r, summary=:s, language=:l WHERE username=:u')
        get_db().session.execute(query_string, {'r' : user_data['reminder'], 's' : user_data['summary'], 'l' : user_data['language'], 'u' : g.user['username']})
        get_db().session.commit()

        g.user['language'] = user_data['language']

        flash(gettext('Settings were successfully modified'), 'success')

    query_string = text('SELECT username, email, reminder, summary, language FROM bet_user WHERE username=:username')
    result = get_db().session.execute(query_string, {'username' : g.user['username']})
    user_data = result.fetchone()._asdict()
    user_data['language_number'] = list(current_app.config['SUPPORTED_LANGUAGES'].keys()).index(user_data['language'])

    return render_template('/auth/profile.html', user_data = user_data, disabled = True)

@bp.route('/forgotten-password', methods=('GET', 'POST'))
def forgotten_password():
    if g.user is not None:
        return redirect(url_for('home.homepage'))

    email = ''
    requested = False

    if request.method == 'POST':
        user_data = request.form.to_dict(flat=True)
        email = user_data['email'] if 'email' in user_data else ''        

        if 'email' not in user_data:
            flash(gettext('Email is not registered'), 'danger')
        else:
            db = get_db()
            query_string = text('SELECT * FROM bet_user WHERE email = :email')
            result = db.session.execute(query_string, user_data)

            if result.fetchone() is None:
                flash(gettext('Email is not registered'), 'danger')
            else:
                requested = True
                reset_keys = cache.get('password_reset_keys')

                if reset_keys is None:
                    reset_keys = {}

                reset_keys[user_data['email']] = {
                    'date' : time_handler.stringify_datetime_object(time_handler.get_now_time_object() + timedelta(hours=24)),
                    'key' : ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))
                }

                cache.set('password_reset_keys', reset_keys, 3600 * 24)

                if current_app.config['DIRECT_MESSAGING'] == 1:
                    pass # TODO: send reset key in email to user

    return render_template('auth/forgotten-password.html', requested=requested, email=email)

@bp.route('/reset-password', methods=('GET', 'POST'))
def reset_password() -> str:
    if g.user is not None:
        return redirect(url_for('home.homepage'))
    
    best_language = request.accept_languages.best_match(current_app.config['SUPPORTED_LANGUAGES'].keys())
    
    if request.method == 'GET':
        with force_locale(best_language):
            return render_template('auth/reset-password.html', user_data=request.args.to_dict(), error=None)

    if request.method == 'POST':
        user_data = request.form.to_dict(flat=True)

        db = get_db()
        error = None
        user = None

        if not user_data['email']:
            error = (gettext('Email is not specified.'), 'danger')
        elif not user_data['key']:
            error = (gettext('Reset key is not specified.'), 'danger')
        elif not user_data['password1'] or len(user_data['password1']) < 8:
            error = (gettext('The given password is too short (min. 8 characters).'), 'danger')
        elif user_data['password1'] != user_data['password2']:
            error = (gettext('The two passwords are not identical.'), 'danger')
        else:
            query_string = text('SELECT * FROM bet_user WHERE email = :email')
            result = db.session.execute(query_string, user_data)
            user = result.fetchone()
            if user is None:
                error = (gettext('The given nickname does not exist.'), 'danger')
            else:
                reset_keys = cache.get('password_reset_keys')

                if not reset_keys or user.email not in reset_keys or time_handler.get_now_time_object() > time_handler.parse_datetime_string(reset_keys[user.email]['date']):
                    error = (gettext('No password reset key has been requested.'), 'danger')
                elif reset_keys[user.email]['key'] != user_data['key']:
                    error = (gettext('The given reset key is invalid.'), 'danger')

        if error is not None:
            lan = user.language if user is not None else best_language
            flash(error[0], error[1])
            with force_locale(lan):
                return render_template('auth/reset-password.html', user_data=user_data, error=error)
        
        del reset_keys[user.email]
        cache.set('password_reset_keys', reset_keys, 3600 * 24)

        password_change_query_string = text('UPDATE bet_user SET password=:password1 WHERE email=:email')
        user_data['password1'] = generate_password_hash(user_data['password1'])
        result = db.session.execute(password_change_query_string, user_data)
        db.session.commit()

        session.clear()
        session['username'] = user.username
        session.permanent = True

        return redirect(url_for('home.homepage'))    
