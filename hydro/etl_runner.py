# hydro/etl_runner.py
from bs4 import BeautifulSoup
from typing import Dict
from .http_client import make_session, warmup_get, post_search
from .payloads import build_search_payload
from .parsing.mappers import parse_datetime_any, build_id_from_date_and_insee
from .parsing.sections import parse_section_kv
from .tables.criteres import build_criteres, upsert_criteres
from .tables.informations import build_informations, upsert_informations
from .tables.conformite import build_conformite, upsert_conformite
from .tables.resultats import build_resultats, upsert_resultats

def _extract_prelevement_datetime(html: str):
    soup = BeautifulSoup(html, "html.parser")
    info = parse_section_kv(soup, "Informations générales")
    for k, v in info.items():
        if "prélèvement" in k.lower():
            return parse_datetime_any(v)
    return None

def _compute_page_id(html: str, payload: dict) -> str:
    dt = _extract_prelevement_datetime(html)
    code_insee = payload.get("communeDepartement")  # <- INSEE desde el payload
    return build_id_from_date_and_insee(dt, code_insee)

def process_city(city: dict) -> str:
    session = make_session()
    warmup_get(session)
    payload = build_search_payload(city)
    status, html = post_search(session, payload)
    if not (200 <= status < 300):
        raise RuntimeError(f"POST failed: {status}")

    page_id = _compute_page_id(html, payload)

    row_criteres = build_criteres(html, payload, page_id)
    row_info = build_informations(html, page_id)
    row_conf = build_conformite(html, page_id)
    rows_res = build_resultats(html, page_id)

    upsert_criteres(row_criteres)
    upsert_informations(row_info)
    upsert_conformite(row_conf)
    upsert_resultats(rows_res)

    return page_id

def process_html_debug(html: str, city_stub: dict | None = None) -> str:
    payload = {
        "reseau": (city_stub or {}).get("reseau", ""),
        "departement": (city_stub or {}).get("departement", ""),
        "communeDepartement": (city_stub or {}).get("communeDepartement", ""),
    }
    page_id = _compute_page_id(html, payload)

    row_criteres = build_criteres(html, payload, page_id)
    row_info = build_informations(html, page_id)
    row_conf = build_conformite(html, page_id)
    rows_res = build_resultats(html, page_id)

    upsert_criteres(row_criteres)
    upsert_informations(row_info)
    upsert_conformite(row_conf)
    upsert_resultats(rows_res)
    return page_id
