from flask import Flask

from datetime import datetime, UTC
from dateutil import tz

def get_now_time_object() -> datetime:
    return datetime.now(UTC)

def get_now_time_string() -> str:
    return get_now_time_object().strftime('%Y-%m-%d %H:%M')

def get_now_time_string_with_seconds() -> str:
    return get_now_time_object().strftime('%Y-%m-%d %H:%M:%S')

def parse_datetime_string(datetime_string : str) -> datetime:
    return datetime.strptime(datetime_string, '%Y-%m-%d %H:%M').replace(tzinfo=tz.gettz('UTC'))

def parse_datetime_string_with_seconds(datetime_string : str) -> datetime:
    return datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz.gettz('UTC'))

def stringify_datetime_object(datetime_object : datetime) -> str:
    return datetime_object.strftime('%Y-%m-%d %H:%M')

def init_time_handler(app : Flask) -> None:
    if app.debug:
        debug_start_time = datetime.strptime(app.config['DEBUG_START_TIME'], '%Y-%m-%d %H:%M').replace(tzinfo=tz.gettz('UTC'))
        app_start_time = datetime.now(UTC)

        global get_now_time_object
        get_now_time_object = lambda : debug_start_time + (datetime.now(UTC) - app_start_time)
