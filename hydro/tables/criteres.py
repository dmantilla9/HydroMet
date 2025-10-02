from bs4 import BeautifulSoup
from typing import Dict
from ..parsing.sections import extract_communes_block_csv
from db.supabase_utils import upsert_criteres as sb_upsert_criteres  # usar utils

def build_criteres(html: str, payload: dict, id_page: str) -> Dict:
    """
    departement, commune (code INSEE), reseau -> del payload
    communes (CSV) -> del HTML (bloque 'Commune(s) et/ou quartier(s) du réseau')
    """
    communes_csv = extract_communes_block_csv(BeautifulSoup(html, "html.parser"))
    return {
        "id": id_page,
        "departement": (payload.get("departement") or "").strip(),
        "commune": (payload.get("communeDepartement") or "").strip(),  # code INSEE
        "reseau": (payload.get("reseau") or "").strip(),
        "communes": communes_csv or "",
    }

def upsert_criteres(row: Dict) -> None:
    sb_upsert_criteres(row)
