import logging

from levermann_share_value.database.models import Share
from levermann_share_value.scraper import ScraperMgr as scraperMgr

logger = logging.getLogger(__name__)


def get_all_shares() -> [Share]:
    return Share.query.all()


def get_share_by_isin(isin: str) -> Share:
    share: Share = Share.query.filter(Share.isin == isin).first()
    if share is None or not share.share_values.all():
        share = scraperMgr.scrape_share_data(share=Share(isin=isin))
    return share


def load_shares_from_fingreen():
    scraperMgr.load_all_shares_from_fingreen()
