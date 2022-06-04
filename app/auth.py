from flask import Blueprint
from flask import redirect
from flask import g
from flask import flash
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask import render_template_string

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import functools

from datetime import datetime
from dateutil import tz

from app.db import get_db
from app.configuration import user_invitation_key, admin_invitation_key
from app.configuration import register_deadline_time
from app.configuration import supported_languages

from app.gmail_handler import get_email_resource_by_tag
from app.gmail_handler import send_messages, create_message

bp = Blueprint('auth', __name__, '''url_prefix="/auth"''')

#https://docs.python.org/3/library/sqlite3.html

@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""

    #session.permanent = True
    #app.permanent_session_lifetime = timedelta(minutes=1)

    username = session.get('username')

    if username is None:
        g.user = None
    else:
        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM bet_user WHERE username = %s', (username,))

        g.user = (
            cursor.fetchone()
        )

def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

def admin_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not g.user['admin']:
            return render_template(g.user['language'] + '/page-404.html'), 404

        return view(**kwargs)

    return wrapped_view

@bp.route('/register', methods=('GET', 'POST'))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    utc_now = datetime.utcnow()
    utc_now = utc_now.replace(tzinfo=tz.gettz('UTC'))

    register_deadline = datetime.strptime(register_deadline_time, '%Y-%m-%d %H:%M')
    register_deadline = register_deadline.replace(tzinfo=tz.gettz('UTC'))

    if utc_now > register_deadline:
        return render_template(g.user['language'] + '/auth/register-fail.html')

    if g.user is not None:
        return redirect(url_for('home.homepage'))

    if request.method == 'POST':
        language = request.form.get('language')
        name = request.form.get('fullname')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        password_repeat = request.form.get('password_repeat')
        key = request.form.get('key')
        reminder = request.form.get('reminder')
        summary = request.form.get('summary')

        db = get_db()
        error = None
        if not username:
            error = 'username_null'
        elif len(str(username)) < 3:
            error = 'username_short'
        elif len(str(username)) > 20:
            error = 'username_long'
        elif not name:
            error = 'name_null'
        elif len(str(name)) < 3:
            error = 'name_short'
        elif not email:
            error = 'email_null'
        elif not password:
            error = 'password_null'
        elif len(str(password)) < 8:
            error = 'password_short'
        elif password != password_repeat:
            error = 'password_differ'
        elif key != user_invitation_key and key != admin_invitation_key:
            error = 'invalid_invitation'
        else:
            cursor = db.cursor()
            cursor.execute('SELECT name FROM bet_user WHERE username = %s', (username,))
            if cursor.fetchone() is not None:         
                error = 'username_taken'
            else:                
                cursor = db.cursor()
                cursor.execute('SELECT name FROM bet_user WHERE email = %s', (email,))
                if cursor.fetchone() is not None:
                    error = 'email_taken'

        if error is None:
            # the name is available, store it in the database and go to
            # the login page

            admin = False

            if key == admin_invitation_key:
                admin = True

            db.cursor().execute(
                'INSERT INTO bet_user (username, name, password, email, reminder, summary, language, admin) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (username, name, generate_password_hash(password), email, reminder, summary, language, admin),
            )

            db.commit()

            session.clear()
            session['username'] = username

            # sending welcome email
            emails = []
            email_object = get_email_resource_by_tag('Welcome', language)
            subject = render_template_string(email_object[0], )
            message_text = render_template_string(email_object[1], username=username)
            emails.append(create_message(sender='me', to=email, subject=subject, message_text=message_text, subtype='html'))
            send_messages(emails)

            # if first time sign in upload team data
            player_cursor = db.cursor()
            player_cursor.execute('SELECT * FROM bet_user')

            if len(player_cursor.fetchall()) <= 1:
                return redirect(url_for('admin.upload_team_data'))

            return redirect(url_for('group.group_order'))

        flash(error)

        return render_template(language + '/auth/register.html', language=language, username_form = name, username = username, email = email, password = password, password_repeat = password_repeat, key=key, reminder=int(reminder), summary=int(summary))

    return render_template(supported_languages[0] +'/auth/register.html', reminder=0, summary=1, language=supported_languages[0])


@bp.route('/login', methods=('GET', 'POST'))
def login():
    # Redirect to homepage if user is already signed in
    if g.user is not None:
        return redirect(url_for('home.homepage'))

    """Log in a registered user by adding the user id to the session."""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        cursor = db.cursor()
        cursor.execute('SELECT * FROM bet_user WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user is None:
            error = 'username_invalid'
        elif not check_password_hash(user['password'], password):
            error = 'password_invalid'

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session['username'] = user['username']
            return redirect(url_for('home.homepage'))

        flash(error)

        return render_template(supported_languages[0] + '/auth/login.html', username_form=username)

    return render_template(supported_languages[0] + '/auth/login.html')

@bp.route('/logout')
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for('auth.login'))

@bp.route('/page-profile', methods=('GET', 'POST'))
@login_required
def page_profile():
    if request.method == 'POST':
        reminder = request.form['reminder']
        summary = request.form['summary']
        get_db().cursor().execute('UPDATE bet_user SET reminder=%s, summary=%s WHERE username=%s', (reminder, summary, g.user['username']))
        get_db().commit()

    cursor = get_db().cursor()
    cursor.execute('SELECT username, name, email, reminder, summary FROM bet_user WHERE username=%s', (g.user['username'],))
    user_data = cursor.fetchone()

    return render_template(g.user['language'] + '/auth/modify.html', email=user_data['email'], name=user_data['name'], reminder=user_data['reminder'], summary=user_data['summary'])