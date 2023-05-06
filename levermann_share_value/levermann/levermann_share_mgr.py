import datetime
import logging
from datetime import datetime, date

from dateutil import relativedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session

from levermann_share_value.database.models import Share, ShareValue
from levermann_share_value.scraper.fingreen import fingreen
from levermann_share_value.scraper.onvista.onvista import OnVista
from levermann_share_value.scraper.raw_data import RawData, BasicShare

logger = logging.getLogger(__name__)


def map_to_share_value(share_id: int, raw_data: RawData) -> ShareValue:
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


def get_all_shares() -> list[Share]:
    return Share.query.all()


def map_share_data(share: Share, share_meta_datas: list[RawData], today: date = date.today()):
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

    share.next_quarter = get_next_quarter(share.last_fiscal_year, today)


class LevermannShareMgr:

    def __init__(self, db: SQLAlchemy):
        self.db = db
        self.ov = OnVista()
        self.fingreen = fingreen

    def load_everything(self):
        self.load_all_shares_from_fingreen()
        self.load_ov_data_for_all_shares()

    def load_all_shares_from_fingreen(self):
        fingreens: list[BasicShare] = self.fingreen.get_shares()

        for bs in fingreens:
            share: Share = Share()
            share.isin = bs.isin
            share.name = bs.name
            share.short_description_de = bs.description
            share.gree = True
            self.db.session.add(share)
        self.db.session.commit()

    def load_ov_data_for_all_shares(self):
        shares: list[Share] = get_all_shares()
        for share in shares:
            if not share.wkn:
                # everything else already scraped
                self.scrape_share_by(share)

    def scrape_share_by(self, share: Share):
        """
        get the share with the given name
        :param share:
        :return:
        """
        logger.info(f'scrape share with isin {share.isin}')
        share_meta_datas: list[RawData] = self.ov.get_meta_data(share.isin, datetime.utcnow())
        if len(share_meta_datas) <= 0:
            return
        map_share_data(share, share_meta_datas)
        self.db.session.commit()
        # get share details
        session = Session(self.db.engine)
        # TODO - market capitalization!
        # rawdata market_capitalization

        logger.info(f"Get metrics for {share.isin} shareId: {share.id}")
        if len(share.isin) > 0 and share is not None:
            share_values: list[ShareValue] = self.__scrape_share_data(share)
            session.add_all(share_values)
            session.commit()

    def __scrape_share_data(self, share: Share) -> list[ShareValue]:
        """
        get the data which is necessary for levermann calculation
        :param share: share to get the data for
        :return: list of share data
        """
        ov_raw_data: list[RawData] = self.ov.scrape(share.isin, datetime.utcnow())
        share_values: list[ShareValue] = []
        for ov_data in ov_raw_data:
            share_value: ShareValue = map_to_share_value(share.id, ov_data)
            share_values.append(share_value)
        return share_values


def get_next_quarter(fiscal_year_end: date, now: date) -> date:
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


if __name__ == '__main__':
    next_quarter = get_next_quarter(fiscal_year_end=date(2022, 1, 31), now=date.today())
    print(f'next quarter {next_quarter}')
