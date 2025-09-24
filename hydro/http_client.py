"""
Very small HTTP client:
- creates a requests.Session
- supports an optional warm-up GET
- posts the search payload
"""

import requests
import urllib3
from typing import Tuple
from .settings import URL_GET, URL_POST, DEFAULT_HEADERS, VERIFY_SSL

# Silence "InsecureRequestWarning" if VERIFY_SSL=False during early tests.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def make_session() -> requests.Session:
    """
    Return a plain requests.Session with default headers.
    Keep it tiny and predictable; retries can be added later if needed.
    """
    s = requests.Session()
    s.headers.update(DEFAULT_HEADERS)
    return s


def warmup_get(session: requests.Session) -> None:
    """
    Optional warm-up GET. If it fails, we simply continue.
    Some sites set cookies or session state on the first GET.
    """
    try:
        session.get(
            URL_GET,
            params={"methode": "menu", "usd": "AEP", "idRegion": "11"},
            timeout=30,
            verify=VERIFY_SSL,
        )
    except Exception:
        pass


def post_search(session: requests.Session, payload: dict) -> Tuple[int, str]:
    """
    Perform the POST to OROBNAT and return (status_code, response_text).
    Raises HTTPError on non-2xx responses.
    """
    resp = session.post(URL_POST, data=payload, timeout=40, verify=VERIFY_SSL)
    resp.raise_for_status()
    return resp.status_code, resp.text
