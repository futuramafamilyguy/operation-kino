from typing import Iterator

from bs4 import BeautifulSoup
from uuid import uuid4
import validators

from common import web_utils
from models.cinema import Cinema
from models.region import Region


CINEMAS_URL_TEMPLATE = '{host}/cinemas/{region_slug}/'
CINEMA_DETAILS_URL_TEMPLATE = '{host}/cinema/{cinema_slug}'

CINEMA_CLASS_SELECTOR = 'more-cinemas__link'
CINEMA_TITLE_CLASS_SELECTOR = 'more-cinemas__title'
CINEMA_DETAILS_CLASS_SELECTOR = 'cinema-info__block'


def scrape_cinemas(region: Region, host: str) -> list[Cinema] | None:
    cinemas_url = CINEMAS_URL_TEMPLATE.format(host=host, region_slug=region.slug)
    cinemas_html = web_utils.fetch_html(cinemas_url)
    if cinemas_html is None:
        return None

    cinemas = []
    for cinema in _parse_cinema_listings(cinemas_html):
        cinema_details_url = CINEMA_DETAILS_URL_TEMPLATE.format(
            host=host, cinema_slug=cinema['slug']
        )
        cinema_details_html = web_utils.fetch_html(cinema_details_url)
        cinema_enriched = _enrich_cinema_with_url(
            cinema['name'], region.name, cinema_details_html
        )
        cinemas.append(cinema_enriched)

    return cinemas


def _parse_cinema_listings(html: str) -> Iterator[dict]:
    cinemas_soup = BeautifulSoup(html, 'lxml')
    for cinema_element in cinemas_soup.find_all('a', class_=CINEMA_CLASS_SELECTOR):
        cinema_name = cinema_element.find('h2', class_=CINEMA_TITLE_CLASS_SELECTOR).text
        cinema_slug = cinema_element.get('href').strip('/').split('/')[1]
        yield {'name': cinema_name, 'slug': cinema_slug}


def _enrich_cinema_with_url(cinema_name: str, region_name: str, html: str) -> Cinema:
    if html is None:
        return Cinema(
            id=str(uuid4()), name=cinema_name, homepage_url=None, region=region_name
        )

    cinema_details_soup = BeautifulSoup(html, 'lxml')
    cinema_details_element = cinema_details_soup.find(
        'ul', class_=CINEMA_DETAILS_CLASS_SELECTOR
    )
    cinema_url = cinema_details_element.find('a').text
    if not validators.url(
        cinema_url
    ):  # sometimes the url is a phone number wtf brisbane??
        cinema_url = None

    return Cinema(
        id=str(uuid4()), name=cinema_name, homepage_url=cinema_url, region=region_name
    )
