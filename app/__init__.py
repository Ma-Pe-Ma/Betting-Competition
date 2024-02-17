import os

from flask import Flask
from flask import render_template
from flask import session
from flask import g
from flask import request

from datetime import timedelta
import json

from app.tools import db_handler
from app.tools import scheduler_handler
from app.tools import time_handler
from app.tools import cache_handler
from app.notification import notification_handler

from flask_babel import Babel

def create_app(test_config = None):
    app = Flask(__name__, instance_relative_config=True)
    # create custom default filter for none object
    app.jinja_env.filters['d_none'] = lambda value, default_text : value if value is not None else default_text

    # load configuration from file
    app.config.from_object('app.config.Default')
    app.config.from_file("config.json", load=json.load, silent=True)

    # ensure the instance folder exists
    try:
        from pathlib import Path
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(app.instance_path, app.config['UPLOAD_FOLDER'])).mkdir(parents=True, exist_ok=True)
    except OSError:
        print('Error while creating app directories.')

    # setup various tools
    db_handler.init_db(app)
    cache_handler.init_cache(app)
    time_handler.init_time_handler(app)
    scheduler_handler.init_scheduler(app)
    notification_handler.init_notifier(app)    

    def get_locale():
        # if a user is signed in, use the locale from the user settings
        user = getattr(g, 'user', None)
        if user is not None:
            return user['language']
        return request.accept_languages.best_match(app.config['SUPPORTED_LANGUAGES'].keys())

    babel = Babel(app, locale_selector=get_locale)

    # apply the blueprints to the app
    from app import auth
    from app import group_bet
    from app import home_page
    from app import previous_bets
    from app import standings
    from app import admin    
    from app import match_bet
    from app import chat

    app.register_blueprint(auth.bp)
    app.register_blueprint(group_bet.bp)
    app.register_blueprint(home_page.bp)
    app.register_blueprint(previous_bets.bp)
    app.register_blueprint(standings.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(match_bet.bp)
    app.register_blueprint(chat.bp)

    if app.config['DIRECT_MESSAGING'] == 2:
        from app.notification import push_methods
        app.register_blueprint(push_methods.bp)

    # setting session timeout TODO: check flask-login capabilities
    @app.before_request
    def before_request():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=app.config['SESSION_TIMEOUT'])

    @app.errorhandler(403)
    def page_403(e):
        return render_template('/error-handling/page-403.html'), 403

    @app.errorhandler(404)
    def page_404(e):
        return render_template('/error-handling/page-404.html'), 404

    @app.errorhandler(500)
    def page_500(e):
        return render_template('/error-handling/page-500.html'), 500

    return app