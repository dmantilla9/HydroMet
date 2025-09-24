from typing import Dict, Any
from .settings import DEFAULT_SEARCH
#from db.supabase_utils import fetch_cities



def build_search_payload(city: Dict[str, Any]) -> Dict[str, str]:
    
    #city = fetch_cities()[0] if city is None else city
    """
    Build the POST payload that OROBNAT expects, using the DB 'city' row.
    Expected 'city' keys:
      - water_code: e.g. "095000386_095"
      - commune_code: e.g. "95176" == Cormeilles-en-Parisis
    """
    water_code = (city.get("water_code") or "").strip()
    departement = water_code[:3] if len(water_code) >= 3 else ""

    payload = {
        "methode": "rechercher",
        "idRegion": DEFAULT_SEARCH["idRegion"],
        "usd": DEFAULT_SEARCH["usd"],
        "posPLV": DEFAULT_SEARCH["posPLV"],
        "departement": departement,
        "communeDepartement": (city.get("commune_code") or "").strip(),
        "reseau": water_code,
    }
    return payload
# print(build_search_payload(None))  # for quick manual testing