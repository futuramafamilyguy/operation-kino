from datetime import date

from pydantic import HttpUrl
from models.cinema import CinemaSummary
from session_scraper.scraper import (
    _clean_movie_title,
    _parse_date,
    _parse_movie_details,
    _parse_movie_showtimes,
    _parse_movie_venues,
    _parse_now_showing_movies,
)
from test_utils import load_html_fixture


# _parse_now_showing_movies


def test_parse_now_showing_movies():
    expected_movies = [
        {'title': 'Mr. Baseball', 'slug': 'mr-baseball'},
        {'title': 'Cannery Row', 'slug': 'cannery-row'},
    ]
    html = load_html_fixture('now_showing.html')

    actual_movies = list(_parse_now_showing_movies(html))

    assert actual_movies == expected_movies


def test_parse_now_showing_no_movies():
    expected_movies = []
    html = load_html_fixture('now_showing_no_movies.html')

    actual_movies = list(_parse_now_showing_movies(html))

    assert actual_movies == expected_movies


# _parse_movie_details


def test_parse_movie_details():
    expected_details = {
        'release_year': 1982,
        'image_url': 'img-store.com/cannery-row.jpg',
    }
    html = load_html_fixture('movie_details.html')

    actual_details = _parse_movie_details(html)

    assert actual_details == expected_details


# _parse_movie_showtimes


def test_parse_movie_showtimes():
    expected_showtimes = [{'day': '31', 'month': '05'}, {'day': '01', 'month': '06'}]
    html = load_html_fixture('movie_showtimes.html')

    actual_showtimes = [
        {'day': d.split('-')[2], 'month': d.split('-')[1]}
        for d in _parse_movie_showtimes(html)
    ]

    assert actual_showtimes == expected_showtimes


# _parse_movie_venues


def test_parse_movie_venues():
    expected_venues = [
        CinemaSummary(
            name='Maya Cinemas',
            homepage_url='https://www.mayacinemas.com/salinas',
        ),
        CinemaSummary(name='Lighthouse Cinemas', homepage_url=None),
    ]
    existing_cinemas: dict[str, HttpUrl | None] = {}
    existing_cinemas['Maya Cinemas'] = HttpUrl('https://www.mayacinemas.com/salinas')
    existing_cinemas['Lighthouse Cinemas'] = None
    html = load_html_fixture('movie_venues.html')

    actual_venues = _parse_movie_venues(html, existing_cinemas)

    assert actual_venues == expected_venues


# _clean_movie_title


def test_clean_movie_title_with_year():
    original_title = 'Cannery Row (1982)'
    expected_title = 'Cannery Row'

    actual_title = _clean_movie_title(original_title)

    assert actual_title == expected_title


def test_clean_movie_title_with_year_range():
    original_title = 'Cannery Row (1982-83)'
    expected_title = 'Cannery Row'

    actual_title = _clean_movie_title(original_title)

    assert actual_title == expected_title


def test_clean_movie_title_no_year():
    original_title = 'Cannery Row'
    expected_title = 'Cannery Row'

    actual_title = _clean_movie_title(original_title)

    assert actual_title == expected_title


# _parse_date


def test_parse_date():
    expected_date = '2024-12-31'
    now = date(2024, 12, 30)

    actual_date = _parse_date('31', 'Dec', now)

    assert actual_date == expected_date


def test_parse_date_rollover():
    expected_date = '2025-01-01'
    now = date(2024, 12, 30)

    actual_date = _parse_date('1', 'Jan', now)

    assert actual_date == expected_date
