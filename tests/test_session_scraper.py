from src.session_scraper.scraper import _clean_movie_title, _parse_movie_details, _parse_now_showing_movies
from tests.test_utils import load_html_fixture


# _parse_now_showing_movies

def test_parse_now_showing_movies():
    expected_movies = [
        {
            'title': 'Mr. Baseball',
            'slug': 'mr-baseball'
        },
        {
            'title': 'Cannery Row',
            'slug': 'cannery-row'
        }
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
        'image_url': 'img-store.com/cannery-row.jpg'
    }
    html = load_html_fixture('movie_details.html')

    actual_details = _parse_movie_details(html)

    assert actual_details == expected_details


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
