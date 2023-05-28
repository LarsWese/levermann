import datetime
import logging

import requests

from levermann_share_value.levermann import constants
from levermann_share_value.scraper import headers
from levermann_share_value.scraper.onvista import BASE_URL, json_data
from levermann_share_value.scraper.raw_data import RawData

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
        country = country_list['indicesDetails']['isoCountry']
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
    return result


if __name__ == '__main__':
    print(index())
