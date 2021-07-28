# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from app.db import get_db
from app.home_page import homepage
import os

# import Flask 
from flask import Flask

from flask   import render_template, request
from flask.helpers import make_response
from jinja2  import TemplateNotFound

def create_app(test_config = None):
    # Inject Flask magic
    app = Flask(__name__, instance_relative_config=True)

    # App Config - the minimal footprint
    #app.config['TESTING'   ] = True 
    #app.config['SECRET_KEY'] = 'S#perS3crEt_JamesBond' 

    # this is from the tutorial
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    print("__name__: " + __name__)
    print ("instance path: " + os.path.join(app.instance_path, "flaskr.sqlite"))

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

    from flask import session

    #Setting session timeout
    @app.before_request
    def before_request():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=15)

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

    from datetime import timedelta


    return app

# Import routing to render the pages
#from app import views
