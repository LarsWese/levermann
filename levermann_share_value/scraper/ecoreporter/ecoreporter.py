import logging

import requests
from bs4 import BeautifulSoup

from levermann_share_value.scraper import headers
from levermann_share_value.scraper.raw_data import BasicShare

BASE_URL = "https://www.ecoreporter.de/aktienkurse/"
logger = logging.getLogger(__name__)


def scrape_ecoreporter() -> list[BasicShare]:
    result: list[BasicShare] = []
    page = requests.get(BASE_URL, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")
    soup = soup.select('.list')[0]
    rows = soup.find_all('tr')
    for row in rows:
        # Extract the instrument-name
        instrument_name = row.find('td', {'class': 'instrument-name'}).get_text(strip=True)
        # Extract the isin
        isin = row.find('a').get('href').split('/')[-2]
        # Create a BasicShare object and append it to the result list
        basic_share = BasicShare(isin=isin, name=instrument_name, green=True, description='')
        logger.info(f'add {instrument_name} {isin}')
        result.append(basic_share)
    logger.debug(f'{result}')
    return result


if __name__ == '__main__':
    # get_isin('/scatec-asa-aktie')
    scrape_ecoreporter()
