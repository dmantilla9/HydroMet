# hydro/cli.py
# Command Line Interface for HydroMet ETL (English version)

import argparse
import sys
import time
import logging

from db.supabase_utils import fetch_cities
from .etl_runner import process_city, process_html_debug

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("hydromet")


def main():
    parser = argparse.ArgumentParser(description="HydroMet ETL runner")
    parser.add_argument("--html", type=str, default="", help="Path to a local HTML file (offline mode)")
    parser.add_argument("--reseau", type=str, default="", help="Reseau code (optional)")
    parser.add_argument("--departement", type=str, default="", help="Departement code (optional)")
    parser.add_argument("--commune", type=str, default="", help="Commune INSEE code (optional)")

    # If provided, process a single city; if omitted, process ALL active cities.
    parser.add_argument("--city-index", type=int, default=None, help="City index (optional)")

    # Batch controls
    parser.add_argument("--limit", type=int, default=0, help="Process only the first N active cities (0 = all)")
    parser.add_argument("--sleep", type=float, default=0.8, help="Seconds to sleep between cities (anti rate-limit)")

    args = parser.parse_args()

    try:
        # ---------- Offline mode (local HTML) ----------
        if args.html:
            with open(args.html, "r", encoding="utf-8") as f:
                html = f.read()
            page_id = process_html_debug(
                html,
                city_stub={
                    "reseau": args.reseau,
                    "departement": args.departement,
                    "communeDepartement": args.commune,
                },
            )
            print(f"[OK] Insert/Update from local HTML. id={page_id}")
            return

        # ---------- Online mode ----------
        cities = fetch_cities()
        if not cities:
            log.error("No active cities found in DB.")
            sys.exit(2)

        # Single-city mode when index is provided
        if args.city_index is not None:
            idx = max(0, min(args.city_index, len(cities) - 1))
            city = cities[idx]
            name = city.get("city_name") or city.get("commune_code") or f"idx-{idx}"
            log.info(f"Processing 1 city: {name}")
            page_id = process_city(city)
            print(f"[OK] Insert/Update from OROBNAT. id={page_id} (city_index={idx})")
            return

        # Batch mode: process ALL active cities (with optional limit)
        total = len(cities) if args.limit in (None, 0) else min(args.limit, len(cities))
        ok, fail = 0, 0
        failed = []

        log.info(f"Processing {total} active city(ies)...")
        for i, city in enumerate(cities[:total], start=1):
            name = city.get("city_name") or city.get("commune_code") or f"idx-{i-1}"
            try:
                pid = process_city(city)
                log.info(f"[{i}/{total}] OK {name} -> id={pid}")
                ok += 1
            except Exception as e:
                log.error(f"[{i}/{total}] FAIL {name}: {e}")
                fail += 1
                failed.append((name, str(e)))
            # Anti rate-limit pause
            if args.sleep > 0 and i < total:
                time.sleep(args.sleep)

        print("\n===== Summary =====")
        print(f"Total: {total} | OK: {ok} | FAIL: {fail}")
        if failed:
            print("Failures:")
            for name, err in failed[:10]:
                print(f" - {name}: {err}")
            if len(failed) > 10:
                print(f" ... and {len(failed)-10} more")

    except Exception as e:
        print(f"[FATAL] ETL runtime error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()