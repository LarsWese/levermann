import json
import logging
from datetime import date, datetime

import requests

from levermann_share_value.levermann import constants
from levermann_share_value.levermann.exceptions import ShareNotExist, MarketCapitalizationNotFound
from levermann_share_value.scraper import get_weekdays_m6_nearest_today_y1_y5, get_end_of_last_3_month
from levermann_share_value.scraper import headers
from levermann_share_value.scraper.onvista import analyzer_recommendation_url, \
    snapshot_url, company_url, timeout
from levermann_share_value.scraper.raw_data import RawData

logger = logging.getLogger(__name__)


def scrape(isin: str, now: datetime) -> list[RawData]:
    entity_value = ""
    id_notation = ""

    logger.info(f"Scraping {isin}")
    metrics: [RawData] = __get_metrics(now, isin)

    for metric in metrics:
        if metric.name == "entity_value":
            entity_value = metric.value
        elif metric.name == "id_notation":
            id_notation = metric.value
    metadata: [RawData] = __get_meta_data(entity_value, now)
    stock_price: [RawData] = __get_stock_price(now, id_notation, entity_value, isin)
    analyzer_recommendations: [RawData] = __get_analyzer_recommendation(entity_value, now)

    return metadata + metrics + stock_price + analyzer_recommendations


def __get_analyzer_recommendation(entity_value: str, now: datetime) -> [RawData]:
    result: [RawData] = []
    # response = requests.get(analyzer_recommendation_url(entity_value), headers=headers, timeout=timeout)
    response = requests.get(analyzer_recommendation_url(entity_value), headers=headers)
    response.encoding = 'utf-8'
    try:
        data = json.loads(response.text)
        if 'numBuy' in data:
            result.append(RawData(name=constants.numBuy, value=data['numBuy'], fetch_date=now, related_date=now))
        if 'numHold' in data:
            result.append(RawData(name=constants.numHold, value=data['numHold'], fetch_date=now, related_date=now))
        if 'numSell' in data:
            result.append(RawData(name=constants.numSell, value=data['numSell'], fetch_date=now, related_date=now))
        if 'numTotal' in data:
            result.append(RawData(name=constants.numTotal, value=data['numTotal'], fetch_date=now, related_date=now))
    except AttributeError:
        raise ShareNotExist(entity_value)
    return result


def __get_meta_data(entity_value: str, now: datetime) -> [RawData]:
    """
    metadata for the share
    isin
    now:
    :return: a list raw metadata to create the share from
    """
    result: [RawData] = []
    # response = requests.get(company_url(entity_value), headers=headers, timeout=timeout)
    response = requests.get(company_url(entity_value), headers=headers)
    response.encoding = 'utf-8'
    data = json.loads(response.text)
    if 'companyLogo' in data:
        result.append(RawData(name=constants.logo, value=data['companyLogo']['photoUrl'], fetch_date=now))

    if 'profile' in data:
        result.append(
            RawData(name=constants.long_description_ov, value=data['profile'][0]['value'], fetch_date=now))

    if 'companyDescriptor' in data:
        descriptor_ = data['companyDescriptor']
        if 'yearLastBalance' in descriptor_:
            result.append(RawData(name=constants.last_balance_year, value=descriptor_['yearLastBalance'], fetch_date=now,
                                  related_date=now))
        if 'yearEndFiscal' in descriptor_:
            result.append(RawData(name=constants.coming_fiscal_year, value=descriptor_['yearEndFiscal'], fetch_date=now,
                                  related_date=now))
        if 'url' in descriptor_:
            result.append(RawData(name=constants.website, value=descriptor_['url'], fetch_date=now))

        contact_ = descriptor_['contact']
        result.append(
            RawData(name=constants.street, value=f'{contact_["street"]} {contact_["streetnumber"]}', fetch_date=now))
        result.append(RawData(name=constants.city, value=f'{contact_["city"]}', fetch_date=now))
        result.append(RawData(name=constants.zip_code, value=f'{contact_["zipCode"]}', fetch_date=now))

        if 'branch' in descriptor_['company']:
            branch_ = descriptor_['company']['branch']
            result.append(RawData(name=constants.sector, value=branch_['sector']['name'], fetch_date=now))
            result.append(RawData(name=constants.branch, value=branch_['name'], fetch_date=now))
    return result

# try:
#     import http.client as http_client
# except ImportError:
#     # Python 2
#     import httplib as http_client
# http_client.HTTPConnection.debuglevel = 1
#
# # You must initialize logging, otherwise you'll not see debug output.
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

def __get_metrics(today: datetime, isin_: str) -> [RawData]:
    logger.debug(f'{snapshot_url(isin_)}')
    # response = requests.get(snapshot_url(isin_), headers=headers, timeout=timeout)
    response = requests.get(snapshot_url(isin_), headers=headers)
    response.encoding = 'utf-8'
    logger.debug(f'get metrics {response.text}')
    data = json.loads(response.text)
    if 'stocksFigure' not in data:
        raise MarketCapitalizationNotFound(isin_)
    stocks_figure = data['stocksFigure']
    if 'marketCapCompany' not in stocks_figure:
        raise MarketCapitalizationNotFound(isin_)
    onvista_datas: [RawData] = [
        RawData(name=constants.market_capitalization, value=stocks_figure['marketCapCompany'],
                fetch_date=today, related_date=today.date())]
    if 'company' in data:
        onvista_datas.append(RawData(name=constants.country, value=data['company']['isoCountry'], fetch_date=today))

    instrument = data['instrument']
    onvista_datas.append(RawData(name=constants.isin, value=instrument['isin'], fetch_date=today))
    onvista_datas.append(RawData(name=constants.wkn, value=instrument['wkn'], fetch_date=today))
    onvista_datas.append(RawData(name=constants.symbol, value=instrument['symbol'], fetch_date=today))
    onvista_datas.append(RawData(name=constants.name, value=instrument['name'], fetch_date=today))

    quote = data['quote']
    onvista_datas.append(RawData(name=constants.market, value=quote['market']['name'], fetch_date=today))

    financial_list = data['stocksCnFinancialList']['list']
    for fin in financial_list:
        item_label = fin['label']
        item_date = date(year=fin['idYear'], month=1, day=1)
        # 3 Eigenkapitalquote in % yearly
        if 'cnEquityRatio' in fin:
            onvista_datas.append(RawData(
                name=constants.equity_ratio_in_percent,
                value=fin['cnEquityRatio'],
                related_date=item_date,
                fetch_date=today,
                note=item_label
            ))
        # 2 Ebit Margin yearly
        if 'cnEbitMa' in fin:
            onvista_datas.append(RawData(
                name=constants.ebit_margin,
                value=fin['cnEbitMa'],
                related_date=item_date,
                fetch_date=today,
                note=item_label
            ))
        # 1 Eigenkapitalrendite (ROI) yearly
        if 'cnReturnEquity' in fin:
            onvista_datas.append(RawData(
                name=constants.return_equity,
                value=fin['cnReturnEquity'],
                related_date=item_date,
                fetch_date=today,
                note=item_label
            ))
        # 4, 5, 13 KGV (earnings_per_share ratio), earnings revision
        if 'cnEpsAdj' in fin:
            onvista_datas.append(RawData(
                name=constants.earnings_per_share,
                value=fin['cnEpsAdj'],
                related_date=item_date,
                fetch_date=today,
                note=item_label
            ))

    fundamental_list = data['stocksCnFundamentalList']['list']
    for fun in fundamental_list:
        item_label = fun['label']
        item_date = date(year=fun['idYear'], month=1, day=1)
        if 'cnPer' in fun:
            onvista_datas.append(RawData(
                name=constants.price_earnings_ratio,
                value=fun['cnPer'],
                related_date=item_date,
                fetch_date=today,
                note=item_label
            ))

    # entity value (some id)
    entity_value = instrument["entityValue"]
    onvista_datas.append(RawData(
        name=constants.entity_value,
        value=entity_value,
        # to get sure this will be loaded only ones
        related_date=date(1970, 1, 1),
        fetch_date=today
    ))
    # id_notation (some id)
    id_notation = stocks_figure["idNotation"]
    onvista_datas.append(RawData(
        name=constants.id_notation,
        value=id_notation,
        # to get sure this will be loaded only ones
        related_date=date(1970, 1, 1),
        fetch_date=today
    ))

    return onvista_datas


def __get_stock_price(today: datetime, id_notation: str, entity_value: str, isin: str) -> [RawData]:
    m6, nearest_weekday, y1, y5 = get_weekdays_m6_nearest_today_y1_y5(today.date())
    m1, m2, m3 = get_end_of_last_3_month(today.date())
    url = f'https://api.onvista.de/api/v1/instruments/STOCK/{entity_value}' \
          f'/eod_history?idNotation={id_notation}&range=Y1&startDate={y1.strftime("%Y-%m-%d")}'
    logger.debug(f"url for stock prices {url}")
    # response = requests.get(url, headers=headers, timeout=timeout)
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    data = json.loads(response.text)

    onvista_datas: [RawData] = []
    dates = data["datetimeLast"]

    for idx, timestamp in enumerate(dates):
        data['datetimeLast'][idx] = datetime.utcfromtimestamp(int(timestamp)).date()

    for idx, day_ in enumerate(dates):
        # 9 course today vs 6m every two weeks
        if m6 == day_:
            onvista_datas.append(RawData(
                name=constants.share_price_m6_ago,
                value=data["last"][idx],
                related_date=day_,
                fetch_date=today
            ))
        # 10 course today vs 1y every two weeks
        elif y1 == day_:
            onvista_datas.append(RawData(
                name=constants.share_price_y1_ago,
                value=data["last"][idx],
                related_date=day_,
                fetch_date=today
            ))
        # 9, 10, 11 course today every two weeks
        elif nearest_weekday == day_:
            onvista_datas.append(RawData(
                name=constants.share_price_today,
                value=data["last"][idx],
                related_date=day_,
                fetch_date=today
            ))
        # 12 three-month reversal
        elif m1 == day_:
            onvista_datas.append(RawData(
                name=constants.share_price_m1_ago,
                value=data["last"][idx],
                related_date=day_,
                fetch_date=today
            ))
        elif m2 == day_:
            onvista_datas.append(RawData(
                name=constants.share_price_m2_ago,
                value=data["last"][idx],
                related_date=day_,
                fetch_date=today
            ))
        elif m3 == day_:
            onvista_datas.append(RawData(
                name=constants.share_price_m3_ago,
                value=data["last"][idx],
                related_date=day_,
                fetch_date=today
            ))

    if len(onvista_datas) < 3:
        logger.warning(f"could not find all stock prices for {isin} {onvista_datas}")
    return onvista_datas


if __name__ == '__main__':
    # __get_meta_data('DE000A0WMPJ6', datetime.utcnow())
    # __get_metrics(datetime.utcnow(), 'DE000A0WMPJ6')
    s = scrape("DE000A2NB601", datetime.utcnow())
    print(s)
    # print(__get_stock_price(datetime.utcnow(), '24865177', '21058705', 'US79466L3024'))
