import re
from typing import Iterator
from bs4 import BeautifulSoup
import requests
from src.common import web_utils
from src.models.region import Region
from src.models.movie import Movie

MOVIES_URL_TEMPLATE = '{host}/now-playing/{region_slug}'

MOVIE_CLASS_SELECTOR = 'movie-list-carousel-item__heading'

def scrape_sessions(region: Region, host: str) -> list[Movie] | None:    
    now_showing_url = MOVIES_URL_TEMPLATE.format(host=host, region_slug=region.slug)
    now_showing_html = web_utils.fetch_html(now_showing_url)
    if now_showing_html is None:
        return None
    
    for movie in _parse_now_showing_movies(now_showing_html):
        print(f"{movie['title']}: {movie['slug']}")
    
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

def _clean_movie_title(title: str) -> str:
    # removes trailing year from some movies eg. (2014), (2014-15)
    return re.sub(r'\s*\((\d{4}(?:-\d{2,4})?)\)$', '', title)
