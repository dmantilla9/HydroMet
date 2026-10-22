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
