import json
import logging
from datetime import date, datetime
from json import JSONDecodeError

import requests
from bs4 import BeautifulSoup
from dateutil import relativedelta

from levermann_share_value.scraper import headers
from levermann_share_value.scraper.raw_data import RawData
from levermann_share_value.scraper import get_weekdays_nearest_today_m6_y1_y5

BASE_URL = "https://onvista.de"

METRICS_URL = f"{BASE_URL}/aktien/kennzahlen/"

logger = logging.getLogger(__name__)


def get_be_weekly_data(data: list[RawData]) -> list[RawData]:
    """
    Only returns the data that looked at be weekly. That is
    4, 5, 13 price_earnings_ratio (=KGV = EPS) last 3, now, next year
    9, 10, 11 course_y1_ago, course_6m_ago, course_today
    :param data:
    :return:
    """
    biweekly_data: list[RawData] = []
    for d in data:
        if d.name == 'price_earnings_ratio' \
                or d.name == 'course_y1_ago' \
                or d.name == 'course_6m_ago' \
                or d.name == 'course_today':
            biweekly_data.append(d)
    return biweekly_data


def get_yearly_data(data: list[RawData]) -> list[RawData]:
    """
    Only return the data that is important after the fiscal year ends
    0 market_capitalization
    1 return_equity
    2 ebit_margin
    3 equity_ratio_in_percent 
    :param data: 
    :return: 
    """""
    yearly_data: list[RawData] = []
    for d in data:
        if d.name == 'equity_ratio_in_percent' \
                or d.name == 'ebit_margin' \
                or d.name == 'return_equity' \
                or d.name == 'market_capitalization':
            yearly_data.append(d)
    return yearly_data


def json_data(html_content):
    soup: BeautifulSoup = BeautifulSoup(html_content, "html.parser")
    data_json = soup.find('script', id='__NEXT_DATA__').text
    try:
        return json.loads(data_json)
    except JSONDecodeError as ex:
        logger.error(f"could not load data origin: {html_content}")
        logger.error(f"error: {ex.msg}")
        raise ex


class OnVista:

    def __init__(self):
        self.isin: str = ""
        self.id_notation: str = ""
        self.entity_value: str = ""
        self.now: datetime = datetime.utcnow()

    def scrape(self, isin: str, now: datetime) -> list[RawData]:
        self.isin = isin
        self.now = now

        metrics: list[RawData] = self.__get_metrics()

        for metric in metrics:
            if metric.name == "entity_value":
                self.entity_value = metric.value
            elif metric.name == "id_notation":
                self.id_notation = metric.value
        stock_price: list[RawData] = self.__get_stock_price()
        return metrics + stock_price

    def get_meta_data(self, isin_: str, now: datetime) -> list[RawData]:
        """
        metadata for the share
        isin
        now:
        :return: a list raw metadata to create the share from
        """
        result: list[RawData] = []
        self.isin = isin_
        self.now = now
        url = f'{BASE_URL}/aktien/unternehmensprofil/{self.isin}'
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        data = json_data(response.text)
        props_data_ = data['props']['pageProps']['data']
        try:
            snapshot_ = props_data_['snapshot']
            result.append(
                RawData(name="market_capitalization", value=snapshot_['stocksFigure']['marketCapCompany'], fetch_date=now))

            last_fiscal_year = snapshot_['stocksBalanceSheetList']['list'][-1]['periodeEnd']
            result.append(
                RawData(name="last_fiscal_year", value=last_fiscal_year,
                        fetch_date=now))
            instrument_ = snapshot_['instrument']
            result.append(RawData(name="isin", value=instrument_['isin'], fetch_date=now))
            result.append(RawData(name="wkn", value=instrument_['wkn'], fetch_date=now))
            result.append(RawData(name="symbol", value=instrument_['symbol'], fetch_date=now))
            result.append(RawData(name="name", value=instrument_['name'], fetch_date=now))
            result.append(RawData(name="detail_page", value=instrument_['urls']['WEBSITE'], fetch_date=now))

            company_ = props_data_['company']
            if hasattr(company_, 'companyLogo'):
                result.append(RawData(name="logo", value=company_['companyLogo']['photoUrl'], fetch_date=now))

            result.append(RawData(name="long_description_ov", value=company_['profile'][0]['value'], fetch_date=now))

            result.append(RawData(name="country", value=snapshot_['keywords']['isoCountry'], fetch_date=now))

            descriptor_ = company_['companyDescriptor']
            result.append(RawData(name="website", value=descriptor_['url'], fetch_date=now))

            contact_ = descriptor_['contact']
            result.append(RawData(name="street", value=f'{contact_["street"]} {contact_["streetnumber"]}', fetch_date=now))
            result.append(RawData(name="city", value=f'{contact_["city"]}', fetch_date=now))
            result.append(RawData(name="zip_code", value=f'{contact_["zipCode"]}', fetch_date=now))

            branch_ = snapshot_['company']['branch']
            result.append(RawData(name="sector", value=branch_['sector']['name'], fetch_date=now))
            result.append(RawData(name="branch", value=branch_['name'], fetch_date=now))
        except AttributeError as ae:
            logger.warning(f'{isin_} has not attribute', ae)
        except KeyError as ke:
            logger.warning(f'{isin_} has not key', ke)
        return result

    def __get_metrics(self) -> list[RawData]:
        url = METRICS_URL + self.isin.strip()
        logger.info(f"url for metrics {url}")
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        data = json_data(response.text)

        financial_list = data['props']['pageProps']['data']['figures']['stocksCnFinancialList']['list']
        fundamental_list = data['props']['pageProps']['data']['figures']['stocksCnFundamentalList']['list']
        snapshot = data['props']['pageProps']['data']['snapshot']
        instrument = snapshot['instrument']
        onvista_datas: list[RawData] = []
        for fin in financial_list:
            item_date = date(year=fin['idYear'], month=1, day=1)
            # 3 Eigenkapitalquote in % yearly
            if 'cnEquityRatio' in fin:
                onvista_datas.append(RawData(
                    name='equity_ratio_in_percent',
                    value=fin['cnEquityRatio'],
                    related_date=item_date,
                    fetch_date=self.now
                ))
            # 2 Ebit Margin yearly
            if 'cnEbitMa' in fin:
                onvista_datas.append(RawData(
                    name='ebit_margin',
                    value=fin['cnEbitMa'],
                    related_date=item_date,
                    fetch_date=self.now
                ))
            # 1 Eigenkapitalrendite (ROI) yearly
            if 'cnReturnEquity' in fin:
                onvista_datas.append(RawData(
                    name='return_equity',
                    value=fin['cnReturnEquity'],
                    related_date=item_date,
                    fetch_date=self.now
                ))

            # KGV (price-earnings ratio)
            # if 'cnPer' in fin:
            #     onvista_datas['price_earnings_ratio']=                RawData(share_
            #                 name='price_earnings_ratio',
            #                 value=fin['cnPer'],
            #                 year=item_date,
            #                 fetch_date=today
            #                 )
        for fun in fundamental_list:
            item_date = date(year=fun['idYear'], month=1, day=1)
            # 4, 5 KGV (price-earnings ratio) every two weeks
            if 'cnPer' in fun:
                onvista_datas.append(RawData(
                    name='price_earnings_ratio',
                    value=fun['cnPer'],
                    related_date=item_date,
                    fetch_date=self.now
                ))

        # symbol
        symbol = instrument["symbol"]
        onvista_datas.append(RawData(
            name='symbol',
            value=symbol,
            related_date=self.now.date(),
            fetch_date=self.now
        ))

        # entity value (some id)
        quote = snapshot["quote"]
        entity_value = quote["entityValue"]
        onvista_datas.append(RawData(
            name='entity_value',
            value=entity_value,
            related_date=self.now.date(),
            fetch_date=self.now
        ))
        # id_notation (some id)
        id_notation = quote["market"]["idNotation"]
        onvista_datas.append(RawData(
            name='id_notation',
            value=id_notation,
            related_date=self.now.date(),
            fetch_date=self.now
        ))

        # Market capitalization (Marktkapitalisierung) important for cap classification yearly
        # market_cap_instrument = snapshot["stocksFigure"]["marketCapCompany"]
        # onvista_datas.append(RawData(
        #     name='market_capitalization',
        #     value=market_cap_instrument,
        #     related_date=self.now.date(),
        #     fetch_date=self.now
        # ))
        if len(onvista_datas) < 8:
            logger.error(f"could not find everything for {self.isin}")
            # TODO - exception handling
        return onvista_datas

    def __get_stock_price(self) -> list[RawData]:
        today: date = self.now.date()
        m6, nearest_weekday, y1, y5 = get_weekdays_nearest_today_m6_y1_y5(today)
        last_year = nearest_weekday.replace(year=today.year - 1)
        url = f'https://api.onvista.de/api/v1/instruments/STOCK/{self.entity_value}' \
              f'/eod_history?idNotation={self.id_notation}&range=Y1&startDate={last_year.strftime("%Y-%m-%d")}'
        logger.info(f"url for stock prices {url}")
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        onvista_datas: list[RawData] = []
        data = json.loads(response.text)
        dates = data["datetimeLast"]

        for idx, day_timestamp in enumerate(dates):
            search_date = datetime.utcfromtimestamp(int(day_timestamp)).date()
            # 9 course today vs 6m every two weeks
            if m6 == search_date:
                onvista_datas.append(RawData(
                    name='course_m6_ago',
                    value=data["last"][idx],
                    related_date=search_date,
                    fetch_date=today
                ))
            # 10 course today vs 1y every two weeks
            elif y1 == search_date:
                onvista_datas.append(RawData(
                    name='course_y1_ago',
                    value=data["last"][idx],
                    related_date=search_date,
                    fetch_date=today
                ))
            # 9, 10, 11 course today every two weeks
            elif nearest_weekday == search_date:
                onvista_datas.append(RawData(
                    name='course_today',
                    value=data["last"][idx],
                    related_date=search_date,
                    fetch_date=today
                ))
        if len(onvista_datas) < 3:
            logger.error(f"could not find everything for {self.isin} {onvista_datas}")
            # TODO - exception handling
        return onvista_datas


if __name__ == '__main__':
    ov: OnVista = OnVista()

    # raw_data = ov.get_meta_data('DE000A0WMPJ6', datetime.utcnow()) # aixtron
    raw_data = ov.get_meta_data('DE000A3MQC70', datetime.utcnow())  # aixtron
    # raw_data = ov.get_meta_data('US79466L3024', datetime.utcnow()) # Salesforce
    # raw_data = ov.get_meta_data('US02079K3059', datetime.utcnow()) # alphabet
    for r in raw_data:
        print(r)
