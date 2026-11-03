
import json
import logging
import os
from datetime import datetime
from html import escape
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from db.supabase_utils import (
    get_pending_water_analyses,
    get_telegram_topic,
    mark_analysis_as_sent,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("hydromet")

CHANNEL = "telegram"


def format_conformity(value):
    """Format official conformity values."""
    if value is None or str(value).strip() == "":
        return "Non renseigné"

    normalized = str(value).strip().lower()

    if normalized == "oui":
        return "✅ Conforme"

    if normalized == "non":
        return "⚠️ Non conforme / non respecté"

    return escape(str(value))


def build_message(payload):
    """Build a readable Telegram notification."""

    # Get the city name dynamically from the payload
    city_name = escape(
        str(payload.get("city_name") or "Ville inconnue")
    )

    city_collect = escape(
        str(payload.get("commune_prelevement") or "Non renseignée")
    )
    
    raw_date = payload.get("date_prelevement")
    date_label = "Non renseignée"

    if raw_date:
        date_label = datetime.fromisoformat(
            str(raw_date).replace("Z", "+00:00")
        ).strftime("%d/%m/%Y")

    conformity = payload.get("conformite") or {}
    results = payload.get("resultats") or []

    lines = [
        "💧 <b>HydroMet | Qualité de l'eau</b>",
        "",
        f"📍 <b>{city_name}</b>",
        f"📅 Prélèvement : {date_label}",
        f"🧪 Commune de prélèvement : {city_collect}",
        "",
        "<b>Conformité sanitaire</b>",
        "Bactériologique : "
        + format_conformity(conformity.get("bacteriologique")),
        "Physico-chimique : "
        + format_conformity(conformity.get("physico_chimique")),
        "Références de qualité : "
        + format_conformity(conformity.get("references_qualite")),
        "",
    ]

    conclusion = conformity.get("conclusions_sanitaires")

    if conclusion:
        lines.extend([
            "<b>Conclusion officielle</b>",
            escape(str(conclusion)),
            "",
        ])

    lines.append(
        f"🔬 <b>Paramètres analysés : {len(results)}</b>"
    )

    # Keep the Telegram message concise.
    highlighted = (
        "température",
        "ph ",
        "chlore libre",
        "turbidité",
        "escherichia coli",
        "nitrates",
    )

    for result in results:
        name = str(result.get("parametre") or "")
        value = str(result.get("valeur") or "")

        if any(term in name.lower() for term in highlighted):
            lines.append(
                f"• {escape(name)} : {escape(value)}"
            )

    lines.extend([
        "",
        f"🔎 Analyse : <code>{escape(str(payload['id']))}</code>",
    ])

    return "\n".join(lines)


def send_telegram_message(message, chat_id, message_thread_id):
    """Send a message to a specific Telegram topic."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urlencode({
        "chat_id": chat_id,
        "message_thread_id": message_thread_id,
        "text": message,
        "parse_mode": "HTML",
    }).encode("utf-8")

    request = Request(
        url,
        data=body,
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            result = json.load(response)
    except (HTTPError, URLError, TimeoutError) as exc:
        # Do not print the request URL: it contains the bot token.
        raise RuntimeError(
            "Telegram delivery failed"
        ) from None

    if result.get("ok") is not True:
        raise RuntimeError(
            "Telegram did not confirm delivery"
        )

    return result



def main():
    """Check and notify pending analyses by Telegram topic."""
    logger.info("Checking pending water analyses")

    analyses = get_pending_water_analyses(channel=CHANNEL)

    logger.info("Pending analyses: %s", len(analyses))

    if not analyses:
        logger.info("No new analyses. No notification sent.")
        return

    dry_run = os.getenv("HYDROMET_DRY_RUN", "false").lower() == "true"

    for analysis in analyses:
        analysis_id = analysis["analysis_id"]
        payload = analysis["notification_payload"]

        city_name = payload.get("city_name", "Unknown")
        code_insee = str(payload["commune"])

        logger.info(
            "Processing %s | %s | %s",
            analysis_id,
            city_name,
            code_insee,
        )

        # Get the destination for this commune.
        topic = get_telegram_topic(code_insee)

        if not topic:
            logger.warning(
                "No Telegram topic for %s (%s). Skipping.",
                city_name,
                code_insee,
            )
            continue

        chat_id = topic.get("chat_id")
        thread_id = topic.get("message_thread_id")

        if chat_id is None or thread_id is None:
            logger.warning(
                "Incomplete Telegram destination for %s",
                city_name,
            )
            continue

        message = build_message(payload)

        if dry_run:
            logger.info(
                "DRY RUN | City: %s | Chat: %s | Thread: %s",
                city_name,
                chat_id,
                thread_id,
            )
            logger.info("Message preview:\n%s", message)
            continue

        send_telegram_message(
            message,
            chat_id,
            thread_id,
        )

        logger.info("Telegram accepted: %s", analysis_id)

        mark_analysis_as_sent(analysis_id, CHANNEL)

        logger.info("Notification recorded: %s", analysis_id)


if __name__ == "__main__":
    main()

