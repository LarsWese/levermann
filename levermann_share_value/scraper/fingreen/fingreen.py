import logging

import requests
from bs4 import BeautifulSoup, ResultSet

from levermann_share_value import db
from levermann_share_value.database.models import Share
from levermann_share_value.scraper import headers

BASE_URL = "https://www.fingreen.de"
URL = BASE_URL + "/gruene-Aktien"
logger = logging.getLogger(__name__)


def get_shares() -> list:
    result: list = []
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")

    stock_tables = soup.find_all("table", class_="table")

    for stock_table in stock_tables:
        rows = stock_table.find_all("tr", class_="row")

        for row in rows:
            find_all: ResultSet = row.find_all("td")
            if len(find_all) > 0:
                name = find_all[0]('a', href=True)[0].text
                link = find_all[0]('a', href=True)[0]['href']
                wkn = find_all[1].text
                description = find_all[2].text
                country: str = find_all[3].text
                s: Share = Share(name=name,
                                 description=description,
                                 wkn=wkn,
                                 detail_page=BASE_URL + link,
                                 country=country)
                what: Share = Share.query.filter_by(wkn=s.wkn).first()
                logger.info(f'one Share for {s.wkn} {what} ')
                if not what:
                    logger.info('not yet in list.')
                    add_details(s)
                    result.append(s)
                    db.session.add(s)
        db.session.commit()

    return result


def add_details(share: Share):
    logger.debug(f'details for {share.name}')
    response = requests.get(share.fingreen_detail_page, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")
    add_first_information(share, soup)
    # TODO - put infos from fingreen into section
    # div class="according-description" are description and address
    # share.long_description_fingreen = soup.find('p', attrs={'class': 'rteBlock'}).text.replace('\xa0', '')
    # share.address = soup.find('strong', string='Adresse:').parent.text.replace('\xa0', '').replace('Adresse:', '')
    logger.debug(f'details: {share}')


def add_first_information(share, soup):
    # get ISIN and Website
    find = soup.find('span', string='ISIN:')
    isin_number_tag = find.next_sibling
    isin = isin_number_tag.text
    if len(isin) < 13:  # 12 chars for isin and 3 for \xa0
        sibling = isin_number_tag.next_sibling
        if sibling:
            isin = sibling.text
        else:
            isin = find.parent()[0].previous_element.next_sibling.text
    share.isin = isin.replace('\xa0', '').replace('\n', '').strip()
    share.website = soup.find('span', string='Website:').next_sibling.next_sibling.text
