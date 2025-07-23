import asyncio
from datetime import date, datetime
import logging
import re
from typing import Iterator, Optional
from uuid import uuid4
from zoneinfo import ZoneInfo
import aiohttp
from bs4 import BeautifulSoup
from pydantic import HttpUrl
from exceptions import ScrapingException
from models.cinema import Cinema, CinemaSummary
from web_utils import fetch_html, fetch_html_section
from models.region import Region
from models.movie import Movie

MOVIES_URL_TEMPLATE = '{host}/now-playing/{region_slug}'
MOVIE_DETAILS_URL_TEMPLATE = '{host}/movie/{movie_slug}/'
MOVIE_SHOWTIMES_URL_TEMPLATE = '{host}/movie/times/{movie_slug}/{region_slug}'
MOVIE_VENUES_URL_TEMPLATE = '{host}/movie/sessions/{movie_slug}/{showtime}/region/'

# now showing page
MOVIE_CLASS_SELECTOR = 'movie-list-carousel-item__heading'

# movie details page
MOVIE_RELEASE_YEAR_SELECTOR = 'single-movie__release-year'
MOVIE_IMAGE_URL_SELECTOR = 'single-movie__featured-image'

# movie showtimes page
MOVIE_SHOWTIMES_SELECTOR = 'times-calendar__el-grouper'
MOVIE_SHOWTIME_DAY_SELECTOR = 'times-calendar__el__date'
MOVIE_SHOWTIME_MONTH_SELECTOR = 'times-calendar__el__month'

# movie bookings page
MOVIE_VENUES_SELECTOR = 'movie-times__cinema__copy'

# no need to stream showtime and venue pages since they are much smaller
MOVIES_START = '<div class="container__outer playing-now playing-now--sliders">'
MOVIES_END = (
    '<div id="genre-modal class="modal modal--v5 modal--genre modal--opacity js-modal">'
)
MOVIE_DETAILS_START = '<main>'
MOVIE_DETAILS_END = '</main>'

logger = logging.getLogger(__name__)


async def scrape_sessions(
    region: Region, host: str, cinemas: list[Cinema]
) -> list[Movie] | None:
    async with aiohttp.ClientSession() as http_session:
        now_showing_url = MOVIES_URL_TEMPLATE.format(host=host, region_slug=region.slug)
        now_showing_html = await fetch_html_section(
            http_session, now_showing_url, MOVIES_START, MOVIES_END
        )
        if now_showing_html is None:
            logger.error(
                f'fetching now showing movies html returned null: {now_showing_html}'
            )
            return None

        async def _fetch_movie_details(movie_slug: str) -> dict:
            movie_details_url = MOVIE_DETAILS_URL_TEMPLATE.format(
                host=host, movie_slug=movie_slug
            )
            movie_details_html = await fetch_html_section(
                http_session, movie_details_url, MOVIE_DETAILS_START, MOVIE_DETAILS_END
            )
            return _parse_movie_details(movie_details_html)

        async def _fetch_movie_showtimes(movie_slug: str) -> list[str]:
            movie_showtimes_url = MOVIE_SHOWTIMES_URL_TEMPLATE.format(
                host=host, movie_slug=movie_slug, region_slug=region.slug
            )
            movie_showtimes_html = await fetch_html(
                session=http_session, url=movie_showtimes_url
            )
            if movie_showtimes_html is None:
                raise ScrapingException(
                    f'fetching movie showtimes html returned null: {movie_showtimes_html}'
                )

            return _parse_movie_showtimes(movie_showtimes_html)

        async def _fetch_movie_venues(movie_slug: str, showtime: str) -> list[str]:
            movie_venues_url = MOVIE_VENUES_URL_TEMPLATE.format(
                host=host, movie_slug=movie_slug, showtime=showtime
            )
            movie_venues_html = await fetch_html(
                session=http_session, url=movie_venues_url
            )
            if movie_venues_html is None:
                raise ScrapingException(
                    f'fetching movie venues html returned null: {movie_venues_url}'
                )

            cinemas_map = {cinema.name: cinema.homepage_url for cinema in cinemas}
            return _parse_movie_venues(movie_venues_html, cinemas_map)

        async def _fetch_and_enrich_movie(movie: dict) -> Optional[Movie]:
            try:
                fetch_details_task = _fetch_movie_details(movie['slug'])
                fetch_showtimes_task = _fetch_movie_showtimes(movie['slug'])
                details, showtimes = await asyncio.gather(
                    fetch_details_task, fetch_showtimes_task
                )
                if not showtimes:
                    logger.error(
                        f'failed to scrape showtimes for movie {movie["title"]}'
                    )
                    raise ScrapingException('movie showtime scraping failed')

                earliest_showtime = showtimes[0]
                venues = await _fetch_movie_venues(movie['slug'], earliest_showtime)
                if not venues:
                    logger.error(f'failed to scrape venues for movie {movie["title"]}')
                    raise ScrapingException('movie venue scraping failed')

                return Movie(
                    id=str(uuid4()),
                    title=movie['title'],
                    release_year=details['release_year'],
                    image_url=details['image_url'],
                    region=region.name,
                    region_code=region.slug,
                    cinemas=venues,
                    showtimes=showtimes,
                    last_showtime=showtimes[-1],
                )
            except ScrapingException:
                logger.warning(
                    f'skipping movie due to scraping failure: {movie["title"]}'
                )
                return None

        parsed_movies = _parse_now_showing_movies(now_showing_html)
        try:
            tasks = [
                _fetch_and_enrich_movie(parsed_movie) for parsed_movie in parsed_movies
            ]
        except ScrapingException:
            logger.error(
                f'could not find any movies in now showing page at: {now_showing_url}'
            )
            logger.debug(f'now showing page: {now_showing_html}')
            return []

        enriched_movies = await asyncio.gather(*tasks)
        return [
            enriched_movie
            for enriched_movie in enriched_movies
            if enriched_movie is not None
        ]


def _parse_now_showing_movies(html: str) -> Iterator[dict]:
    seen_titles = set()
    now_showing_soup = BeautifulSoup(html, 'lxml')
    movie_elements = now_showing_soup.find_all('h3', class_=MOVIE_CLASS_SELECTOR)
    if not movie_elements:
        raise ScrapingException('now playing movies scraping failed')

    for movie_element in movie_elements:
        movie_anchor = movie_element.find('a')

        # scrape movie title
        if movie_anchor is None or movie_anchor.text is None:
            logger.error(
                f'could not find <a> element for movie title in: {movie_element}'
            )
            continue
        movie_title = _clean_movie_title(movie_anchor.text)
        if movie_title in seen_titles:
            continue
        seen_titles.add(movie_title)

        # scrape movie slug
        movie_slug_href = movie_anchor.get('href')
        if movie_slug_href is None:
            logger.error(f'could not find <a[href]> for movie slug in {movie_anchor}')
            continue
        movie_slug_parts = movie_slug_href.strip('/').split('/')
        if len(movie_slug_parts) != 2:
            logger.error(
                f'unexpected format for movie slug. expected: </movie/movie-title> actual: <{movie_slug_href}>'
            )
            continue

        yield {'title': movie_title, 'slug': movie_slug_parts[1]}


def _parse_movie_details(html: str) -> dict:
    movie_details_soup = BeautifulSoup(html, 'lxml')

    # scrape movie release year
    movie_release_year_element = movie_details_soup.find(
        'div', MOVIE_RELEASE_YEAR_SELECTOR
    )
    if movie_release_year_element is None:
        logger.error(
            f'could not find <div.{MOVIE_RELEASE_YEAR_SELECTOR}> for movie release year in movie details page'
        )
        logger.debug(f'movie details page: {movie_details_soup}')
        raise ScrapingException('movie detail (release year) scraping failed')

    # scrape movie image url
    movie_image_url_div = movie_details_soup.find('div', MOVIE_IMAGE_URL_SELECTOR)
    if movie_image_url_div is None:
        logger.error(
            f'could not find <div.{MOVIE_IMAGE_URL_SELECTOR}> for movie image url in movie details page'
        )
        logger.debug(f'movie details page: {movie_details_soup}')
        raise ScrapingException('movie detail (image url) scraping failed')
    movie_image_url_img = movie_image_url_div.find('img')
    if movie_image_url_img is None:
        logger.error(
            f'could not find <img> for movie image url in: {movie_image_url_div}'
        )
        raise ScrapingException('movie detail (image url) scraping failed')

    return {
        'release_year': int(movie_release_year_element.text),
        'image_url': movie_image_url_img['src'],
    }


def _parse_movie_showtimes(html: str) -> list[str]:
    movie_showtimes_soup = BeautifulSoup(html, 'lxml')
    showtimes_elements = movie_showtimes_soup.find_all('span', MOVIE_SHOWTIMES_SELECTOR)
    showtimes = []
    for showtime_element in showtimes_elements:
        # scrape showtime day
        showtime_day_span = showtime_element.find('span', MOVIE_SHOWTIME_DAY_SELECTOR)
        if showtime_day_span is None:
            logger.error(
                f'could not find <span.{MOVIE_SHOWTIME_DAY_SELECTOR}> for showtime day in: {showtime_element}'
            )
            continue

        # scrape showtime month
        showtime_month_span = showtime_element.find(
            'span', MOVIE_SHOWTIME_MONTH_SELECTOR
        )
        if showtime_month_span is None:
            logger.error(
                f'could not find <span.{MOVIE_SHOWTIME_MONTH_SELECTOR}> for showtime month in: {showtime_element}'
            )
            continue

        showtimes.append(
            _parse_date(
                showtime_day_span.text,
                showtime_month_span.text,
                datetime.now(ZoneInfo('Pacific/Auckland')).date(),
            )
        )

    return showtimes


def _parse_movie_venues(
    html: str, cinemas: dict[str, Optional[HttpUrl]]
) -> list[CinemaSummary]:
    movie_venues_soup = BeautifulSoup(html, 'lxml')
    venues_elements = movie_venues_soup.find_all('div', MOVIE_VENUES_SELECTOR)
    venues = []
    for venue_element in venues_elements:
        venue_name_h4 = venue_element.find('h4')
        if venue_name_h4 is None:
            logger.error(
                f'could not find <h4> for movie venue name in: {venue_element}'
            )
            continue

        venue_name = venue_name_h4.text
        if venue_name not in cinemas:
            unparsed_venue_name = venue_name
            venue_name = _clean_cinema_name(venue_name)
            if venue_name not in cinemas:
                logger.warning(
                    f'venue not found in cinema table: {unparsed_venue_name}'
                )
                continue
        venue_homepage_url = cinemas.get(venue_name)

        venues.append(
            CinemaSummary(
                name=venue_name,
                homepage_url=str(venue_homepage_url)
                if venue_homepage_url is not None
                else None,
            )
        )

    return venues


def _clean_movie_title(title: str) -> str:
    # removes trailing year from some movies eg. (2014), (2014-15)
    return re.sub(r'\s*\((\d{4}(?:-\d{2,4})?)\)$', '', title)


def _clean_cinema_name(name: str) -> str:
    # removes trailing paren from cinema name
    return re.sub(r'\s*\(.*\)$', '', name)


def _parse_date(day: str, month: str, now: date) -> str:
    month_num = datetime.strptime(month, '%b').month
    year = now.year

    if month_num < now.month:
        year += 1

    return f'{year}-{month_num:02d}-{int(day):02d}'
