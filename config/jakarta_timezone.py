import datetime
import pytz


jakarta_timezone = pytz.timezone('Asia/Jakarta')
current_datetime = datetime.datetime.now(jakarta_timezone)

def current_datetime_jakarta_tz () :
    formatted_time = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    datetime_obj = datetime.datetime.strptime(formatted_time, '%Y-%m-%d %H:%M:%S')
    return datetime_obj

def current_time_jakarta_tz ():
    return current_datetime.time().replace(microsecond=0)

def current_date_jakarta_tz () :
    return current_datetime.date()


jkt_current_datetime = current_datetime_jakarta_tz()
jkt_current_date = current_date_jakarta_tz()
jkt_current_time = current_time_jakarta_tz()

