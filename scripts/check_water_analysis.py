
import json
import logging

from db.supabase_utils import get_pending_water_analyses

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("hydromet")


def main():
    logger.info("Starting HydroMet water analysis check")

    analyses = get_pending_water_analyses(
        commune="95176",
        channel="telegram",
    )

    logger.info("Pending analyses found: %s", len(analyses))

    if not analyses:
        logger.info("No new water analyses available")
        return

    for analysis in analyses:
        payload = analysis["notification_payload"]

        logger.info(
            "New analysis detected: %s",
            analysis["analysis_id"],
        )

        logger.info(
            "Analysis date: %s",
            analysis["date_prelevement"],
        )

        logger.info(
            "Parameters found: %s",
            len(payload.get("resultats", [])),
        )

        print(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
import logging

from db.supabase_utils import supabase, TBL_NOTIFICATIONS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("hydromet")


def main():
    logger.info("Starting HydroMet notification check")

    logger.info("Connecting to Supabase...")

    response = (
        supabase
        .table(TBL_NOTIFICATIONS)
        .select("analysis_id, status")
        .eq("notification_channel", "telegram")
        .limit(3)
        .execute()
    )

    logger.info("Supabase query completed")

    records = response.data or []

    logger.info("Records returned: %s", len(records))

    for record in records:
        logger.info("Record: %s", record)


if __name__ == "__main__":
    main()
