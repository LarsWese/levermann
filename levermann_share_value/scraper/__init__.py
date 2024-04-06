from datetime import date

from dateutil import relativedelta

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari /537.36',
           'Accept': 'application/json',
           }

relative = relativedelta


def get_weekdays_m6_nearest_today_y1_y5(today: date = date.today()) -> [date, date, date, date]:
    y5 = nearest_previous_weekday_date(today + relative.relativedelta(years=-5))
    m6 = nearest_previous_weekday_date(today + relative.relativedelta(months=-6))
    y1 = nearest_previous_weekday_date(today + relative.relativedelta(years=-1))
    # I want the data not from today. Because stock market could be open
    nearest_weekday = nearest_previous_weekday_date(today + relative.relativedelta(days=-1))
    return m6, nearest_weekday, y1, y5


def get_end_of_last_3_month(today: date = date.today()) -> [date, date, date]:
    m1 = nearest_previous_weekday_date(today + relative.relativedelta(months=-1))
    m2 = nearest_previous_weekday_date(today + relative.relativedelta(months=-2))
    m3 = nearest_previous_weekday_date(today + relative.relativedelta(months=-3))
    return m1, m2, m3


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
