from typing import Dict
from bs4 import BeautifulSoup
from ..parsing.sections import parse_section_kv
from db.supabase_utils import upsert_conformite as sb_upsert_conformite  # usar utils

def build_conformite(html: str, id_page: str) -> Dict:
    soup = BeautifulSoup(html, "html.parser")
    conf = parse_section_kv(soup, "Conformité")

    def gc(key: str):
        for k, v in conf.items():
            if key.lower() in k.lower():
                return v
        return None

    return {
        "id": id_page,
        "conclusions_sanitaires": gc("conclusions sanitaires") or gc("conclusions_sanitaires") or gc("Conclusions sanitaires"),
        "conformite_bacteriologique": gc("bactériolog"),
        "conformite_physico_chimique": gc("physico"),
        "respect_references_qualite": gc("références") or gc("references"),
    }

def upsert_conformite(row: Dict) -> None:
    sb_upsert_conformite(row)
