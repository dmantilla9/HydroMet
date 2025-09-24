# -*- coding: utf-8 -*-
"""
End-to-end:
- fetch city
- build payload
- POST (http_client)
- parse HTML → DataFrames (parser)
- map DataFrames → analysis record (mapper)
- insert into DB
"""

from db.supabase_utils import fetch_cities, insert_analysis
from .payloads import build_search_payload
from .http_client import make_session, warmup_get, post_search
from .parser import parse_search_page
from .mapper import build_analysis_record


def main():
    cities = fetch_cities()
    if not cities:
        print("No active cities.")
        return

    city = cities[0]  # process first city for now
    print("Selected city:", city.get("city_name"))

    # Build payload and request HTML
    payload = build_search_payload(city)
    session = make_session()
    warmup_get(session)
    status, html = post_search(session, payload)
    print("POST status:", status)

    # Parse HTML to DataFrames
    parsed = parse_search_page(html, payload)

    # Map DataFrames to a single DB row (public.analysis)
    record = build_analysis_record(
        meta_df=parsed["meta_df"],
        info_df=parsed["info_df"],
        conf_df=parsed["conf_df"],
        res_df=parsed["res_df"],
        payload=payload,
    )

    # Debug: show a few mapped fields
    preview_keys = ["departement", "commune", "reseau", "date_prelevement",
                    "commune_prelevement", "conclusion_sanitaire",
                    "conformite_bacteriologique", "conformite_physico_chimique",
                    "ph", "conductivite_25c", "enterocoques_100ml_ms", "enterocoques_100ml_ms_value"]
    print("Record preview:", {k: record.get(k) for k in preview_keys})

    # Insert into DB
    ok = insert_analysis(record)
    print("Insert OK:", ok)


if __name__ == "__main__":
    main()
