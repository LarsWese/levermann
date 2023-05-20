from datetime import date

from dateutil import relativedelta

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
headers = {'User-Agent': USER_AGENT}

relative = relativedelta


def get_weekdays_nearest_today_m6_y1_y5(today: date = date.today()) -> [date, date, date, date]:
    y5 = nearest_previous_weekday_date(today + relative.relativedelta(years=-5))
    m6 = nearest_previous_weekday_date(today + relative.relativedelta(months=-6))
    y1 = nearest_previous_weekday_date(today + relative.relativedelta(years=-1))
    # I want the data not from today. Because stock market could be open
    nearest_weekday = nearest_previous_weekday_date(today + relative.relativedelta(days=-1))
    return m6, nearest_weekday, y1, y5


def nearest_previous_weekday_date(d: date) -> date:
    new_date = d
    if new_date.weekday() == 5:
        new_date = new_date + relative.relativedelta(days=-1)
    if new_date.weekday() == 6:
        new_date = new_date + relative.relativedelta(days=-2)
    return new_date


def nearest_coming_weekday_date(d: date) -> date:
    new_date = d
    if new_date.weekday() == 5:
        new_date = new_date + relative.relativedelta(days=+2)
    if new_date.weekday() == 6:
        new_date = new_date + relative.relativedelta(days=+1)
    return new_date
