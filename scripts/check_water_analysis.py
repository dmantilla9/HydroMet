
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


def send_telegram_message(message):
    """Send message and verify Telegram API response."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    body = urlencode({
        "chat_id": chat_id,
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
    logger.info("Checking pending water analyses")

    analyses = get_pending_water_analyses(
    channel=CHANNEL,
    )

    logger.info("Pending analyses: %s", len(analyses))

    if not analyses:
        logger.info("No new analyses. No notification sent.")
        return

    # Send older pending analyses first.
    for analysis in analyses:
        analysis_id = analysis["analysis_id"]
        payload = analysis["notification_payload"]

        logger.info("Processing analysis: %s", analysis_id)

        message = build_message(payload)

        if os.getenv("HYDROMET_DRY_RUN", "false").lower() == "true":
            logger.info(
                "DRY RUN | Analysis: %s | City: %s",
                analysis_id,
                payload.get("city_name"),
            )
            logger.info("Message preview:\n%s", message)
            continue

        send_telegram_message(message)

        logger.info("Telegram accepted: %s", analysis_id)

        mark_analysis_as_sent(analysis_id, CHANNEL)

        logger.info("Notification recorded: %s", analysis_id)


if __name__ == "__main__":
    main()
