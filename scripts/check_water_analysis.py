import json
import logging
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

LOGGER = logging.getLogger("hydromet")

BASE_DIR = Path(__file__).resolve().parent.parent
SQL_FILE = BASE_DIR / "sql" / "pending_analyses.sql"

COMMUNE = os.getenv("HYDROMET_COMMUNE", "95176")
CHANNEL = "telegram"


def get_pending_analyses():
    database_url = os.environ["DATABASE_URL"]
    query = SQL_FILE.read_text(encoding="utf-8")

    with psycopg.connect(
        database_url,
        connect_timeout=15,
        row_factory=dict_row
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (COMMUNE, CHANNEL))
            return cursor.fetchall()


def main():
    LOGGER.info("Checking water analyses for commune %s", COMMUNE)

    analyses = get_pending_analyses()

    if not analyses:
        LOGGER.info("No new analyses found.")
        return

    LOGGER.info("Found %s pending analyses", len(analyses))

    for analysis in analyses:
        LOGGER.info("New analysis: %s", analysis["id"])

        print(
            json.dumps(
                analysis["notification_payload"],
                indent=2,
                ensure_ascii=False,
                default=str
            )
        )


if __name__ == "__main__":
    main()
