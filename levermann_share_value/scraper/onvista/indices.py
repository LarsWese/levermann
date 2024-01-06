import datetime
import json
import logging
from datetime import datetime, date

import requests

from levermann import constants
from scraper import headers, get_end_of_last_3_month
from scraper.onvista import BASE_URL, json_data
from scraper.raw_data import RawData

logger = logging.getLogger(__name__)

index_url = BASE_URL + '/index'


def index() -> {str: [RawData]}:
    result: {str: [RawData]} = {}
    utcnow = datetime.datetime.utcnow()

    response = requests.get(index_url, headers=headers)
    response.encoding = 'utf-8'
    data_ = json_data(response.text, logger)
    # logger.info(data_)
    list_ = data_['props']['pageProps']['lists']
    for li in list_:
        if not (li['type'] == "WORLD") and not (li['type'] == "MSCI") and not (li['type'] == "CHART"):
            raw_data: {str: [RawData]} = __index_data(li['list'], utcnow)
            result = result | raw_data
    return result


def performance_m3(index_id: str):
    # index_id == entity_value
    start_date = datetime.utcnow()
    m1, m2, m3 = get_end_of_last_3_month(start_date.date())
    url = f'https://api.onvista.de/api/v1/instruments/INDEX/{index_id}/eod_history?idNotation={index_id}' \
          f'&range=Y1&startDate={m3}'
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    data_ = json.loads(response.text)
    index_performance: [RawData] = []

    dates = data_["datetimeLast"]

    for idx, day_timestamp in enumerate(dates):
        data_['datetimeLast'][idx] = datetime.utcfromtimestamp(int(day_timestamp)).date()

    for idx, day_ in enumerate(dates):
        # 9 course today vs 6m every two weeks
        if m1 == day_:
            index_performance.append(RawData(
                name=constants.course_m1_ago,
                value=data_["last"][idx],
                related_date=day_,
                fetch_date=start_date
            ))
        elif m2 == day_:
            index_performance.append(RawData(
                name=constants.course_m2_ago,
                value=data_["last"][idx],
                related_date=day_,
                fetch_date=start_date
            ))
        elif m3 == day_:
            index_performance.append(RawData(
                name=constants.course_m3_ago,
                value=data_["last"][idx],
                related_date=day_,
                fetch_date=start_date
            ))
    return index_performance


def __index_data(index_list: {}, utcnow: datetime) -> {str: [RawData]}:
    result: {str: [RawData]} = {}
    for country_list in index_list:

        instr = country_list['instrument']
        url = instr['urls']['WEBSITE']
        name = instr['name']
        symbol = None
        isin = None
        wkn = None
        try:
            wkn = instr['wkn']
            isin = instr['isin']
            symbol = instr['symbol']
        except KeyError as ke:
            logger.warning(f'could not find something for {name}')
        details = country_list['indicesDetails']
        country = details['isoCountry']
        if details['nameSecuritySubType'] == 'Aktienindex':
            raw_data = [RawData(name=constants.name, value=name, fetch_date=utcnow),
                        RawData(name=constants.url, value=url, fetch_date=utcnow),
                        RawData(name=constants.country, value=country, fetch_date=utcnow)
                        ]
            if symbol:
                raw_data.append(RawData(name=constants.symbol, value=symbol, fetch_date=utcnow))
            if isin:
                raw_data.append(RawData(name=constants.isin, value=isin, fetch_date=utcnow))
            if wkn:
                raw_data.append(RawData(name=constants.isin, value=wkn, fetch_date=utcnow))

            result[name] = raw_data
            logger.debug(raw_data)
        else:
            logger.debug(f'{name} is not shareindex')
    return result


def __index_details(url: str):
    utcnow = datetime.datetime.utcnow()

    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    data_ = json_data(response.text, logger)
    print(data_)


if __name__ == '__main__':
    # print(__index_details('https://www.onvista.de/index/DAX-Index-20735'))
    print(performance_m3('20735'))