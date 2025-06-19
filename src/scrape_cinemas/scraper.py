import asyncio
import logging
from typing import Iterator, Optional

import aiohttp
from bs4 import BeautifulSoup
from uuid import uuid4
import validators

from web_utils import fetch_html
from exceptions import ScrapingException
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
        cinemas_html = await fetch_html(session, cinemas_url)
        if cinemas_html is None:
            logger.error(f'{cinemas_url} did not return anything')
            return []

        async def _fetch_and_enrich_cinema(cinema: dict) -> Optional[Cinema]:
            cinema_details_url = CINEMA_DETAILS_URL_TEMPLATE.format(
                host=host, cinema_slug=cinema['slug']
            )
            cinema_details_html = await fetch_html(session, cinema_details_url)
            try:
                if cinema_details_html is None:
                    logger.error(
                        f'cinema details page could not be loaded for {cinema["name"]} at: {cinema_details_url}'
                    )
                    raise ScrapingException('cinema detail scraping failed')
                return _enrich_cinema_with_url(
                    cinema['name'], region.name, region.slug, cinema_details_html
                )
            except ScrapingException:
                logger.warning(
                    f'skipping cinema due to scraping failure: {cinema["name"]}'
                )
                return None

        parsed_cinemas = _parse_cinema_listings(cinemas_html)
        try:
            tasks = [_fetch_and_enrich_cinema(cinema) for cinema in parsed_cinemas]
        except ScrapingException:
            logger.error(
                f'could not find any cinemas in cinema listing page at: {cinemas_url}'
            )
            logger.debug(f'cinema listing page: {cinemas_html}')
            return []

        enriched_cinemas = await asyncio.gather(*tasks)

        return [
            enriched_cinema
            for enriched_cinema in enriched_cinemas
            if enriched_cinema is not None
        ]


def _parse_cinema_listings(html: str) -> Iterator[dict]:
    cinemas_soup = BeautifulSoup(html, 'lxml')
    cinema_elements = cinemas_soup.find_all('a', class_=CINEMA_CLASS_SELECTOR)
    if not cinema_elements:
        raise ScrapingException('cinema listing scraping failed')

    for cinema_element in cinema_elements:
        # scrape cinema name
        cinema_name_element = cinema_element.find(
            'h2', class_=CINEMA_TITLE_CLASS_SELECTOR
        )
        if cinema_name_element is None:
            logger.error(
                f'could not find <h2.{CINEMA_TITLE_CLASS_SELECTOR}> element for cinema name in: {cinema_element}'
            )
            continue

        # scrape cinema url slug
        cinema_slug_href = cinema_element.get('href')
        if cinema_slug_href is None:
            logger.error(
                f'could not find <a.{CINEMA_CLASS_SELECTOR}[href]> for cinema slug in: {cinema_element}'
            )
            continue
        cinema_slug_parts = cinema_slug_href.strip('/').split('/')
        if len(cinema_slug_parts) != 2:
            logger.error(
                f'unexpected format for cinema slug. expected: </cinema/cinema-name> actual: <{cinema_slug_href}>'
            )
            continue

        yield {'name': cinema_name_element.text, 'slug': cinema_slug_parts[1]}


def _enrich_cinema_with_url(
    cinema_name: str, region_name: str, region_slug: str, html: str
) -> Cinema:
    cinema_details_soup = BeautifulSoup(html, 'lxml')
    cinema_details_element = cinema_details_soup.find(
        'ul', class_=CINEMA_DETAILS_CLASS_SELECTOR
    )
    if cinema_details_element is None:
        logger.error(
            f'could not find <ul.{CINEMA_DETAILS_CLASS_SELECTOR}> for {cinema_name} cinema details in cinema details page:'
        )
        logger.debug(f'cinema details page: {cinema_details_soup}')
        raise ScrapingException('cinema detail scraping failed')

    cinema_url_element = cinema_details_element.find('a')
    if cinema_url_element is None:
        logger.error(
            f'could not find <a> for {cinema_name} cinema details in: {cinema_details_element}'
        )
        raise ScrapingException('cinema detail scraping failed')

    cinema_url = cinema_url_element.text
    if not validators.url(
        cinema_url
    ):  # sometimes the url is a phone number wtf brisbane??
        logger.warning(
            f'found homepage url element for {cinema_name} but does not contain a valid url: {cinema_url}'
        )
        cinema_url = None

    return Cinema(
        id=str(uuid4()),
        name=cinema_name,
        homepage_url=cinema_url,
        region=region_name,
        region_code=region_slug,
    )
