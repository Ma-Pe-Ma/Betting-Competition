from flask import Flask

from datetime import datetime, UTC
import pytz
from dateutil import tz

def get_now_time_object() -> datetime:
    return datetime.now(UTC)

def get_now_time_string() -> str:
    return get_now_time_object().strftime('%Y-%m-%d %H:%M')

def get_now_time_string_with_seconds() -> str:
    return get_now_time_object().strftime('%Y-%m-%d %H:%M:%S')

def parse_datetime_string(datetime_string : str, tzinfo=tz.gettz('UTC')) -> datetime:
    return datetime.strptime(datetime_string, '%Y-%m-%d %H:%M').replace(tzinfo=tzinfo)

def parse_datetime_string_with_seconds(datetime_string : str, tzinfo=tz.gettz('UTC')) -> datetime:
    return datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tzinfo)

def stringify_datetime_object(datetime_object : datetime) -> str:
    return datetime_object.strftime('%Y-%m-%d %H:%M')

def local_date_time_from_utc(utc_datetime_string, timezone, format='%Y-%m-%d %H:%M', time_format='%H:%M'):
    if utc_datetime_string == '' or utc_datetime_string is None:
        return '', ''

    utc_datetime = datetime.strptime(utc_datetime_string, format)
    utc_datetime = pytz.utc.localize(utc_datetime)
    local_datetime = utc_datetime.astimezone(pytz.timezone(timezone))

    return local_datetime.strftime('%Y-%m-%d'), local_datetime.strftime(time_format)

def utc_date_time_from_local(local_datetime_string, timezone, format='%Y-%m-%d %H:%M', time_format='%H:%M'):
    if local_datetime_string == '' or local_datetime_string is None:
        return '', ''

    local_datetime = datetime.strptime(local_datetime_string, format)
    local_datetime = pytz.timezone(timezone).localize(local_datetime)
    utc_time = local_datetime.astimezone(pytz.utc)

    return utc_time.strftime('%Y-%m-%d'), utc_time.strftime(time_format),

def init_time_handler(app : Flask) -> None:
    if app.debug:
        debug_start_time = datetime.strptime(app.config['DEBUG_START_TIME'], '%Y-%m-%d %H:%M').replace(tzinfo=tz.gettz('UTC'))
        app_start_time = datetime.now(UTC)

        global get_now_time_object
        get_now_time_object = lambda : debug_start_time + (datetime.now(UTC) - app_start_time)
