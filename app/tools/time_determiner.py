from flask import Flask

from datetime import datetime
from dateutil import tz

debug_now_string = '2022-12-10 18:30'

def get_now_time_object() -> datetime:
    return datetime.utcnow().replace(tzinfo=tz.gettz('UTC'))

def get_now_time_string() -> str:
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M')

def get_now_time_string_with_seconds() -> str:
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

def get_now_time_object_debug() -> datetime:
    return datetime.strptime(debug_now_string, '%Y-%m-%d %H:%M').replace(tzinfo=tz.gettz('UTC'))

def parse_datetime_string(datetime_string : str) -> datetime:
    return datetime.strptime(datetime_string, '%Y-%m-%d %H:%M').replace(tzinfo=tz.gettz('UTC'))

def parse_datetime_string_with_seconds(datetime_string : str) -> datetime:
    return datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz.gettz('UTC'))

def stringify_datetime_object(datetime_object : datetime) -> str:
    return datetime_object.strftime('%Y-%m-%d %H:M%')

def init_time_calculator(app : Flask) -> None:
    global get_now_time_object
    global get_now_time_string
    global get_now_time_string_with_seconds

    if app.debug:
        get_now_time_object = get_now_time_object_debug
        get_now_time_string = lambda : debug_now_string
        get_now_time_string_with_seconds = lambda : debug_now_string + ':17'