import datetime
import pytz
from calendar import timegm


def string_datetime_to_timestamp(string_datetime, format, local_tz):
    '''Transforms scraped date to timestamp (always UTC)'''
    naive_dt = datetime.datetime.strptime(string_datetime, format)
    local_dt = local_tz.localize(naive_dt, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    utc_timetuple = utc_dt.timetuple()
    return timegm(utc_timetuple)

def timestamp_to_month_date(timestamp, local_tz):
    naive_dt = datetime.datetime.fromtimestamp(timestamp)
    local_dt = local_tz.localize(naive_dt, is_dst=None)
    current_dt = datetime.datetime.now()
    current_local_dt = local_tz.localize(current_dt, is_dst=None)
    is_open = current_local_dt < local_dt
    return (is_open, local_dt.strftime("%b %d"))