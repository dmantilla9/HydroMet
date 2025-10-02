from typing import Dict
from bs4 import BeautifulSoup
from ..parsing.sections import parse_section_kv
from ..parsing.mappers import parse_datetime_any
from db.supabase_utils import upsert_informations as sb_upsert_informations  # usar utils

def build_informations(html: str, id_page: str) -> Dict:
    soup = BeautifulSoup(html, "html.parser")
    info = parse_section_kv(soup, "Informations générales")

    def gi(key: str):
        for k, v in info.items():
            if key.lower() in k.lower():
                return v
        return None

    dt = parse_datetime_any(gi("prélèvement"))
    return {
        "id": id_page,
        "date_prelevement": dt.isoformat() if dt else None,
        "commune_prelevement": gi("commune"),
        "installation": gi("installation"),
        "service_distribution": gi("service"),
        "responsable_distribution": gi("responsable"),
        "maitre_ouvrage": gi("maître") or gi("maitre"),
    }

def upsert_informations(row: Dict) -> None:
    sb_upsert_informations(row)
