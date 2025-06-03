import asyncio
import logging
from typing import Iterator

import aiohttp
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

logger = logging.getLogger(__name__)


async def scrape_cinemas(region: Region, host: str) -> list[Cinema]:
    async with aiohttp.ClientSession() as session:
        cinemas_url = CINEMAS_URL_TEMPLATE.format(host=host, region_slug=region.slug)
        cinemas_html = await web_utils.fetch_html(session, cinemas_url)
        if cinemas_html is None:
            logger.error(f'{cinemas_url} did not return anything')
            return []

        async def _fetch_and_enrich_cinema(cinema: dict):
            cinema_details_url = CINEMA_DETAILS_URL_TEMPLATE.format(
                host=host, cinema_slug=cinema['slug']
            )
            cinema_details_html = await web_utils.fetch_html(
                session, cinema_details_url
            )
            if cinema_details_html is None:
                logger.warning(
                    f'cinema details page could not be loaded for {cinema["name"]} at: {cinema_details_url}'
                )
                return Cinema(
                    id=str(uuid4()),
                    name=cinema['name'],
                    homepage_url=None,
                    region=region.name,
                )

            return _enrich_cinema_with_url(
                cinema['name'], region.name, cinema_details_html
            )

        parsed_cinemas = _parse_cinema_listings(cinemas_html)
        if not parsed_cinemas:
            logger.error(
                f'{cinemas_url} returned something but could not find any cinemas in it: {cinemas_html}'
            )
            return []

        enriched_cinemas = await asyncio.gather(
            *[_fetch_and_enrich_cinema(cinema) for cinema in parsed_cinemas]
        )

        return enriched_cinemas


def _parse_cinema_listings(html: str) -> Iterator[dict]:
    cinemas_soup = BeautifulSoup(html, 'lxml')
    for cinema_element in cinemas_soup.find_all('a', class_=CINEMA_CLASS_SELECTOR):
        cinema_name_element = cinema_element.find(
            'h2', class_=CINEMA_TITLE_CLASS_SELECTOR
        )
        if cinema_name_element is None:
            logger.error(
                f'could not find <h2.{CINEMA_TITLE_CLASS_SELECTOR}> element for cinema name in: {cinema_element}'
            )
            continue

        cinema_slug = cinema_element.get('href').strip('/').split('/')[1]
        if cinema_slug is None:
            logger.error(
                f'could not find <a.{CINEMA_CLASS_SELECTOR}[href]> for cinema slug in: {cinema_element}'
            )
            continue

        yield {'name': cinema_name_element.text, 'slug': cinema_slug}


def _enrich_cinema_with_url(cinema_name: str, region_name: str, html: str) -> Cinema:
    cinema_details_soup = BeautifulSoup(html, 'lxml')
    cinema_details_element = cinema_details_soup.find(
        'ul', class_=CINEMA_DETAILS_CLASS_SELECTOR
    )
    cinema_url_element = cinema_details_element.find('a')
    if cinema_details_element is None or cinema_url_element is None:
        logger.error(
            f'could not find <ul.{CINEMA_DETAILS_CLASS_SELECTOR} a> for cinema details in: {cinema_details_soup}'
        )
        return Cinema(
            id=str(uuid4()), name=cinema_name, homepage_url=None, region=region_name
        )

    cinema_url = cinema_url_element.text
    if not validators.url(
        cinema_url
    ):  # sometimes the url is a phone number wtf brisbane??
        logger.warning(
            f'found homepage url element for {cinema_name} but does not contain a valid url: {cinema_url}'
        )
        cinema_url = None

    return Cinema(
        id=str(uuid4()), name=cinema_name, homepage_url=cinema_url, region=region_name
    )
