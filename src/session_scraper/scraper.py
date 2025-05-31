import re
from typing import Iterator
from bs4 import BeautifulSoup
import requests
from src.common import web_utils
from src.models.region import Region
from src.models.movie import Movie

MOVIES_URL_TEMPLATE = '{host}/now-playing/{region_slug}'
MOVIE_DETAILS_URL_TEMPLATE = '{host}/movie/{movie_slug}'

MOVIE_CLASS_SELECTOR = 'movie-list-carousel-item__heading'

MOVIE_RELEASE_YEAR_SELECTOR = 'single-movie__release-year'
MOVIE_IMAGE_URL_SELECTOR = 'single-movie__featured-image'

def scrape_sessions(region: Region, host: str) -> list[Movie] | None: 
    http_session = requests.Session()   
    now_showing_url = MOVIES_URL_TEMPLATE.format(host=host, region_slug=region.slug)
    now_showing_html = web_utils.fetch_html_stateful(session=http_session, url=now_showing_url)
    if now_showing_html is None:
        return None
    
    movies = []
    for movie in _parse_now_showing_movies(now_showing_html):
        movie_details_url = MOVIE_DETAILS_URL_TEMPLATE.format(host=host, movie_slug=movie['slug'])
        movie_details_html = web_utils.fetch_html_stateful(session=http_session, url=movie_details_url)
        movie_details = _parse_movie_details(movie_details_html)
        print(f"{movie['title']}: {movie['slug']}, {movie_details['release_year']}, {movie_details['image_url']}")
    
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
        yield {
            'title': movie_title,
            'slug': movie_slug
        }

def _parse_movie_details(html: str) -> dict:
    movie_details_soup = BeautifulSoup(html, 'lxml')
    movie_release_year = movie_details_soup.find('div', MOVIE_RELEASE_YEAR_SELECTOR).text
    movie_image_url = movie_details_soup.find('div', MOVIE_IMAGE_URL_SELECTOR).find('img')['src']
    
    return {
        'release_year': int(movie_release_year),
        'image_url': movie_image_url
    }

def _clean_movie_title(title: str) -> str:
    # removes trailing year from some movies eg. (2014), (2014-15)
    return re.sub(r'\s*\((\d{4}(?:-\d{2,4})?)\)$', '', title)
