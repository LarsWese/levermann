import json
from json import JSONDecodeError

from bs4 import BeautifulSoup

BASE_URL = "https://onvista.de"


def json_data(html_content, logger):
    soup: BeautifulSoup = BeautifulSoup(html_content, "html.parser")
    try:
        data_json = soup.find('script', id='__NEXT_DATA__').text
        return json.loads(data_json)
    except JSONDecodeError as ex:
        logger.error(f"could not load data origin: {html_content}")
        logger.error(f"error: {ex.msg}")
        raise ex
