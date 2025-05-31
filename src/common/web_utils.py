import requests

def fetch_html(url: str, headers: dict = None, timeout=10) -> str | None:
    try:
        response = requests.get(url, headers=headers or {}, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return None

def fetch_html_stateful(session: requests.Session, url: str, headers: dict = None, timeout=10) -> str | None:
    try:
        response = session.get(url, headers=headers or {}, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return None
