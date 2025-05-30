from pathlib import Path

from pydantic import HttpUrl
from src.cinema_scraper.scraper import _enrich_cinema_with_url, _parse_cinema_listings

def load_fixture(filename):
    path = Path(__file__).parent.parent / 'fixtures' / filename
    return path.read_text()

def test_parse_cinema_listings():
    expected_cinemas = [
        {
            'name': 'Maya Cinemas',
            'slug': 'maya-cinemas'
        },
        {
            'name': 'Lighthouse Cinemas',
            'slug': 'lighthouse-cinemas'
        },
    ]
    html = load_fixture('cinemas.html')

    actual_cinemas = list(_parse_cinema_listings(html))

    assert actual_cinemas == expected_cinemas

def test_parse_cinema_listings_no_cinemas():
    expected_cinemas = []
    html = load_fixture('no_cinemas.html')

    actual_cinemas = list(_parse_cinema_listings(html))

    assert actual_cinemas == expected_cinemas

def test_enrich_cinema_with_url():
    cinema_name = 'Maya Cinemas'
    cinema_region = 'Monterey County'
    html = load_fixture('cinema_details.html')

    cinema = _enrich_cinema_with_url(cinema_name, cinema_region, html)

    assert cinema.name == cinema_name
    assert cinema.homepage_url == HttpUrl('https://www.mayacinemas.com/salinas')
    assert cinema.region == cinema_region

def test_enrich_cinema_with_url_no_url():
    cinema_name = 'Lighthouse Cinemas'
    cinema_region = 'Monterey County'
    html = load_fixture('cinema_details_no_url.html')

    cinema = _enrich_cinema_with_url(cinema_name, cinema_region, html)

    assert cinema.name == cinema_name
    assert cinema.homepage_url == None
    assert cinema.region == cinema_region
