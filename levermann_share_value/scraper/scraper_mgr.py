import logging
from datetime import datetime

from levermann_share_value import scheduler

from levermann_share_value import db
from levermann_share_value.database.models import Share, ShareType, ShareValue
from levermann_share_value.levermann import constants
from levermann_share_value.levermann.exceptions import MarketCapitalizationNotFound
from levermann_share_value.levermann.mapper import ShareDataMapper
from levermann_share_value.scraper.ecoreporter import ecoreporter
from levermann_share_value.scraper.fingreen import fingreen
from levermann_share_value.scraper.onvista import METRICS_URL, onvista
from levermann_share_value.scraper.raw_data import BasicShare
from levermann_share_value.scraper.raw_data import RawData

logger = logging.getLogger(__name__)
mapper = ShareDataMapper()


def get_all_shares() -> [{}]:
    result = []
    shares: [Share] = Share.query.all()
    for share in shares:
        share_values = share.share_values
        share_data = share.as_dict()
        logger.debug(f'{share.isin}')
        calculated_values = mapper.calculate(share_values)
        share_data.update(calculated_values)
        share_data[constants.onvista_url] = f'{METRICS_URL}{share_data[constants.isin]}'
        result.append(share_data)
    result = sorted(result, key=lambda s: s.get('total_points').get('point'), reverse=True)
    return result


def get_share_by_isin(isin: str) -> Share:
    share: Share = Share.query.filter(Share.isin == isin).first()
    if share is None:
        share = scrape(isin)
        db.session.add(share)
        db.session.commit()
    return share


def change_type(share_id: int, new_type: int) -> Share:
    share: Share = Share.query.get(share_id)
    share.share_type = ShareType(new_type)
    db.session.commit()
    return share


def load_all_shares():
    ecoreporter_shares: list[BasicShare] = ecoreporter.scrape_ecoreporter()
    fingreen_shares: list[BasicShare] = fingreen.get_shares()

    # merge them together
    all_shares: list[BasicShare] = fingreen_shares
    for ecoreporter_share in ecoreporter_shares:
        found: bool = False
        for share in all_shares:
            if share.isin == ecoreporter_share.isin:
                found = True
                logger.info(f"{ecoreporter_share.name} is in fingreen and ecoreporter")
                break
        if not found:
            logger.info(f'add {ecoreporter_share.name}')
            all_shares.append(ecoreporter_share)
    print(f'{len(all_shares)} new shares found')

    # get share details
    batch = 0
    for bs in all_shares:
        share = scrape(bs.isin)
        if share:
            share.green = True
            db.session.add(share)
            if batch % 10 == 0:
                db.session.commit()
            batch += 1
    db.session.commit()


def scrape(isin: str) -> Share | None:
    try:
        share_raw_data: list[RawData] = onvista.scrape(isin, datetime.utcnow())
        share = __map_share_data(share_raw_data)
        share_values: [ShareValue] = []
        for ov_data in share_raw_data:
            share_value: ShareValue = __map_to_share_value(ov_data)
            share_values.append(share_value)
        share.share_values = share_values
        share.share_type = ShareType.None_Finance
        return share
    except MarketCapitalizationNotFound:
        logger.warning(f'{isin} market capitalization not found')
        return None


@scheduler.task('cron', id='scraper_mgr_cron', day='1,14', month='*', hour='7', minute='0')
def update_all_shares():
    """
    Update the shares every 1 and 14 day of a month at 7.
    All shares in the db were updated
    """
    with scheduler.app.app_context():
        logger.info(f'Updating all')
        shares: [Share] = Share.query.all()
        batch = 0
        for stored_share in shares:
            # TODO - add last scrape to share_value and check before scraping again
            new_share_data: Share = scrape(stored_share.isin)
            if new_share_data:
                new_share_value: list[ShareValue] = new_share_data.share_values
                for share_value in new_share_value:
                    if not stored_share.exists(share_value):
                        share_value.share_id = stored_share.id
                        db.session.add(share_value)
                if batch % 10 == 0:
                    db.session.commit()
                batch += 1
        db.session.commit()


def __map_share_data(share_meta_datas: [RawData]) -> Share:
    """
    :param today:
    :param share_meta_datas:
    :param share:
    :return:
    """
    share: Share = Share()
    for smd in list(share_meta_datas):
        if smd.name == constants.isin:
            share.isin = smd.value
            share_meta_datas.remove(smd)
        elif smd.name == constants.wkn:
            share.wkn = smd.value
            share_meta_datas.remove(smd)
        elif smd.name == constants.symbol:
            share.symbol = smd.value
            share_meta_datas.remove(smd)
        elif smd.name == constants.name:
            share.name = smd.value
            share_meta_datas.remove(smd)
        elif smd.name == constants.logo:
            share.logo_url = smd.value
            share_meta_datas.remove(smd)
        elif smd.name == constants.long_description_ov:
            share.long_description_de = smd.value
            share_meta_datas.remove(smd)
        elif smd.name == constants.country:
            share.country = smd.value
            share_meta_datas.remove(smd)
        elif smd.name == constants.website:
            share.website = smd.value
            share_meta_datas.remove(smd)
        elif smd.name == constants.street:
            share.street = smd.value
            share_meta_datas.remove(smd)
        elif smd.name == constants.city:
            share.city = smd.value
            share_meta_datas.remove(smd)
        elif smd.name == constants.zip_code:
            share.zip_code = smd.value
            share_meta_datas.remove(smd)
        elif smd.name == constants.sector:
            share.sector = smd.value
            share_meta_datas.remove(smd)
        elif smd.name == constants.branch:
            share.branch = smd.value
            share_meta_datas.remove(smd)
        elif smd.name == constants.market:
            share.market = smd.value
            share_meta_datas.remove(smd)

    share.share_type = ShareType.None_Finance
    return share


def __map_to_share_value(raw_data: RawData) -> ShareValue:
    """
    Maps raw data to share value to store the data
    :param share_id:
    :param raw_data:
    :return:
    """
    share_value: ShareValue = ShareValue()
    share_value.name = raw_data.name
    share_value.value = raw_data.value
    share_value.fetch_date = raw_data.fetch_date
    share_value.related_date = raw_data.related_date
    share_value.note = raw_data.note
    return share_value


if __name__ == "__main__":
    print(f'Scraping data from')
    update_all_shares()
