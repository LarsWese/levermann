import logging
from datetime import date

from levermann_share_value.database.models import Share, ShareValue
from levermann_share_value.levermann import constants
from levermann_share_value.scraper import ScraperMgr as scraperMgr
from levermann_share_value.scraper.onvista import METRICS_URL as onvista_metrics_url

logger = logging.getLogger(__name__)



def get_all_shares() -> [{}]:
    result = []
    shares: [Share] = Share.query.all()
    for share in shares:
        share_values = share.share_values
        share_data = share.as_dict()
        for sv in share_values:
            get_large_cap(share_data, sv)
        for sv in share_values:
            get_ebit_marge(share_data, sv)
            get_equity_ratio(share_data, sv)
            get_return_equity(share_data, sv)
            get_per(share_data, sv)
        calculate_per(share_data)
        get_onvista_url(share_data)
        result.append(share_data)

    return result

def get_onvista_url(share_data):
    share_data[constants.onvista_url] = f'{onvista_metrics_url}{share_data[constants.isin]}'
def calculate_per(share_data):
    pass


def get_per(share_data: {}, sv: ShareValue):
    year_now: int = date.today().year
    share_data[constants.price_earnings_ratio] = []
    if sv.name == constants.price_earnings_ratio:
        if year_now - 3 <= sv.related_date.year <= year_now + 1:
            share_data[constants.price_earnings_ratio].append({'year': str(sv.related_date.year),
                                                               'value': sv.value})


def get_share_by_isin(isin: str) -> Share:
    share: Share = Share.query.filter(Share.isin == isin).first()
    if share is None or not share.share_values.all():
        share = scraperMgr.scrape_share_data(share=Share(isin=isin))
    return share


def get_large_cap(share_data: {}, sv: ShareValue):
    if sv.name == constants.market_capitalization:
        share_data[constants.large_cap] = is_large_cap(float(sv.value))
        share_data[constants.market_capitalization] = float(sv.value)


def get_return_equity(share_data: {}, sv) -> {}:
    if sv.name == constants.return_equity and is_date_last_year(sv.related_date):
        share_data[constants.return_equity] = {}
        value = float(sv.value)
        share_data[constants.return_equity]['value'] = value
        if value > 20:
            share_data[constants.return_equity]['point'] = 1
        elif value < 10:
            share_data[constants.return_equity]['point'] = -1
        else:
            share_data[constants.return_equity]['point'] = 0


def get_ebit_marge(share_data: {}, sv: ShareValue):
    if sv.name == constants.ebit_margin and is_date_last_year(sv.related_date):
        share_data[constants.ebit_margin] = {}
        value = float(sv.value)
        share_data[constants.ebit_margin]['value'] = value
        if value > 20:
            share_data[constants.ebit_margin]['point'] = 1
        elif value < 10:
            share_data[constants.ebit_margin]['point'] = -1
        else:
            share_data[constants.ebit_margin]['point'] = 0


def get_equity_ratio(share_data, sv):
    if sv.name == constants.equity_ratio_in_percent and is_date_last_year(sv.related_date):
        share_data[constants.equity_ratio_in_percent] = {}
        value = float(sv.value)
        share_data[constants.equity_ratio_in_percent]['value'] = value
        if value > 25:
            share_data[constants.equity_ratio_in_percent]['point'] = 1
        elif value < 15:
            share_data[constants.equity_ratio_in_percent]['point'] = -1
        else:
            share_data[constants.equity_ratio_in_percent]['point'] = 0


def load_shares_from_fingreen():
    scraperMgr.load_all_shares_from_fingreen()


def is_large_cap(market_cap: float):
    return market_cap >= 5_000_000_000


def is_date_last_year(to_check: date):
    return (date.today().year - to_check.year) == 1
