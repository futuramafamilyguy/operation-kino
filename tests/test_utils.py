from pathlib import Path


def load_html_fixture(filename):
    path = Path(__file__).parent / 'fixtures' / filename
    return path.read_text()
