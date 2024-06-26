import json
from json import JSONDecodeError

from bs4 import BeautifulSoup

BASE_URL = "https://onvista.de"

METRICS_URL = f"{BASE_URL}/aktien/kennzahlen/"
COMPANY_PROFILE = f'{BASE_URL}/aktien/unternehmensprofil/'
SHARE_PAGE = f'{BASE_URL}/aktien/'


def snapshot_url(isin: str):
    return f'https://api.onvista.de/api/v1/stocks/ISIN:{isin}/snapshot'


def company_url(entity_value: str):
    return f'https://api.onvista.de/api/v1/stocks/{entity_value}/company_snapshot'


def analyzer_recommendation_url(id_notation: str):
    return f'https://api.onvista.de/api/v1/stocks/{id_notation}/analyzer_recommendations'


timeout = 0


def json_data(html_content, logger):
    soup: BeautifulSoup = BeautifulSoup(html_content, "html.parser")
    try:
        data_json = soup.find('script', id='__NEXT_DATA__').text
        return json.loads(data_json)
    except JSONDecodeError as ex:
        logger.error(f"could not load data origin: {html_content}")
        logger.error(f"error: {ex.msg}")
        raise ex
