# hydro/parsing/mappers.py
import html
import re
import unicodedata
from datetime import datetime

NBSP = "\u00a0"  # non-breaking space
ZWSP = "\u200b"  # zero-width space


def clean_text(s: str | None) -> str | None:
    if s is None:
        return None
    t = html.unescape(s)
    t = t.replace(NBSP, " ").replace(ZWSP, "")
    t = re.sub(r"\s+", " ", t)
    t = unicodedata.normalize("NFC", t)
    return t.strip()


def parse_datetime_any(txt: str | None) -> datetime | None:
    if not txt:
        return None
    s = re.sub(r"(\d{1,2})h(\d{2})", r"\1:\2", str(txt).strip(), flags=re.IGNORECASE)
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


def normalize_headers(headers: list[str]) -> list[str]:
    out = []
    for h in headers:
        h0 = h.strip().lower()
        h0 = h0.replace("paramètre", "parametre")
        h0 = h0.replace("limite de qualité", "limite_qualite")
        h0 = h0.replace("référence de qualité", "reference_qualite").replace(
            "référence", "reference"
        )
        out.append(h0)
    return out


def communes_text_to_csv(span_html_text: str) -> str:
    items = []
    for line in span_html_text.splitlines():
        line = re.sub(r"^\s*-\s*", "", line).strip()
        if line:
            items.append(line)
    return ", ".join(items)


def build_id_from_date_and_insee(dt: datetime | None, code_insee: str | None) -> str:
    """
    ID = 'dd-mm-aaaa' + '-' + code_insee (communeDepartement).
    Si falta fecha, usa hoy; si falta INSEE, usa '00000'.
    """
    from datetime import datetime as _dt

    d = dt or _dt.now()
    insee = (code_insee or "00000").strip() or "00000"
    return f"{d.strftime('%d-%m-%Y')}-{insee}"
