import logging

import requests
from bs4 import BeautifulSoup, ResultSet

from levermann_share_value.scraper import headers
from scraper.raw_data import BasicShare

BASE_URL = "https://www.fingreen.de"
URL = BASE_URL + "/gruene-Aktien"
logger = logging.getLogger(__name__)


def get_shares() -> list[BasicShare]:
    result: list[BasicShare] = []
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")

    stock_tables = soup.find_all("table", class_="table")

    for stock_table in stock_tables:
        rows = stock_table.find_all("tr", class_="row")

        for row in rows:
            find_all: ResultSet = row.find_all("td")
            if len(find_all) > 0:
                detail = find_all[0].find('a', href=True)
                name = detail.text
                isin = get_isin(detail['href'])
                description = find_all[2].text
                result.append(BasicShare(name=name, isin=isin, description=description))

    return result


def get_isin(detail_page_link: str) -> str:
    detail_page = BeautifulSoup(requests.get(BASE_URL + detail_page_link, headers=headers).content,
                                "html.parser")
    isin = detail_page.find_all('span', text='ISIN:')[0].next_sibling.text.strip()
    if not isin:
        sibling = detail_page.find_all('span', text='ISIN:')[0].next_sibling.next_sibling
        if sibling:
            isin = sibling.text.strip()
        else:
            isin = detail_page.find_all('span', text='ISIN:')[0].parent.next_sibling.text.strip()
    return isin


if __name__ == '__main__':
    # get_isin('/scatec-asa-aktie')
    get_shares()