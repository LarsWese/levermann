import logging

from levermann_share_value import db
from levermann_share_value.database.models import Share, ShareType
from levermann_share_value.levermann import constants
from levermann_share_value.levermann.mapper import ShareDataMapper
from levermann_share_value.scraper import ScraperMgr as scraperMgr
from levermann_share_value.scraper import onvista

logger = logging.getLogger(__name__)
mapper = ShareDataMapper()


def get_all_shares() -> [{}]:
    result = []
    shares: [Share] = Share.query.all()
    for share in shares:
        share_values = share.share_values
        share_data = share.as_dict()
        calculated_values = mapper.calculate(share_values)
        share_data.update(calculated_values)
        get_onvista_url(share_data)
        result.append(share_data)

    return result


def get_share_by_isin(isin: str) -> Share:
    share: Share = Share.query.filter(Share.isin == isin).first()
    if share is None:
        share = Share(isin=isin)
    scraperMgr.scrape_share_data(share=share)
    db.session.add(share)
    db.session.commit()
    return share


def change_type(share_id: int, new_type: int) -> Share:
    share: Share = Share.query.get(share_id)
    share.share_type = ShareType(new_type)
    db.session.commit()
    return share


def get_onvista_url(share_data):
    share_data[constants.onvista_url] = f'{onvista.METRICS_URL}{share_data[constants.isin]}'


def load_all_shares():
    scraperMgr.load_all_fingreen_shares()
