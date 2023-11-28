from flask import current_app
from flask import g
from flask.cli import with_appcontext
import click

import psycopg2
from psycopg2.extras import RealDictCursor

from app.configuration import configuration

def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """

    if "db" not in g:
        g.db = psycopg2.connect(configuration.DATABASE_URL, sslmode='require', cursor_factory=RealDictCursor)

    return g.db

def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()
        print("close_db called!")

def init_db():
    """Clear existing data and create new tables."""
    db = get_db()

    with current_app.open_resource("schema.sql", 'rb') as f:
        cursor = db.cursor()
        cursor.execute(f.read().decode('utf-8'))
        db.commit()

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")

def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)