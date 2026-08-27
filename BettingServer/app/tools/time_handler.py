from flask import Flask

from datetime import datetime, UTC
import pytz
from dateutil import tz

def get_now_time_object() -> datetime:
    return datetime.now(UTC)

def get_now_time_string_with_seconds() -> str:
    return get_now_time_object().strftime('%Y-%m-%dT%H:%M:%SZ')

def parse_datetime_string(datetime_string : str, tzinfo=tz.gettz('UTC')) -> datetime:
    return datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tzinfo)

def stringify_datetime_object(datetime_object : datetime) -> str:
    return datetime_object.strftime('%Y-%m-%dT%H:%M:%SZ')

def init_time_handler(app : Flask) -> None:
    if app.debug:
        debug_start_time = datetime.strptime(app.config['DEBUG_START_TIME'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.gettz('UTC'))
        app_start_time = datetime.now(UTC)

        global get_now_time_object
        get_now_time_object = lambda : debug_start_time + (datetime.now(UTC) - app_start_time)
