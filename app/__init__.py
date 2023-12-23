import os

from app.configuration import load_configuration
configuration = load_configuration()

# import Flask 
from flask import Flask
from flask import render_template

from datetime import timedelta

from app import db
from app import scheduler
from app.tools import time_determiner

from flask_babel import Babel

UPLOAD_FOLDER = './app'
ALLOWED_EXTENSIONS = {'csv'}

# TODO: builtin default filter not working with zero values despite using true as second argument
def custom_default(value, text):
    if value is None:
        return text
    return value

def create_app(test_config = None):
    app = Flask(__name__, instance_relative_config=True)
    app.jinja_env.filters['default0'] = custom_default

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY=configuration.app_secret_key,
        # store the database in the instance folder
        #DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        SQLALCHEMY_DATABASE_URI='sqlite:///flaskr.sqlite',
        # file upload folder
        UPLOAD_FOLDER=UPLOAD_FOLDER,
        # extensions enabled for uploading
        ALLOWED_EXTENSIONS=ALLOWED_EXTENSIONS,
        CACHE_TYPE='SimpleCache',  # Flask-Caching related configs
        CACHE_DEFAULT_TIMEOUT=300
    )

    db.db.init_app(app)
    db.add_db_commands(app)

    time_determiner.init_time_calculator(app)

    babel = Babel(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    from flask import session

    #Setting session timeout
    @app.before_request
    def before_request():
        #if not request.is_secure:
        #    url = request.url.replace('http://', 'https://', 1)
        #    code = 301
        #    return redirect(url, code=code)

        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=configuration.session_timeout)

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

    @app.errorhandler(403)
    def page_not_found(e):
        return render_template('/error-handling/page-403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('/error-handling/page-404.html'), 404

    @app.errorhandler(500)
    def page_not_found(e):
        # note that we set the 500 status explicitly
        return render_template('/error-handling/page-500.html'), 500

    app.config.update(SCHEDULER_TIMEZONE = 'utc')
    scheduler.init_scheduler(app)

    @app.context_processor
    def set_jinja_global_variables():
        return dict()

    return app