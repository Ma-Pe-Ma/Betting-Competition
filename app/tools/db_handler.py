from flask import current_app
from flask.cli import with_appcontext
import click
import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

db : SQLAlchemy = None

def get_db() -> SQLAlchemy:
    return db

def init_db(app):
    global db 
    db = SQLAlchemy(app)
    app.cli.add_command(init_db_command)

    with app.app_context():
        import pytz
        import dateutil.parser

        def time_converter(datetime, tz, target_tz, format='%Y-%m-%d %H:%M'):
            if datetime is None or datetime == '':
                return None
            return pytz.timezone(tz).localize(dateutil.parser.parse(datetime)).astimezone(pytz.timezone(target_tz)).strftime(format)

        def register_custom_functions(conn, _):
            conn.create_function('time_converter', 4, time_converter)
            conn.create_function('time_converter', 3, time_converter)

        event.listen(db.engine, 'connect', register_custom_functions)        

@click.command('init-db')
@with_appcontext
def init_db_command():
    #script_dir = os.path.dirname(os.path.abspath(__file__))
    #schema_directory = os.path.join(script_dir, 'resources', 'db-schemas')

    with current_app.open_resource('./resources/schema.sql', 'rb') as f:
        database_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        
        if db.engine.dialect.name == 'sqlite':            
            database_file_path = os.path.join(current_app.instance_path, database_uri.replace('sqlite:///', ''))

            import sqlite3
            db_initer = sqlite3.connect(database_file_path, detect_types=sqlite3.PARSE_DECLTYPES)
            db_initer.row_factory = sqlite3.Row
            db_initer.executescript(f.read().decode('utf8'))

        elif db.engine.dialect.name == 'postgresql':
            database_uri = database_uri.replace('postgres//', '')

            import psycopg2
            from psycopg2.extras import RealDictCursor

            db_initer = psycopg2.connect(database_uri, sslmode='require', cursor_factory=RealDictCursor)

            cursor = db_initer.cursor()
            cursor.execute(f.read().decode('utf-8'))
            db_initer.commit()

        # TODO 
        elif db.engine.dialect.name == 'mysql':
            pass

    click.echo("Initialized the database.")