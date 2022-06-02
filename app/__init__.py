import os

# import Flask 
from flask import Flask

from flask import render_template, request, redirect
from flask.helpers import make_response
from jinja2  import TemplateNotFound

from datetime import timedelta

#from multiprocessing import Process, Value
#from app import scheduler
from app.scheduler import init_scheduler
from app.database_manager import init_db_with_data_command

from app.configuration import app_secret_key, session_timeout

UPLOAD_FOLDER = './app'
ALLOWED_EXTENSIONS = {'csv'}

def create_app(test_config = None):
    # Inject Flask magic
    app = Flask(__name__, instance_relative_config=True)

    # this is from the tutorial
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY=app_secret_key,
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
        # file upload folder
        UPLOAD_FOLDER=UPLOAD_FOLDER,
        # extensions enabled for uploading
        ALLOWED_EXTENSIONS=ALLOWED_EXTENSIONS
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # register the database commands
    from app import db

    db.init_app(app)
    app.cli.add_command(init_db_with_data_command)

    from flask import session

    #Setting session timeout
    @app.before_request
    def before_request():
        if not request.is_secure:
            url = request.url.replace('http://', 'https://', 1)
            code = 301
            return redirect(url, code=code)

        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=session_timeout)

    # apply the blueprints to the app
    from app import auth
    from app import group_bet
    from app import home_page
    from app import previous_bets
    from app import standings
    from app import admin    
    from app import match_bet

    app.register_blueprint(auth.bp)
    app.register_blueprint(group_bet.bp)
    app.register_blueprint(home_page.bp)
    app.register_blueprint(previous_bets.bp)
    app.register_blueprint(standings.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(match_bet.bp)

    @app.errorhandler(404)
    def page_not_found(e):
        # note that we set the 404 status explicitly
        return render_template('page-404.html'), 404

    app.config.update(SCHEDULER_TIMEZONE = "utc")

    #download_data_csv()
    init_scheduler(app)

    return app

app = create_app()

# Import routing to render the pages
#from app import views