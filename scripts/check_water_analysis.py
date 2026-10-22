import logging

from db.supabase_utils import get_notification_history

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hydromet")


def main():
    logger.info("Starting water analysis notification check")

    history = get_notification_history()

    logger.info("History records found: %s", len(history))

    for record in history[:3]:
        logger.info(
            "Analysis: %s | Status: %s",
            record["analysis_id"],
            record["status"],
        )


if __name__ == "__main__":
    main()
