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

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import functools

from datetime import datetime

from sqlalchemy import text
from enum import Enum
from flask_babel import gettext
from dateutil import tz

from app.db import get_db
from app.configuration import configuration

from app.tools import time_determiner

from app.gmail_handler import get_email_resource_by_tag
from app.gmail_handler import send_messages, create_message

bp = Blueprint('auth', __name__, '''url_prefix="/auth"''')

@bp.before_app_request
def load_logged_in_user() -> None:
    username = session.get('username')

    if username is None:
        g.user = None
    else:
        query_string = text('SELECT * FROM bet_user WHERE username = :username')
        result = get_db().session.execute(query_string, {'username' : username})

        user_row = result.fetchone()

        #TODO REDIRECT properly when session cookie is invalid?
        #if user_row is None:
        #     return redirect(url_for('auth.login'))

        user_dict = user_row._asdict()

        g.user = (
            user_dict
        )

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        elif not g.user['admin']:
            return render_template('/page-404.html'), 404

        return view(**kwargs)

    return wrapped_view

RegisterError = Enum('RegisterError', ['UsernameNull', 'UsernameShort', 'UsernameLong', 'EmailNull', 'PasswordNull', 'PasswordShort', 'PasswordDiffer', 'InvalidInvitation', 'UsernameTaken', 'EmailTaken'])

error_message_dict = {
    RegisterError.UsernameShort : gettext('Chosen nickname is too short (min. 3 characters).'),
    RegisterError.UsernameLong : gettext('Chosen nickname is too long (max. 20 characters).'),
    RegisterError.EmailNull : gettext('E-mail address is required.'),
    RegisterError.PasswordShort : gettext('The given password is too short (min. 8 characters).'),
    RegisterError.PasswordDiffer : gettext('The two passwords are not identical.'),
    RegisterError.InvalidInvitation : gettext('The invitation key is not valid.'),
    RegisterError.UsernameTaken : gettext('The chosen nickname is already taken.'),
    RegisterError.EmailTaken : gettext('The chosen email address is already taken.')
}

@bp.route('/register', methods=('GET', 'POST'))
def register() -> str:
    utc_now : datetime = time_determiner.get_now_time_object()
    register_deadline : datetime = time_determiner.parse_datetime_string(configuration.deadline_times.register)    

    if utc_now > register_deadline:
        return render_template('/auth/register-fail.html')

    if g.user is not None:
        return redirect(url_for('home.homepage'))

    if request.method == 'POST':
        user_data = request.form.to_dict(flat=True)

        if user_data['language'] not in configuration.supported_languages:
            user_data['language'] = configuration.supported_languages[0]        

        db = get_db()
        error : RegisterError = None
        if not user_data['username'] or len(str(user_data['username'])) < 3:
            error = RegisterError.UsernameShort
        elif len(str(user_data['username'])) > 20:
            error = RegisterError.UsernameLong
        elif not user_data['email']:
            error = RegisterError.EmailNull
        elif not user_data['password'] or len(user_data['password']) < 8:
            error = RegisterError.PasswordShort
        elif user_data['password'] != user_data['password_repeat']:
            error = RegisterError.PasswordDiffer
        elif user_data['key'] != configuration.invitation_keys.user and user_data['key'] != configuration.invitation_keys.admin:
            error = RegisterError.InvalidInvitation
        else:
            query_string = text('SELECT * FROM bet_user WHERE username = :username')
            result = db.session.execute(query_string, {'username' : user_data['username'] })
            if result.fetchone() is not None:         
                error = RegisterError.UsernameTaken
            else:
                query_string = text('SELECT * FROM bet_user WHERE email = :email')
                result = db.session.execute(query_string, {'email' : user_data['email']})
                if result.fetchone() is not None:
                    error = RegisterError.EmailTaken

        if error is None:
            user_data['password'] = generate_password_hash(user_data['password'])
            user_data['admin'] = user_data['key'] == configuration.invitation_keys.admin
            # TODO CHECK AND ADD TIMEZONE!
            user_data['timezone'] = '-01:00'

            query_string = text("INSERT INTO bet_user (username, password, email, reminder, summary, language, admin, timezone) " 
                                "VALUES (:username, :password, :email, :reminder, :summary, :language, :admin, :timezone)")
            result = db.session.execute(query_string, user_data)
            db.session.commit()

            session.clear()
            session['username'] = user_data['username']

            # sending welcome email
            emails = []
            email_object = get_email_resource_by_tag('Welcome')
            subject = render_template_string(email_object[0])
            message_text = render_template_string(email_object[1], username=user_data['username'])
            emails.append(create_message(sender='me', to=user_data['email'], subject=subject, message_text=message_text, subtype='html'))
            send_messages(emails)

            # if first time sign in upload team data
            result = db.session.execute(text('SELECT * FROM bet_user'))

            if len(result.fetchall()) <= 1:
                return redirect(url_for('admin.upload_team_data'))

            return redirect(url_for('group.group_order'))

        flash(error_message_dict[error])

        return render_template('/auth/register.html', user_data = user_data)

    user_data = {
        'reminder' : '0',
        'summary' : '1',
        'language' : configuration.supported_languages[0]
    }

    # TODO: 
    if current_app.debug:
        user_data = {
            'username' : 'MPM',
            'email' : 'mpm@mpm.mpm',
            'password' : 'aaaaaaaa',
            'password_repeat' : 'aaaaaaaa',
            'key' : configuration.invitation_keys.admin,
            'reminder' : '0',
            'summary' : '1',        
            'language' : configuration.supported_languages[0]
        }   

    return render_template('/auth/register.html', user_data = user_data)


@bp.route('/login', methods=('GET', 'POST'))
def login() -> str:
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
            error = gettext('Invalid username!')
        elif not check_password_hash(user.password, password):
            error = gettext('Invalid password!')

        if error is not None:
            flash(error)
            return render_template('/auth/login.html', username_form=username)
        
        session.clear()
        session['username'] = user.username          

        return redirect(url_for('home.homepage'))

    return render_template('/auth/login.html')

@bp.route('/logout')
def logout() -> str:
    session.clear()
    return redirect(url_for('auth.login'))

@bp.route('/page-profile', methods=('GET', 'POST'))
@login_required
def page_profile() -> str:
    if request.method == 'POST':
        user_data = request.form.to_dict(flat=True)

        if user_data['language'] not in configuration.supported_languages:
            user_data['language'] = configuration.supported_languages[0]

        query_string = text('UPDATE bet_user SET reminder=:r, summary=:s, language=:l WHERE username=:u')
        get_db().session.execute(query_string, {'r' : user_data['reminder'], 's' : user_data['summary'], 'l' : user_data['language'], 'u' : g.user['username']})
        get_db().session.commit()

        g.user['language'] = user_data['language']

    query_string = text('SELECT username, email, reminder, summary, language FROM bet_user WHERE username=:username')
    result = get_db().session.execute(query_string, {'username' : g.user['username']})
    user_data = result.fetchone()

    return render_template('/auth/modify.html', user_data = user_data)