from typing import List, Dict
from bs4 import BeautifulSoup
from ..parsing.sections import parse_results_rows
from db.supabase_utils import upsert_resultats as sb_upsert_resultats  # usar utils

def build_resultats(html: str, id_page: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = parse_results_rows(soup)
    out: List[Dict] = []
    for r in rows:
        out.append({
            "id": id_page,
            "parametre": r.get("parametre") or r.get("Paramètre") or r.get("Parametre") or "",
            "valeur": r.get("valeur") or r.get("Valeur") or "",
            "limite_qualite": r.get("limite_qualite") or r.get("Limite de qualité") or "",
            "reference_qualite": r.get("reference_qualite") or r.get("Référence de qualité") or r.get("Reference de qualite") or "",
        })
    return out

def upsert_resultats(rows: List[Dict]) -> None:
    if rows:
        sb_upsert_resultats(rows)
