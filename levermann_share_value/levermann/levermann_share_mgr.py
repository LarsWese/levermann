import datetime
import logging
from datetime import datetime, date
from sqlalchemy.orm import Session
from flask_sqlalchemy import SQLAlchemy

from levermann_share_value.database.models import Share, ShareValue
from levermann_share_value.scraper.onvista.onvista import OnVista
from levermann_share_value.scraper.onvista.onvista import RawData

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


class LevermannShareMgr:

    def __init__(self, db: SQLAlchemy):
        self.db = db
        self.ov = OnVista()

    def scrape_share_by(self, isin: str = "", wkn: str = "", symbol: str = ""):
        """
        get the share with the given name
        :param isin:
        :param wkn:
        :param symbol:
        :return:
        """
        session = Session(self.db.engine)
        logger.info(f'scrape share with isin {isin}')
        share = Share.query.filter_by(isin=isin).first()
        if share is None:
            share: Share = self.get_share_meta_data(isin)
            session.add(share)
            session.commit()
        logger.info(f"Get metrics for {isin} shareId: {share.id}")
        if len(isin) > 0 and share is not None:
            share_values: list[ShareValue] = self.__scrape_share_data(share)
            session.add_all(share_values)
            session.commit()

    def get_all_shares(self) -> list[Share]:
        return Share.query.all()

    def get_share_meta_data(self, isin: str) -> Share:
        """
        TODO - get the metadata which I get normally from fingreen
        :param isin:
        :return:
        """
        share_meta_datas: list[RawData] = self.ov.get_meta_data(isin, datetime.utcnow())
        share: Share = Share()
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
                share.long_description_ov = smd.value
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
            elif smd.name == 'fiscal_year_end':
                share.fiscal_year_end = date.fromisoformat(smd.value)

        return share

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
