import asyncio
from datetime import date, datetime
import re
from typing import Iterator, Optional
from uuid import uuid4
from zoneinfo import ZoneInfo
import aiohttp
from bs4 import BeautifulSoup
from pydantic import HttpUrl
from models.cinema import Cinema, CinemaSummary
from common import web_utils
from models.region import Region
from models.movie import Movie

MOVIES_URL_TEMPLATE = '{host}/now-playing/{region_slug}'
MOVIE_DETAILS_URL_TEMPLATE = '{host}/movie/{movie_slug}'
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


async def scrape_sessions(
    region: Region, host: str, cinemas: list[Cinema]
) -> list[Movie] | None:
    async with aiohttp.ClientSession() as http_session:
        now_showing_url = MOVIES_URL_TEMPLATE.format(host=host, region_slug=region.slug)
        now_showing_html = await web_utils.fetch_html(
            session=http_session, url=now_showing_url
        )
        if now_showing_html is None:
            return None

        async def fetch_movie_details(movie_slug: str) -> dict:
            movie_details_url = MOVIE_DETAILS_URL_TEMPLATE.format(
                host=host, movie_slug=movie_slug
            )
            movie_details_html = await web_utils.fetch_html(
                session=http_session, url=movie_details_url
            )
            return _parse_movie_details(movie_details_html)

        async def fetch_movie_showtimes(movie_slug: str) -> list[str]:
            movie_showtimes_url = MOVIE_SHOWTIMES_URL_TEMPLATE.format(
                host=host, movie_slug=movie_slug, region_slug=region.slug
            )
            movie_showtimes_html = await web_utils.fetch_html(
                session=http_session, url=movie_showtimes_url
            )
            return _parse_movie_showtimes(movie_showtimes_html)

        async def fetch_movie_venues(movie_slug: str, showtime: str) -> list[str]:
            movie_venues_url = MOVIE_VENUES_URL_TEMPLATE.format(
                host=host, movie_slug=movie_slug, showtime=showtime
            )
            movie_venues_html = await web_utils.fetch_html(
                session=http_session, url=movie_venues_url
            )
            cinemas_map = {cinema.name: cinema.homepage_url for cinema in cinemas}
            return _parse_movie_venues(movie_venues_html, cinemas_map)

        async def fetch_and_enrich_movie(movie: dict) -> Optional[Movie]:
            fetch_details_task = fetch_movie_details(movie['slug'])
            fetch_showtimes_task = fetch_movie_showtimes(movie['slug'])
            details, showtimes = await asyncio.gather(
                fetch_details_task, fetch_showtimes_task
            )
            if len(showtimes) == 0:
                return None

            earliest_showtime = showtimes[0]
            venues = await fetch_movie_venues(movie['slug'], earliest_showtime)

            return Movie(
                id=str(uuid4()),
                title=movie['title'],
                release_year=details['release_year'],
                image_url=details['image_url'],
                region=region.name,
                cinemas=venues,
                showtimes=showtimes,
            )

        parsed_movies = _parse_now_showing_movies(now_showing_html)
        tasks = [fetch_and_enrich_movie(parsed_movie) for parsed_movie in parsed_movies]
        enriched_movies = await asyncio.gather(*tasks)

        return [
            enriched_movie
            for enriched_movie in enriched_movies
            if enriched_movie is not None
        ]


def _parse_now_showing_movies(html: str) -> Iterator[dict]:
    seen_titles = set()
    now_showing_soup = BeautifulSoup(html, 'lxml')
    for movie_element in now_showing_soup.find_all('h3', class_=MOVIE_CLASS_SELECTOR):
        movie_anchor = movie_element.find('a')
        movie_title = _clean_movie_title(movie_anchor.text)
        if movie_title in seen_titles:
            continue
        seen_titles.add(movie_title)

        movie_slug = movie_anchor.get('href').strip('/').split('/')[1]
        yield {'title': movie_title, 'slug': movie_slug}


def _parse_movie_details(html: str) -> dict:
    movie_details_soup = BeautifulSoup(html, 'lxml')
    movie_release_year = movie_details_soup.find(
        'div', MOVIE_RELEASE_YEAR_SELECTOR
    ).text
    movie_image_url = movie_details_soup.find('div', MOVIE_IMAGE_URL_SELECTOR).find(
        'img'
    )['src']

    return {'release_year': int(movie_release_year), 'image_url': movie_image_url}


def _parse_movie_showtimes(html: str) -> list[str]:
    movie_showtimes_soup = BeautifulSoup(html, 'lxml')
    showtimes_elements = movie_showtimes_soup.find_all('span', MOVIE_SHOWTIMES_SELECTOR)
    showtimes = []
    for showtime_element in showtimes_elements:
        showtime_day = showtime_element.find('span', MOVIE_SHOWTIME_DAY_SELECTOR).text
        showtime_month = showtime_element.find(
            'span', MOVIE_SHOWTIME_MONTH_SELECTOR
        ).text
        showtimes.append(
            _parse_date(
                showtime_day,
                showtime_month,
                datetime.now(ZoneInfo('Pacific/Auckland')).date(),
            )
        )

    return showtimes


def _parse_movie_venues(
    html: str, cinemas: dict[str, HttpUrl | None]
) -> list[CinemaSummary]:
    movie_venues_soup = BeautifulSoup(html, 'lxml')
    venues_elements = movie_venues_soup.find_all('div', MOVIE_VENUES_SELECTOR)
    venues = []
    for venue_element in venues_elements:
        venue_name = venue_element.find('h4').text
        venue_homepage_url = cinemas[venue_name]
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


def _parse_date(day: str, month: str, now: date) -> str:
    month_num = datetime.strptime(month, '%b').month
    year = now.year

    if month_num < now.month:
        year += 1

    return f'{year}-{month_num:02d}-{int(day):02d}'
