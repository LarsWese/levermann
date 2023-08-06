import logging

from levermann_share_value.database.models import Share
from levermann_share_value.levermann import constants
from levermann_share_value.levermann.mapper import ShareDataMapper
from levermann_share_value.scraper import ScraperMgr as scraperMgr
from levermann_share_value.scraper import onvista

logger = logging.getLogger(__name__)


def get_all_shares() -> [{}]:
    result = []
    shares: [Share] = Share.query.all()
    for share in shares:
        share_values = share.share_values
        share_data = share.as_dict()
        mapper = ShareDataMapper(share_values)
        calculated_values = mapper.calculate()
        share_data.append(calculated_values)

    get_onvista_url(share_data)
    result.append(share_data)

    return result


def get_share_by_isin(isin: str) -> Share:
    share: Share = Share.query.filter(Share.isin == isin).first()
    if share is None or not share.share_values.all():
        share = scraperMgr.scrape_share_data(share=Share(isin=isin))
    return share


def get_onvista_url(share_data):
    share_data[constants.onvista_url] = f'{onvista.METRICS_URL}{share_data[constants.isin]}'


def load_shares_from_fingreen():
    scraperMgr.load_all_shares_from_fingreen()
