from bs4 import BeautifulSoup

from db.supabase_utils import upsert_conformite as sb_upsert_conformite  # usar utils

from ..parsing.mappers import clean_text
from ..parsing.sections import parse_section_kv


def build_conformite(html: str, id_page: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    conf = parse_section_kv(soup, "Conformité")

    def gc(key: str):
        for k, v in conf.items():
            if key.lower() in k.lower():
                return v
        return None

    return {
        "id": id_page,
        "conclusions_sanitaires": clean_text(
            gc("conclusions sanitaires")
            or gc("conclusions_sanitaires")
            or gc("Conclusions sanitaires")
        ),
        "conformite_bacteriologique": gc("bactériolog"),
        "conformite_physico_chimique": gc("physico"),
        "respect_references_qualite": gc("références") or gc("references"),
    }


def upsert_conformite(row: dict) -> None:
    sb_upsert_conformite(row)
