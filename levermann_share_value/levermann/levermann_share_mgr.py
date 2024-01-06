import logging

from levermann_share_value import db
from levermann_share_value.database.models import Share, ShareType
from levermann_share_value.levermann import constants
from levermann_share_value.levermann.mapper import ShareDataMapper
from levermann_share_value.scraper import ScraperMgr as scraperMgr
from levermann_share_value.scraper import onvista
from levermann_share_value.scraper.raw_data import BasicShare

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
    result = sorted(result, key=lambda s: s.get('total_points').get('point'), reverse=True)
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
    fingreen_shares: list[BasicShare] = scraperMgr.load_all_fingreen_shares()
    ecoreporter_shares: list[BasicShare] = scraperMgr.load_all_ecoreporter_shares()
    stored_shares: [Share] = Share.query.all()
    stored_shares_dict = []
    for s in stored_shares:
        stored_shares_dict.append(s.as_dict())

    scrape_share: [] = []
    for share in fingreen_shares + ecoreporter_shares:
        s = Share.query.filter(Share.isin == share.isin).first()
        if s is None:
            scrape_share.append(share)
    print(f'{len(scrape_share)} new shares found')
    load_share_details_from_onvista(scrape_share)


def load_share_details_from_onvista(shares: list[BasicShare]):
    batch = 0
    for bs in shares:
        share: Share = Share()
        share.isin = bs.isin
        share.name = bs.name
        share.short_description_de = bs.description
        share.green = True
        share.share_type = ShareType.None_Finance
        scraperMgr.scrape_share_data(share)
        db.session.add(share)
        if batch % 10 ==0:
            db.session.commit()
        batch += 1
    db.session.commit()
