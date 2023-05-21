import datetime
import logging
from datetime import datetime, date

from dateutil import relativedelta
from sqlalchemy.orm import Session

from levermann_share_value import db
from levermann_share_value.database.models import Share, ShareValue
from levermann_share_value.scraper.fingreen import fingreen
from levermann_share_value.scraper.onvista import onvista
from levermann_share_value.scraper.raw_data import RawData, BasicShare

logger = logging.getLogger(__name__)


def get_all_shares() -> [Share]:
    return Share.query.all()


def load_everything():
    load_all_shares_from_fingreen()
    load_ov_data_for_all_shares()


def get_share_by_isin(isin: str) -> Share:
    share: Share = Share.query.filter(Share.isin == isin).first()
    if share is None or not share.share_values.all():
        share = scrape_share_data(share=Share(isin=isin))
    return share


def scrape_share_data(share: Share) -> Share:
    """
    get the share with the given name
    :param share:
    :return:
    """
    logger.info(f'scrape share with isin {share.isin}')
    share_raw_data: {str: [RawData]} = onvista.scrape(share.isin, datetime.utcnow())
    if len(share_raw_data) <= 0:
        return share
    __map_share_data(share, share_raw_data['metadata'])
    db.session.commit()
    # get share details
    session = Session(db.engine)

    logger.info(f"Get metrics for {share.isin} shareId: {share.id}")
    if len(share.isin) > 0 and share is not None:
        share_values: [ShareValue] = []
        for ov_data in share_raw_data['metrics']:
            share_value: ShareValue = __map_to_share_value(share.id, ov_data)
            share_values.append(share_value)
        session.add_all(share_values)
        session.commit()
    return share


def load_all_shares_from_fingreen():
    fingreens: [BasicShare] = fingreen.get_shares()

    for bs in fingreens:
        share: Share = Share()
        share.isin = bs.isin
        share.name = bs.name
        share.short_description_de = bs.description
        share.gree = True
        db.session.add(share)
    db.session.commit()


def load_ov_data_for_all_shares():
    shares: [Share] = get_all_shares()
    for share in shares:
        if not share.wkn:
            # everything else already scraped
            scrape_share_data(share)


def __get_next_quarter(fiscal_year_end: date, now: date) -> date:
    """
    TODO - write Test
    :param fiscal_year_end:
    :param now:
    :return:
    """
    relative = relativedelta
    d: date = fiscal_year_end
    for m in range(12):
        d = d + relative.relativedelta(months=3)
        if d > now:
            return d


def __map_share_data(share: Share, share_meta_datas: [RawData], today: date = date.today()):
    """
    TODO - get the metadata which I get normally from fingreen
    :param today:
    :param share_meta_datas:
    :param share:
    :return:
    """
    for smd in share_meta_datas:
        if smd.name == 'isin':
            share.isin = smd.value
        elif smd.name == 'wkn':
            share.wkn = smd.value
        elif smd.name == 'symbol':
            share.symbol = smd.value
        elif smd.name == 'name':
            share.name = smd.value
        elif smd.name == 'detail_page':
            share.detail_page_ov = smd.value
        elif smd.name == 'logo':
            share.logo_url = smd.value
        elif smd.name == 'long_description_ov':
            share.long_description_de = smd.value
        elif smd.name == 'country':
            share.country = smd.value
        elif smd.name == 'website':
            share.website = smd.value
        elif smd.name == 'street':
            share.street = smd.value
        elif smd.name == 'city':
            share.city = smd.value
        elif smd.name == 'zip_code':
            share.zip_code = smd.value
        elif smd.name == 'sector':
            share.sector = smd.value
        elif smd.name == 'branch':
            share.branch = smd.value
        elif smd.name == 'last_fiscal_year':
            share.last_fiscal_year = date.fromisoformat(smd.value)

    share.next_quarter = __get_next_quarter(share.last_fiscal_year, today)


def __map_to_share_value(share_id: int, raw_data: RawData) -> ShareValue:
    """
    Maps raw data to share value to store the data
    :param share_id:
    :param raw_data:
    :return:
    """
    share_value: ShareValue = ShareValue()
    share_value.share_id = share_id
    share_value.name = raw_data.name
    share_value.value = raw_data.value
    share_value.fetch_date = raw_data.fetch_date
    share_value.related_date = raw_data.related_date
    return share_value


if __name__ == '__main__':
    next_quarter = __get_next_quarter(fiscal_year_end=date(2022, 1, 31), now=date.today())
    print(f'next quarter {next_quarter}')
