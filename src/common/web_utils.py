import requests

def fetch_html(url: str, headers=None, timeout=10) -> str | None:
    try:
        response = requests.get(url, headers=headers or {}, timeout=timeout)
        response.raise_for_status
        return response.text
    except requests.RequestException as e:
        return None
