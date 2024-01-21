from flask import current_app
from flask import g
from flask import Flask
from flask.cli import with_appcontext
import click

from flask_sqlalchemy import SQLAlchemy

db : SQLAlchemy = None

def get_db() -> SQLAlchemy:
    return db

def init_db(app):
    global db 
    db = SQLAlchemy(app)
    add_db_commands(app)

def add_db_commands(app):
    app.cli.add_command(init_db_command)

@click.command('init-db')
@with_appcontext
def init_db_command():
    with current_app.open_resource('./resources/schema.sql', 'rb') as f:
        database_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        
        if db.engine.dialect.name == 'sqlite':            
            database_file_path = './instance/{path}'.format(path=database_uri.replace('sqlite:///', ''))

            import sqlite3
            db_initer = sqlite3.connect(database_file_path, detect_types=sqlite3.PARSE_DECLTYPES)
            db_initer.row_factory = sqlite3.Row
            db_initer.executescript(f.read().decode("utf8"))

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