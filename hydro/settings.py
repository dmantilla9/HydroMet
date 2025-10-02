from config import BASE, URL_GET, URL_POST

VERIFY_SSL = False

DEFAULT_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": BASE,
    "Referer": URL_GET,
    "User-Agent": "Mozilla/5.0",
}

# Minimal defaults for the OROBNAT search form
DEFAULT_SEARCH = {
    "idRegion": "11",
    "usd": "AEP",
    "posPLV": "0",
}
# print(BASE, URL_GET, URL_POST)