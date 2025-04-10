import os

from flask import Flask
from flask import render_template
from flask import g
from flask import request

import json
import logging

from app.tools import db_handler
from app.tools import scheduler_handler
from app.tools import time_handler
from app.tools import cache_handler
from app.notification import notification_handler
from app.config import Default

from flask_babel import Babel
from pathlib import Path

def create_app(instance_path = None):
    app = Flask(__name__, instance_relative_config=True) if instance_path is None else Flask(__name__, instance_relative_config=True, instance_path=instance_path)

    # create custom default filter for none object
    app.jinja_env.filters['d_none'] = lambda value, default_text : value if value is not None else default_text
    app.jinja_env.filters['d_round'] = lambda value, default_text, precision = 2 : round(value, precision) if value is not None and value != '' else default_text

    # load configuration from file
    app.config.from_object(Default())
    app.config.from_file('configuration.json', load=json.load, silent=True)
    app.config['CACHE_DIR'] = os.path.join(app.instance_path, 'cache')

    # ensure the instance folder exists
    try:
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(app.instance_path, app.config['UPLOAD_FOLDER'])).mkdir(parents=True, exist_ok=True)
    except OSError:
        app.logger.info('Error while creating app directories.')

    # configure logging
    info_handler = logging.FileHandler(os.path.join(app.instance_path, 'logfile_info.log'))
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(logging.Formatter('[%(levelname)s][%(asctime)s] %(message)s - (%(module)s/%(filename)s)'))

    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(info_handler)

    app.logger.info('Server startup.')

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
        return (lambda keys : request.accept_languages.best_match(keys) or list(keys)[0])(app.config['SUPPORTED_LANGUAGES'].keys())

    babel = Babel(app, locale_selector=get_locale)

    # apply the blueprints to the app
    from app import auth
    from app import group_bet
    from app import home_page
    from app import results
    from app import standings
    from app import admin    
    from app import match_bet
    from app import chat

    app.register_blueprint(auth.bp)
    app.register_blueprint(group_bet.bp)
    app.register_blueprint(home_page.bp)
    app.register_blueprint(results.bp)
    app.register_blueprint(standings.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(match_bet.bp)
    app.register_blueprint(chat.bp)

    from app.tools.score_calculator import init_calculator
    init_calculator(app)

    if app.config['DIRECT_MESSAGING'] == 2:
        from app.notification import push_methods
        app.register_blueprint(push_methods.bp)

    if cache_handler.cache.get('comment_nr') is None:
        cache_handler.cache.set('comment_nr', {}, timeout=0)

    @app.context_processor
    def inject_unseen_comment_nr():
        return dict(comment_nr=cache_handler.cache.get('comment_nr'))

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
