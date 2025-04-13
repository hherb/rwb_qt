from datetime import datetime
date = '2025-04-13'
year, month, day = map(int, date.split('-'))
given_date = datetime(year, month, day)
def get_weekday(given_date):
    return given_date.strftime('%A')
weekday = get_weekday(given_date)