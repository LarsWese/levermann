from dataclasses import dataclass
from typing import List

from sqlalchemy import desc

from levermann_share_value import db
from levermann_share_value.database.models import Share, ShareType, ShareValue
from levermann_share_value.scraper.onvista import METRICS_URL, onvista
import logging
from datetime import datetime, date
from levermann_share_value.levermann import constants

logger = logging.getLogger(__name__)


def get_all_shares() -> List[Share]:
    result: List[Share] = []
    shares: [Share] = Share.query.all()
    fetch_date: date = get_fetch_dates()[0]

    # for share in shares:
    #     share_values = share.share_values
    #     share_data = share.as_dict()
    #     logger.debug(f'{share.isin}')
    #     calculated_values = mapper.calculate(share_values)
    #     share_data.update(calculated_values)
    #     share_data[constants.onvista_url] = f'{METRICS_URL}{share_data[constants.isin]}'
    #     result.append(share_data)
    # result = sorted(result, key=lambda s: s.get('total_points').get('point'), reverse=True)
    return result


def get_fetch_dates() -> List[date]:
    return ShareValue.query.group_by(ShareValue.fetch_date)


def get_share_values(share_id: int, fetch_date: datetime) -> List[ShareValue]:
    return ShareValue.query.filter_by(share_id=share_id, fetch_data=fetch_date).order_by(desc(ShareValue.fetch_date))


class LevermannCalculator:
    def __init__(self, share_values: List[ShareValue]):
        self.share_values = share_values


@dataclass
class LevermannValue:
    value: str
    point: int


@dataclass
class ShareData:
    name: str
    wkn: str
    isin: str
    symbol: str
    country: str
    website: str
    sector: str
    branch: str
    description: str
    long_description: str
    levermann_values: {datetime: {str, LevermannValue}}
    total_points: int
